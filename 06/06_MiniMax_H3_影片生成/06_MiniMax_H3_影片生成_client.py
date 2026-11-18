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

'''
Set the URL displayed in the Notebook ngrok cell.
填入 Notebook 的 ngrok 公開網址。
'''
API_URL = 'https://REPLACE_WITH_YOUR_NGROK_DOMAIN'

'''
Choose t2v, i2v, flf2v, or r2v (1–9 reference images).
選擇 t2v、i2v、flf2v 或 r2v（1～9 張參考圖）。
'''
TASK = 't2v'

'''
Describe the scene; R2V can refer to <Picture 1> etc.
編輯場景描述；R2V 可以使用 <Picture 1> 等標記。
'''
PROMPT = '''
A peaceful Taipei park with gentle wind and natural sounds.
'''.strip()

'''
Set the video dimensions and duration.
設定影片尺寸與長度。
'''
WIDTH, HEIGHT, SECONDS = 384, 224, 5

'''
Set steps and the MiniMax-specific audio shift.
設定步數與 MiniMax 專屬的 Audio Shift。
'''
STEPS, AUDIO_SHIFT = 20, 6.0

'''
Choose reference-image resize mode for R2V (match or max).
設定 R2V 參考圖片縮放方式（match 或 max）。
'''
REF_IMAGE_SIZE = 'match'

'''
Fix the seed or use -1 for random.
固定種子，或用 -1 代表隨機。
'''
SEED = 42

'''
List image paths in first/last or reference order; t2v uses [].
依首尾或參考圖順序填入路徑；t2v 使用 []。
'''
IMAGE_PATHS = []

'''
Send fields supported by the MiniMax H3 Notebook.
傳送 MiniMax H3 Notebook 支援的欄位。
'''
PARAMS = dict(task=TASK, prompt=PROMPT, width=WIDTH, height=HEIGHT,
              seconds=SECONDS, steps=STEPS, audio_shift=AUDIO_SHIFT,
              ref_image_size=REF_IMAGE_SIZE, seed=SEED)

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
Validate the reference-image count for this specific Notebook.
依此 Notebook 支援的模式確認參考圖數量。
'''
IMAGE_COUNTS = {'t2v': (0, 0), 'i2v': (1, 1), 'flf2v': (2, 2), 'r2v': (1, 9)}

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
Submit exactly one logical job; retries reuse its ID and cannot duplicate inference.
每次只提交一筆邏輯工作；重試使用相同 ID，避免重複推論。
'''
def submit_job(session, params=PARAMS, images=IMAGE_PATHS, api_url=API_URL):

    '''
    Validate this notebook's image requirements before opening files.
    先檢查此 Notebook 的圖片張數，再開啟檔案。
    '''
    expected = IMAGE_COUNTS.get(params['task'])
    if expected is None or not expected[0] <= len(images) <= expected[1]:
        raise ValueError(f'模式 {params["task"]} 的參考圖數量不正確；允許範圍：{IMAGE_COUNTS}')

    '''
    Check R2V picture labels against the exact number of uploaded images.
    檢查 R2V Prompt 的圖片編號是否對應實際上傳數量。
    '''
    if params['task'] == 'r2v':
        numbers = {int(n) for n in re.findall(r'<Picture\s+(\d+)>', params.get('prompt', ''), re.I)}
        if any(n < 1 or n > len(images) for n in numbers):
            raise ValueError('MiniMax R2V Prompt 指向不存在的 <Picture N> 圖片。')

    '''
    Assign a stable identity to this request, not to each network attempt.
    同一筆請求固定使用一個 ID，網路重試不重新生成編號。
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

            '''
            Reopen upload streams for each attempt so retries send full files.
            每次重試重新開啟檔案，避免送出已讀完的上傳資料。
            '''
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

            '''
            Retry only temporary overloads and gateway failures.
            只重試暫時滿載及閘道錯誤，不隱藏參數或權限錯誤。
            '''
            if response.status_code not in (429, 502, 503, 504):
                if not response.ok:
                    raise RuntimeError(f'提交失敗 HTTP {response.status_code}: {response.text[:800]}')
                return response.json()['job_id']
            network_failures = 0
            reason = f'HTTP {response.status_code}: {response.text[:200]}'
        except (requests.Timeout, requests.ConnectionError) as error:

            '''
            The response may have been lost after acceptance; the ID prevents duplicates.
            伺服器可能已接受工作卻遺失回應，固定 ID 可防止重複執行。
            '''
            network_failures += 1
            if network_failures >= 12:
                raise ConnectionError(f'連續 12 次連線失敗；請檢查 API_URL、ngrok 連線與工作 {request_id}。') from error
            reason = str(error)[:200]

        '''
        Respect a submission deadline rather than retrying indefinitely.
        設定最長等待期限，避免無限重試。
        '''
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f'提交超過 {MAX_SUBMIT_WAIT} 秒；請稍後檢查服務。Request ID: {request_id}；最後錯誤：{reason}')
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
        Submit exactly one generation job to the FIFO queue.
        向 FIFO 佇列提交一筆生成工作。
        '''
        job_id = submit_job(session, PARAMS, IMAGE_PATHS)

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
        Save the last video frame for continuing I2V/FLF2V generation.
        額外儲存影片最後影格，供接續 I2V／FLF2V 使用。
        '''
        if job.get('last_frame_available'):

            '''
            Download the PNG supplied by the Notebook.
            下載 Notebook 擷取的 PNG 影格。
            '''
            frame = download_file(session, job_id, 'last-frame', 'last_frame.png')

            '''
            Show the saved frame path.
            顯示影格儲存位置。
            '''
            print('最後影格：', frame)

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
