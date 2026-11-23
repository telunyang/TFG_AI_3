'''
Import the libraries needed for this section.
匯入本段程式所需的函式庫。
'''
import uuid
import time
from pathlib import Path
import requests
from contextlib import ExitStack
API_URL = 'https://REPLACE_WITH_YOUR_NGROK_DOMAIN'
EXPECTED_SERVICE = '06_Qwen_Image_2.1_圖片生成_Kaggle'

'''
Choose: text (0 images), edit (1 image), or multi (2–10 images).
選擇 text（0 張）、edit（1 張）或 multi（2～10 張參考圖）。
'''
TASK = 'text'
PROMPT = '''
A cozy bookstore in Taipei on a rainy evening, realistic photography.
'''.strip()

'''
Define an optional negative prompt.
設定選用的負面提示詞。
'''
NEGATIVE_PROMPT = '''

'''.strip()
WIDTH, HEIGHT = 640, 640

'''
Configure Qwen sampling; turbo is valid only with 6 steps and CFG=1.
設定 Qwen 取樣參數；turbo 僅適用 6 steps、CFG=1。
'''
STEPS, CFG, SAMPLER = 6, 1.0, 'auto'
REFERENCE_SIZE, SEED = 512, 42

'''
Set local images in upload order; keep [] for text generation.
依順序填入本機參考圖片；文生圖保持 []。
'''
IMAGE_PATHS = []
PARAMS = dict(task=TASK, prompt=PROMPT, negative_prompt=NEGATIVE_PROMPT,
              width=WIDTH, height=HEIGHT, steps=STEPS, cfg=CFG,
              sampler=SAMPLER, reference_size=REFERENCE_SIZE, seed=SEED)

DOWNLOAD_DIR = Path('generated_results')

'''
Query the remote job once every five seconds.
每五秒查詢一次工作狀態。
'''
POLL_SECONDS = 5
HEADERS = {'ngrok-skip-browser-warning': 'true'}
IMAGE_COUNTS = {'text': (0, 0), 'edit': (1, 1), 'multi': (2, 10)}

'''
Reuse a stable job ID for transient failures; give busy queues time to drain.
暫時性失敗沿用同一筆工作 ID，讓滿載佇列有時間消化。
'''

'''
Reattempt interrupted downloads at most three times.
下載暫時中斷時，最多重試三次。
'''
MAX_DOWNLOAD_RETRIES = 3

'''
Submit exactly one logical job; retries reuse its ID and cannot duplicate inference.
每次只提交一筆邏輯工作；重試使用相同 ID，避免重複推論。
'''
'''
Measure each client stage without changing its return value or exception behavior.
統計 Client 各階段耗時，不改變函式回傳值或原本的例外處理。
'''
def measure_time(label, function, *args, **kwargs):
    started = time.perf_counter()
    try:
        return function(*args, **kwargs)
    finally:
        minutes, seconds = divmod(time.perf_counter() - started, 60)
        elapsed = f'{int(minutes)} 分 {seconds:05.2f} 秒' if minutes else f'{seconds:.2f} 秒'
        print(f'⏱ {label}耗時：{elapsed}')

def submit_job(session, params=PARAMS, images=IMAGE_PATHS, api_url=API_URL):
    '''
    Validate this notebook's image requirements before opening files.
    先檢查此 Notebook 的圖片張數，再開啟檔案。
    '''
    expected = IMAGE_COUNTS.get(params['task'])
    if expected is None or not expected[0] <= len(images) <= expected[1]:
        raise ValueError(f'模式 {params["task"]} 的參考圖數量不正確；允許範圍：{IMAGE_COUNTS}')
    request_id = uuid.uuid4().hex
    network_failures = 0
    headers = dict(HEADERS, **{'X-Request-ID': request_id})
    while True:
        response = None
        try:
            with ExitStack() as stack:
                files = []
                for filename in images:
                    path = Path(filename)
                    stream = stack.enter_context(path.open('rb'))
                    files.append(('images', (path.name, stream)))
                url = api_url.rstrip('/') + '/generate'
                if files:
                    response = session.post(url, data=params, files=files, headers=headers, timeout=(30, 180))
                else:
                    response = session.post(url, json=params, headers=headers, timeout=(30, 180))
            if response.status_code not in (429, 502, 503, 504):
                if not response.ok:
                    raise RuntimeError(f'提交失敗 HTTP {response.status_code}: {response.text[:800]}')
                return response.json()['job_id']
            network_failures = 0
            reason = f'HTTP {response.status_code}: {response.text[:200]}'
        except (requests.Timeout, requests.ConnectionError) as error:
            network_failures += 1
            if network_failures >= 12:
                raise ConnectionError(f'連續 12 次連線失敗；請檢查 API_URL、ngrok 連線與工作 {request_id}。') from error
            reason = str(error)[:200]
        retry_after = response.headers.get('Retry-After', '10') if response is not None else '10'
        try:
            delay = min(30, max(2, float(retry_after)))
        except ValueError:
            delay = 10
        print(f'提交暫未成功（{reason}），{delay:.0f} 秒後重試…')
        time.sleep(delay)

