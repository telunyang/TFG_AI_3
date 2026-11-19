'''
Import the libraries needed for this section.
匯入本段程式所需的函式庫。
'''
import uuid
import time
from pathlib import Path
import requests

'''
Set the URL displayed in the Notebook ngrok cell.
填入 Notebook 的 ngrok 公開網址。
'''
API_URL = 'https://REPLACE_WITH_YOUR_NGROK_DOMAIN'

'''
Verify the remote Notebook serves this specific model.
確認遠端 Notebook 啟動的是這份 client 對應的模型。
'''
EXPECTED_SERVICE = '06_Z-Image-Turbo_圖片生成_Kaggle'

'''
Write the requested image description.
編輯要生成的圖片描述。
'''
PROMPT = '''
A cozy Taiwanese street at dusk, photorealistic.
'''.strip()

'''
Set dimensions to multiples of 64 pixels.
將圖片長寬設定為 64 的倍數。
'''
WIDTH, HEIGHT = 640, 960

'''
Choose sampling steps and classifier-free guidance.
設定取樣步數與 CFG 引導值。
'''
STEPS, CFG = 8, 1.0

'''
Use -1 for a new random seed on every generation.
使用 -1 讓每次生成採用不同的隨機種子。
'''
SEED = 42

'''
Match the exact fields supported by this text-to-image Notebook.
僅使用這份文生圖 Notebook 支援的欄位。
'''
PARAMS = dict(task='text', prompt=PROMPT, width=WIDTH, height=HEIGHT,
              steps=STEPS, cfg=CFG, seed=SEED)

'''
Keep downloaded files in a separate local directory.
將下載結果存至獨立資料夾。
'''
DOWNLOAD_DIR = Path('generated_results')

'''
Query the remote job once every five seconds.
每五秒查詢一次工作狀態。
'''
POLL_SECONDS = 5

'''
Skip the ngrok browser warning for API requests and downloads.
避免 ngrok 的瀏覽器提醒干擾 API 提交、查詢及下載。
'''
HEADERS = {'ngrok-skip-browser-warning': 'true'}

'''
Reuse a stable job ID for transient failures; give busy queues time to drain.
暫時性失敗沿用同一筆工作 ID，讓滿載佇列有時間消化。
'''
MAX_SUBMIT_WAIT = 2 * 3600

'''
Keep checking long video jobs without waiting forever.
長影片排隊可持續等待，但不會永久卡住。
'''
MAX_RESULT_WAIT = 24 * 3600

'''
Accept a short ngrok outage without losing the original job.
容許 ngrok 短暫斷線，保留原工作編號。
'''
MAX_OFFLINE_WAIT = 10 * 60

'''
Reattempt interrupted downloads at most three times.
下載暫時中斷時，最多重試三次。
'''
MAX_DOWNLOAD_RETRIES = 3

'''
Submit a text-only request, preserving its identity across network retries.
提交純文字請求，網路重試期間沿用相同工作 ID。
'''
def submit_job(session, params=PARAMS, api_url=API_URL):

    '''
    Keep the same ID even if ngrok drops the response after accepting the task.
    即使 ngrok 中斷已接受請求的回應，也不會重複生成。
    '''
    request_id = uuid.uuid4().hex
    deadline = time.monotonic() + MAX_SUBMIT_WAIT

    '''
    Bound repeated transport failures separately from ordinary queue overload.
    網路持續失敗時提早回報，不讓學生一直等到佇列等待期限。
    '''
    network_failures = 0
    headers = dict(HEADERS, **{'X-Request-ID': request_id})
    while True:
        response = None
        try:
            response = session.post(api_url.rstrip('/') + '/generate', json=params,
                                    headers=headers, timeout=(30, 180))
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

        '''
        Back off when overloaded, but stop after the configured maximum wait.
        服務忙碌時延後重試，超過期限就明確回報。
        '''
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f'提交超過 {MAX_SUBMIT_WAIT} 秒。Request ID: {request_id}；最後錯誤：{reason}')
        retry_after = response.headers.get('Retry-After', '10') if response is not None else '10'
        try:
            delay = min(30, max(2, float(retry_after)), remaining)
        except ValueError:
            delay = min(10, remaining)
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
    deadline = time.monotonic() + MAX_RESULT_WAIT
    offline_since = None
    previous = None
    last_notice = time.monotonic()
    while time.monotonic() < deadline:
        try:
            job = get_job(session, job_id, api_url)
            offline_since = None
        except (requests.ConnectionError, requests.Timeout) as error:
            if offline_since is None:
                offline_since = time.monotonic()
            if time.monotonic() - offline_since > MAX_OFFLINE_WAIT:
                raise ConnectionError(f'持續無法連線至 API；工作編號 {job_id} 可能仍在遠端執行。') from error
            print('連線暫時中斷，保留原工作編號並稍後查詢…')
            time.sleep(POLL_SECONDS)
            continue
        status = (job['status'], job.get('queue_position'))
        if status != previous:
            print('生成狀態：', *[value for value in status if value is not None])
            previous = status
            last_notice = time.monotonic()

        '''
        A quiet long-running inference is not evidence that it has completed.
        長時間沒有狀態變化不代表推論完成。
        '''
        if time.monotonic() - last_notice >= 300:
            print(f'工作 {job_id} 仍在 {job["status"]} 狀態。')
            last_notice = time.monotonic()
        if job['status'] == 'done':
            return job
        if job['status'] not in ('queued', 'running'):
            raise RuntimeError(job.get('error', f'未知狀態：{job["status"]}'))
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f'等待已超過 {MAX_RESULT_WAIT} 秒。工作 {job_id} 可能仍在執行，請稍後以該編號查詢。')

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

                '''
                Expired outputs and invalid jobs need manual intervention.
                結果過期或工作不存在時直接回報，不能盲目重試。
                '''
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
Run a single generation request and download only that job's results.
提交一筆生成請求，並只下載該工作的結果。
'''
'''
Check CUDA readiness before submitting the model-specific generation request.
提交此模型專屬的生成請求前，先確認 Kaggle 的 CUDA 後端已就緒。
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

    '''
    Share one connection pool during submission and polling.
    提交與查詢期間共用 HTTP 連線池。
    '''
    with requests.Session() as session:

        '''
        Reject missing CUDA backends before adding a long-running job to the queue.
        GPU 未就緒就立即提示，不讓學生無謂地等待生成。
        '''
        check_gpu_backend(session)

        '''
        Submit exactly one generation job to the FIFO queue.
        向 FIFO 佇列提交一筆生成工作。
        '''
        job_id = submit_job(session, PARAMS)

        '''
        Print the identifier for troubleshooting or resuming downloads.
        顯示工作編號，方便除錯或重新下載。
        '''
        print('工作編號：', job_id)

        '''
        Wait for this job while the queue processes earlier jobs.
        在其他較早工作執行期間等待本次結果。
        '''
        job = wait_for_job(session, job_id)

        '''
        Download the completed output file or score archive.
        下載完成的音訊、圖片、影片或樂譜封存檔。
        '''
        result = download_file(session, job_id, 'file', job['filename'])

        '''
        Show the actual local result path.
        顯示生成結果的本機路徑。
        '''
        print('生成結果：', result)

'''
Importing this file from another Python program does not generate anything.
從其他 Python 程式匯入時，不會自動生成內容。
'''
if __name__ == '__main__':

    '''
    Start the example generation request.
    執行範例生成請求。
    '''
    main()
