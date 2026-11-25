'''
Import the libraries needed for this section.
匯入本段程式所需的函式庫。
'''
import re
import uuid
import time
from pathlib import Path
import requests
from contextlib import ExitStack
API_URL = 'https://REPLACE_WITH_YOUR_NGROK_DOMAIN'
EXPECTED_SERVICE = '06_MiniMax_H3_影片生成_Kaggle'

'''
Select t2v, i2v, l2v, flf2v, or r2v; reference media depend on the task.
選擇 t2v、i2v、l2v、flf2v 或 r2v；R2V 可使用圖片、影片及音訊參考。
'''
TASK = 't2v'
PROMPT = '''
A peaceful Taipei park with gentle wind and natural sounds.
'''.strip()

'''
Set the video dimensions and duration.
設定影片尺寸與長度。
'''
WIDTH, HEIGHT, SECONDS = 384, 224, 10
STEPS = 20

'''
Match the task-specific Audio Shift in the Notebook, including R2V.
讓 Audio Shift 與 Notebook 各生成模式一致，包括 R2V。
'''
AUDIO_SHIFT = 3.0 if TASK == 'r2v' else 6.0
'''
Keep H3 at its model-supported 24 FPS rather than allowing arbitrary frame rates.
將 H3 維持在模型支援的 24 FPS，不允許任意指定影格率。
'''
FPS = 24
REF_IMAGE_SIZE = 'match'

'''
Fix the seed or use -1 for random.
固定種子，或用 -1 代表隨機。
'''
SEED = 42
IMAGE_PATHS = []

'''
Optional reference videos for R2V, in prompt order (up to three).
R2V 可選的參考影片路徑，依 Prompt 編號排序（最多三段）。
'''
VIDEO_PATHS = []
AUDIO_PATHS = []
VIDEO_AUDIO = False  # True, False

'''
Use the Notebook's quantization, or choose a loaded alternative.
留空沿用 Notebook 量化，或指定已經載入的量化格式。
'''
QUANT = ''
PARAMS = dict(task=TASK, prompt=PROMPT, width=WIDTH, height=HEIGHT,
              seconds=SECONDS, fps=FPS, steps=STEPS, audio_shift=AUDIO_SHIFT,
              ref_image_size=REF_IMAGE_SIZE, seed=SEED)

if QUANT:
    PARAMS['quant'] = QUANT

PARAMS['video_audio'] = str(VIDEO_AUDIO).lower()

'''
Keep downloaded files in a separate local directory.
將下載結果存至獨立資料夾。
'''
DOWNLOAD_DIR = Path('generated_results')
POLL_SECONDS = 5
HEADERS = {'ngrok-skip-browser-warning': 'true'}

'''
Validate the reference-image count for this specific Notebook.
依此 Notebook 支援的模式確認參考圖數量。
'''
IMAGE_COUNTS = {'t2v': (0, 0), 'i2v': (1, 1), 'l2v': (1, 1), 'flf2v': (2, 2), 'r2v': (0, 9)}

'''
Retry temporary download failures without limiting generation time.
下載失敗時有限次重試；生成工作本身沒有總時間限制。
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
    if expected is None or not expected[0] <= len(images) <= expected[1] or (params['task'] == 'r2v' and not (images or VIDEO_PATHS)):
        raise ValueError('圖片張數不符；R2V 需要至少一張圖片或一段影片，音訊只能作為附加參考。')
    if VIDEO_PATHS or AUDIO_PATHS:
        if params['task'] != 'r2v' or len(VIDEO_PATHS) > 3 or len(AUDIO_PATHS) > 3:
            raise ValueError('參考影片／音訊僅支援 R2V，且各最多 3 段。')
    if params['task'] == 'r2v' and len(images) + len(VIDEO_PATHS) + len(AUDIO_PATHS) > 12:
        raise ValueError('R2V 最多接受 12 個參考素材檔案。')
    if params['task'] == 'r2v':
        numbers = {int(n) for n in re.findall(r'<Picture\s+(\d+)>', params.get('prompt', ''), re.I)}
        if any(n < 1 or n > len(images) for n in numbers):
            raise ValueError('MiniMax R2V Prompt 指向不存在的 <Picture N> 圖片。')
        for label, count in (('Video', len(VIDEO_PATHS)),
                             ('Audio', len(AUDIO_PATHS) + (len(VIDEO_PATHS) if VIDEO_AUDIO else 0))):
            numbers = [int(n) for n in re.findall(r'<%s\s+(\d+)>' % label, params.get('prompt', ''), re.I)]
            if any(n < 1 or n > count for n in numbers):
                raise ValueError(f'R2V Prompt 使用了不存在的 <{label} N> 參考素材。')
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
                for field, paths in (('videos', VIDEO_PATHS), ('audios', AUDIO_PATHS)):
                    for filename in paths:
                        path = Path(filename)
                        stream = stack.enter_context(path.open('rb'))
                        files.append((field, (path.name, stream)))
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

        '''
        Submit exactly one generation job to the FIFO queue.
        向 FIFO 佇列提交一筆生成工作。
        '''
        job_id = measure_time('提交生成工作', submit_job, session, PARAMS, IMAGE_PATHS)
        print('工作編號：', job_id)
        job = measure_time('佇列等待與生成', wait_for_job, session, job_id)
        result = measure_time('下載成果', download_file, session, job_id, 'file', job['filename'])
        print('生成結果：', result)

        '''
        Save the last video frame for continuing I2V/FLF2V generation.
        額外儲存影片最後影格，供接續 I2V／FLF2V 使用。
        '''
        if job.get('last_frame_available'):
            frame = measure_time('下載成果', download_file, session, job_id, 'last-frame', 'last_frame.png')

            print('最後影格：', frame)

if __name__ == '__main__':
    measure_time('整體程式', main)