'''
Query the existing job instead of submitting another generation.
查詢既有工作的狀態，不另行提交生成工作。
'''
def get_job(session, job_id, api_url=API_URL):
    response = session.get(f'{api_url.rstrip("/")}/jobs/{job_id}',
                           headers=HEADERS, timeout=(20, 30))
    response.raise_for_status()
    return response.json()

'''
Poll patiently through temporary disconnections and long GPU queues.
等待長時間 GPU 排隊，並容忍短暫斷線。
'''
def wait_for_job(session, job_id, api_url=API_URL):
    previous = None
    last_notice = time.monotonic()
    while True:
        try:
            job = get_job(session, job_id, api_url)
        except (requests.ConnectionError, requests.Timeout):
            print('連線暫時中斷，保留原工作編號並稍後查詢…')
            time.sleep(POLL_SECONDS)
            continue
        status = (job['status'], job.get('queue_position'))
        if status != previous:
            print('生成狀態：', *[value for value in status if value is not None])
            previous = status
            last_notice = time.monotonic()
        if time.monotonic() - last_notice >= 300:
            print(f'工作 {job_id} 仍在 {job["status"]} 狀態。')
            last_notice = time.monotonic()
        if job['status'] == 'done':
            return job
        if job['status'] not in ('queued', 'running'):
            raise RuntimeError(job.get('error', f'未知狀態：{job["status"]}'))
        time.sleep(POLL_SECONDS)

'''
Stream files with atomic local replacement; retry temporary download failures.
串流下載並以原子操作完成存檔，遇到暫時性中斷時可重試。
'''
def download_file(session, job_id, endpoint, filename, api_url=API_URL):
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = DOWNLOAD_DIR / f'{job_id}_{Path(filename).name}'
    temp = path.with_name(path.name + '.part')
    for attempt in range(MAX_DOWNLOAD_RETRIES):
        try:
            with session.get(f'{api_url.rstrip("/")}/jobs/{job_id}/{endpoint}',
                             headers=HEADERS, stream=True, timeout=(30, 300)) as response:
                if response.status_code not in (429, 502, 503, 504):
                    response.raise_for_status()
                elif attempt == MAX_DOWNLOAD_RETRIES - 1:
                    response.raise_for_status()
                else:
                    raise requests.ConnectionError(f'暫時無法下載：HTTP {response.status_code}')
                with temp.open('wb') as output:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            output.write(chunk)
            temp.replace(path)
            return path
        except (requests.ConnectionError, requests.Timeout, OSError):
            temp.unlink(missing_ok=True)
            if attempt == MAX_DOWNLOAD_RETRIES - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError('結果下載未完成')

'''
Check CUDA readiness before submitting the model-specific generation request.
提交此模型專屬的生成請求前，先確認遠端 NVIDIA CUDA 後端已就緒。
'''
def check_gpu_backend(session):
    response = session.get(API_URL.rstrip('/') + '/health?task=' + str(PARAMS['task']), headers=HEADERS, timeout=(10, 20))
    response.raise_for_status()
    status = response.json()
    if status.get('service_id') != EXPECTED_SERVICE:
        raise RuntimeError('API_URL 指向錯誤的模型服務：' + str(status.get('service_id', '未知服務')))
    if status.get('task') != PARAMS['task']:
        raise RuntimeError('遠端服務未正確辨識生成模式：' + str(PARAMS['task']))
    if status.get('gpu_ready') is not True:
        raise RuntimeError('遠端 GPU 尚未就緒：' + status.get('gpu_message', '請更新並重新執行 Notebook 的 API Cell。'))
    if status.get('backend_ready') is not True:
        raise RuntimeError('遠端模型或模式尚未就緒：' + status.get('gpu_message', '請先執行對應的 Notebook 設定 Cells。'))
    print('已偵測 CUDA：', '、'.join(status.get('gpu_devices', [])))

def main():
    '''
    Show a direct setup error instead of retrying an unconfigured address.
    尚未填寫服務設定時直接提示，避免持續重試錯誤網址。
    '''
    if 'REPLACE_WITH_' in API_URL:
        raise ValueError('請先填入 Notebook 顯示的 ngrok API_URL。')
    with requests.Session() as session:
        measure_time('GPU／服務檢查', check_gpu_backend, session)
        job_id = measure_time('提交生成工作', submit_job, session, PARAMS, IMAGE_PATHS)

        print('工作編號：', job_id)
        job = measure_time('佇列等待與生成', wait_for_job, session, job_id)
        result = measure_time('下載成果', download_file, session, job_id, 'file', job['filename'])
        print('生成結果：', result)

if __name__ == '__main__':
    measure_time('整體程式', main)
