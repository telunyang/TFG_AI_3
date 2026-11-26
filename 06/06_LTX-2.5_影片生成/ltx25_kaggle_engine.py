
import asyncio
import io
import math
from fractions import Fraction
import re
import wave
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

COMFY_BASE = os.environ.get("COMFY_BASE", "http://127.0.0.1:8188").rstrip("/")
MODEL_GPU_DEVICE = os.environ.get('LTX25_MODEL_GPU_DEVICE', 'cuda:0')
AUX_GPU_DEVICE = os.environ.get('LTX25_AUX_GPU_DEVICE', 'cuda:1')
COMFY_DIR = Path(os.environ.get("COMFY_DIR", str(Path.home() / 'ai_course/ComfyUI')))
FLOW_REGISTRY_PATH = Path(os.environ.get("FLOW_REGISTRY_PATH", str(Path.home() / 'ai_course/ltx25_local_flows.json')))
WORKFLOW_DIR = Path(os.environ.get(
    "WORKFLOW_DIR",
    str(COMFY_DIR / "user/default/workflows/LTX25-Kaggle"),
))

if not FLOW_REGISTRY_PATH.is_file():
    raise RuntimeError(f"Flow registry missing: {FLOW_REGISTRY_PATH}")

FLOW_REGISTRY = json.loads(FLOW_REGISTRY_PATH.read_text(encoding="utf-8"))

STACK_SCHEMA_VERSION = int(FLOW_REGISTRY.get("schema_version", 0))

MODEL_FILES = {
    tier: item["filename"]
    for tier, item in FLOW_REGISTRY["models"]["transformers"].items()
}
PRIMARY_MODEL_TIER = os.environ.get("LTX25_PRIMARY_MODEL_TIER", "q4km").lower()
FALLBACK_MODEL_TIERS = [
    x.strip().lower()
    for x in os.environ.get("LTX25_FALLBACK_MODEL_TIERS", "").split(",")
    if x.strip()
]

VAE_TILE_SIZE = int(os.environ.get("LTX25_VAE_TILE_SIZE", "512"))
VAE_TILE_OVERLAP = int(os.environ.get("LTX25_VAE_TILE_OVERLAP", "64"))
VAE_TEMPORAL_SIZE = int(os.environ.get("LTX25_VAE_TEMPORAL_SIZE", "32"))
VAE_TEMPORAL_OVERLAP = int(os.environ.get("LTX25_VAE_TEMPORAL_OVERLAP", "8"))

COMFY_LOG_PATH = Path(os.environ.get("LTX25_COMFY_LOG", str(Path.home() / 'ai_course/comfyui_ltx25.log')))
COMFY_PID_PATH = Path(os.environ.get("LTX25_COMFY_PID", str(Path.home() / 'ai_course/comfyui_ltx25.pid')))
TEXT_ENCODER = Path(FLOW_REGISTRY["models"]["text_encoder"]["basename"]).name
VIDEO_VAE = Path(FLOW_REGISTRY["models"]["video_vae"]["filename"]).name
AUDIO_VAE = Path(FLOW_REGISTRY["models"]["audio_vae"]["filename"]).name
UPSCALER = Path(FLOW_REGISTRY["models"]["spatial_upscaler"]["filename"]).name

T2V_I2V_WORKFLOW = WORKFLOW_DIR / FLOW_REGISTRY["workflows"]["t2v_i2v"]["local_name"]
FLF2V_WORKFLOW = WORKFLOW_DIR / "LTX25_FLF2V.json"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_AUDIO_BYTES = 32 * 1024 * 1024

JOBS = {}
JOBS_LOCK = threading.Lock()
EXECUTOR = ThreadPoolExecutor(max_workers=1)



def job_update(job_key, **fields):
    # job_key is the dictionary key; fields may safely contain "job_id".
    with JOBS_LOCK:
        JOBS.setdefault(job_key, {}).update(fields)


def _comfy_http_error(method, path, response):
    try:
        body = response.json()
        detail = json.dumps(body, ensure_ascii=False, indent=2)
    except Exception:
        detail = response.text[:12000]
    raise RuntimeError(
        f"ComfyUI {method} {path} failed: HTTP {response.status_code}\n{detail}"
    )


def comfy_get(path, **kwargs):
    response = requests.get(f"{COMFY_BASE}/{path.lstrip('/')}", **kwargs)
    if not response.ok:
        _comfy_http_error("GET", path, response)
    return response


def comfy_post(path, **kwargs):
    response = requests.post(f"{COMFY_BASE}/{path.lstrip('/')}", **kwargs)
    if not response.ok:
        _comfy_http_error("POST", path, response)
    return response


def get_gguf_loader_choices():
    # Read only the GPU-selectable GGUF loader exposed by this notebook.
    # 只檢查本 Notebook 註冊的雙 GPU GGUF Loader。
    name = 'LTX25GGUFLoaderGPU'
    try:
        spec = comfy_get(f'/object_info/{name}', timeout=30).json()[name]
        return True, spec['input']['required']['unet_name'][0], spec
    except Exception as exc:
        return False, [], {'error': str(exc)}


RELEASE_AFTER_GENERATION = os.environ.get('LTX25_RELEASE_AFTER_GENERATION', '1') == '1'
STOP_AFTER_GENERATION = os.environ.get('LTX25_STOP_AFTER_GENERATION', '1') == '1'
COMFY_PID = int(os.environ['LTX25_COMFY_RUNTIME_PID']) if os.environ.get('LTX25_COMFY_RUNTIME_PID', '').isdigit() else None


def free_comfy():
    """Request one cleanup only after the ComfyUI queue becomes idle."""

    '''
    Wait for the current workflow to leave the active queue before unloading.
    等待目前影片工作完全離開執行佇列後，才允許卸載模型。
    '''
    try:
        for _ in range(15):
            queue = comfy_get('/queue', timeout=5).json()
            if not queue.get('queue_running') and not queue.get('queue_pending'):
                break
            time.sleep(1)
        else:
            print('警告：ComfyUI 仍有工作，為避免中斷其他影片，本次略過清理。', flush=True)
            return False

        '''
        Capture private ComfyUI RAM when the process ID is available.
        若能取得 ComfyUI PID，就測量清理前後的專屬 RAM。
        '''
        process = None
        before = None
        if COMFY_PID is not None:
            try:
                import psutil
                process = psutil.Process(COMFY_PID)
                before = process.memory_full_info().uss / 1024**3
            except (ImportError, OSError, RuntimeError) as exc:
                print(f'USS 診斷無法使用，仍會執行清理：{exc}', flush=True)
                process = None

        '''
        Unload ComfyUI models and clear node-result caches once.
        只送出一次 ComfyUI 模型卸載與節點快取清理請求。
        '''
        comfy_post('/free', json={'unload_models': True, 'free_memory': True}, timeout=15)

        '''
        Allow asynchronous cleanup to finish before reporting memory usage.
        等待背景清理完成，再回報記憶體使用狀態。
        '''
        time.sleep(5)
        if process is not None:
            after = process.memory_full_info().uss / 1024**3
            print(f'ComfyUI 清理請求已送出：USS {before:.2f} → {after:.2f} GiB；'
                  f'變化 {before - after:+.2f} GiB。', flush=True)
        else:
            print('ComfyUI 清理請求已送出（未取得 PID，無法量測 USS）。', flush=True)
        return True
    except Exception as exc:
        '''
        Preserve a valid MP4 even when post-generation cleanup fails.
        清理失敗時保留已生成的 MP4，並清楚顯示警告。
        '''
        print(f'警告：ComfyUI 生成後清理失敗：{type(exc).__name__}: {exc}', flush=True)
        return False


def wait_comfy_ready(timeout=120):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            response = comfy_get("/system_stats", timeout=3)
            if response.ok:
                return True
        except Exception as exc:
            last = exc
        time.sleep(1)
    raise RuntimeError(f"ComfyUI is not ready: {last}")


def validate_dimensions(width, height):
    """Reject nonintegral or unsupported LTX workflow input dimensions."""
    if isinstance(width, bool) or isinstance(height, bool):
        raise ValueError("Video dimensions must be integers")
    try:
        dimensions = (int(width), int(height))
    except (TypeError, ValueError) as exc:
        raise ValueError("Video dimensions must be integers") from exc
    if any(str(value).strip() != str(number) for value, number in zip((width, height), dimensions)):
        raise ValueError("Video dimensions must be integers without truncation")
    if any(number < 256 or number > 4096 or number % 32 for number in dimensions):
        raise ValueError("LTX width and height must be 256..4096 and divisible by 32")
    return dimensions


def save_upload_bytes(data, suffix, prefix):
    input_dir = COMFY_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    name = f"{prefix}_{uuid.uuid4().hex}{suffix.lower()}"
    path = input_dir / name
    path.write_bytes(data)
    return name, path


def ensure_placeholder_image():
    """
    ComfyUI validates LoadImage nodes before execution even when the workflow
    later disables image conditioning. Some downloaded UI workflows contain
    stale example filenames such as Test__00139_.png.

    Keep one valid tiny placeholder in ComfyUI/input and patch unused LoadImage
    nodes to it. The workflow's use-image switch still controls conditioning.
    """
    input_dir = COMFY_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    name = "__ltx25_placeholder__.png"
    path = input_dir / name

    if not path.is_file():
        Image.new("RGB", (64, 64), (0, 0, 0)).save(path, format="PNG")

    return name


def ensure_placeholder_audio():
    """Create a valid one-second silent WAV for unused LoadAudio validation."""
    input_dir = COMFY_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    name = "__ltx25_placeholder__.wav"
    path = input_dir / name
    if not path.is_file():
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 16000)
    return name


def validate_image_bytes(data, suffix):
    if not data:
        raise ValueError("Image is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds {MAX_IMAGE_BYTES / 2**20:.0f} MiB limit.")
    if suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported image extension: {suffix}")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
    except Exception as exc:
        raise ValueError("Invalid/corrupted image.") from exc


def ffprobe_audio_bytes(data, suffix):
    if not data:
        raise ValueError("Audio is empty.")
    if len(data) > MAX_AUDIO_BYTES:
        raise ValueError(f"Audio exceeds {MAX_AUDIO_BYTES / 2**20:.0f} MiB limit.")
    if suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError(f"Unsupported audio extension: {suffix}")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        path = tmp.name

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name,profile:format=duration",
                "-of", "json",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise ValueError("ffprobe could not decode the audio.")
        payload = json.loads(result.stdout or "{}")
        streams = payload.get("streams") or []
        if not streams:
            raise ValueError("No audio stream found.")
        duration = float((payload.get("format") or {}).get("duration") or 0)
        if duration <= 0:
            raise ValueError("Could not determine audio duration.")
        return {
            "codec": streams[0].get("codec_name"),
            "profile": streams[0].get("profile"),
            "duration": duration,
        }
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _norm_label(value):
    text = str(value or "").strip().lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


ALIASES = {
    "prompt": {"prompt", "positive prompt", "prompt positive", "text prompt", "prompt text", "main prompt", "positive text"},
    "width": {"width", "video width", "output width"},
    "height": {"height", "video height", "output height"},
    "seconds": {"duration", "duration in seconds", "seconds", "video duration"},
    "fps": {"fps", "frame rate", "frames per second"},
    "seed": {"seed", "noise seed"},
    "image_strength": {"img strength", "image strength"},
    "video_vae": {"video vae"},
    "audio_vae": {"audio vae"},
    "text_encoder": {"text encoder", "encoder name", "clip name"},
    "upscaler": {"upscale model", "upscaler", "spatial upscaler"},
    "text_to_video": {"text to video", "t2v"},
    "use_image": {"use image input", "use image", "image input"},
    "use_audio": {"use custom audio", "custom audio", "use audio", "audio input"},
    "prompt_enhance": {"enhance positive prompt", "prompt enhance", "enhance prompt"},
    "tile_size": {"tile size"},
    "tile_overlap": {"tile overlap"},
    "temporal_size": {"temporal size"},
    "temporal_overlap": {"temporal overlap"},
    "model": {"ltx model", "diffusion model", "unet", "unet name", "model checkpoint"},
}
ALIASES = {k: {_norm_label(x) for x in v} for k, v in ALIASES.items()}


def _matches_field_label(field, label):
    label = _norm_label(label)
    if label in ALIASES[field]:
        return True
    if field == "prompt" and "prompt" in label:
        blocked = ("negative", "enhanc", "system", "instruction", "translated", "output")
        return not any(word in label for word in blocked)
    return False


def _iter_all_nodes(ui):
    if not isinstance(ui, dict):
        return
    for node in ui.get("nodes", []):
        if isinstance(node, dict):
            yield ui, node
    definitions = ui.get("definitions")
    subgraphs = definitions.get("subgraphs", []) if isinstance(definitions, dict) else []
    for subgraph in subgraphs:
        if isinstance(subgraph, dict):
            yield from _iter_all_nodes(subgraph)


def _remove_ui_link(owner, link_id):
    links = owner.get("links")
    if not isinstance(links, list) or link_id is None:
        return
    kept = []
    for link in links:
        if isinstance(link, list) and link and link[0] == link_id:
            continue
        if isinstance(link, dict) and link.get("id") == link_id:
            continue
        kept.append(link)
    owner["links"] = kept


def _widget_inputs(node):
    return [x for x in (node.get("inputs") or []) if isinstance(x, dict) and "widget" in x]


def _widget_index(node, input_name):
    for i, inp in enumerate(_widget_inputs(node)):
        if inp.get("name") == input_name:
            return i
    return None


def _coerce_widget_value(field, value, ui_type):
    ui_type = str(ui_type or "").upper()
    if ui_type == "BOOLEAN":
        return bool(value)
    if ui_type == "INT":
        if field == "seconds":
            return max(1, int(math.ceil(float(value))))
        return int(round(float(value)))
    if ui_type == "FLOAT":
        return float(value)
    if ui_type in {"STRING", "COMBO"}:
        return str(value)
    return value


def _set_exact_widget(owner, node, field, value, stats):
    values = node.get("widgets_values")
    if not isinstance(values, list):
        return
    for inp in node.get("inputs") or []:
        if not isinstance(inp, dict):
            continue
        label = _norm_label(inp.get("label") or inp.get("name"))
        if not _matches_field_label(field, label):
            continue
        idx = _widget_index(node, inp.get("name"))
        if idx is None or idx >= len(values):
            continue
        # User-requested controls can be linked to helper nodes in a UI workflow
        # (the current GGUF workflow links width/height to ResolutionSelector).
        # Disconnect that incoming UI link so the patched widget value is the
        # value that survives UI -> API conversion.
        if field in {
            "prompt", "width", "height", "seconds", "fps", "seed",
            "image_strength", "text_to_video", "use_image", "use_audio",
            "prompt_enhance", "tile_size", "tile_overlap",
            "temporal_size", "temporal_overlap",
        } and inp.get("link") is not None:
            link_id = inp.get("link")
            _remove_ui_link(owner, link_id)
            inp["link"] = None
            stats[f"disconnected_{field}"] = stats.get(f"disconnected_{field}", 0) + 1
        values[idx] = _coerce_widget_value(field, value, inp.get("type"))
        stats[field] = stats.get(field, 0) + 1


def _patch_primitives(node, values_by_field, stats):
    values = node.get("widgets_values")
    if not isinstance(values, list) or not values:
        return
    node_type = str(node.get("type") or "")
    title = _norm_label(node.get("title"))
    if node_type in {"PrimitiveString", "PrimitiveStringMultiline"} and _matches_field_label("prompt", title):
        values[0] = values_by_field["prompt"]
        stats["prompt"] = stats.get("prompt", 0) + 1
    elif node_type in {"PrimitiveFloat", "PrimitiveInt"} and title in ALIASES["seconds"]:
        values[0] = int(math.ceil(values_by_field["seconds"])) if node_type == "PrimitiveInt" else float(values_by_field["seconds"])
        stats["seconds"] = stats.get("seconds", 0) + 1
    elif node_type in {"PrimitiveFloat", "PrimitiveInt"} and title in ALIASES["fps"]:
        values[0] = int(values_by_field["fps"]) if node_type == "PrimitiveInt" else float(values_by_field["fps"])
        stats["fps"] = stats.get("fps", 0) + 1
    elif node_type == "PrimitiveInt" and title in ALIASES["seed"]:
        values[0] = int(values_by_field["seed"])
        stats["seed"] = stats.get("seed", 0) + 1


def patch_workflow(
    ui, *, mode, prompt, image_name, last_image_name=None, audio_name, model_file,
    width, height, seconds, fps, seed, image_strength,
    tile_size, tile_overlap, temporal_size, temporal_overlap,
):
    text_mode = mode in {"t2v", "a2v"}
    use_image = mode in {"i2v", "ia2v", "flf2v"}
    use_audio = mode in {"a2v", "ia2v"}
    values_by_field = {
        "prompt": prompt, "width": width, "height": height, "seconds": seconds,
        "fps": fps, "seed": seed, "image_strength": image_strength,
        "video_vae": VIDEO_VAE, "audio_vae": AUDIO_VAE,
        "text_encoder": TEXT_ENCODER, "upscaler": UPSCALER,
        "text_to_video": text_mode, "use_image": use_image, "use_audio": use_audio,
        "prompt_enhance": False, "tile_size": tile_size, "tile_overlap": tile_overlap,
        "temporal_size": temporal_size, "temporal_overlap": temporal_overlap,
        "model": model_file,
    }
    stats = {}

    for owner, node in _iter_all_nodes(ui):
        node_type = str(node.get("type") or "")
        widgets = node.get("widgets_values")
        _patch_primitives(node, values_by_field, stats)

        if node_type == "LoadImage" and isinstance(widgets, list) and widgets:
            # FLF2V assigns its ending image by the titled LoadImage node.
            # FLF2V 依照 LoadImage 標題指定結尾圖片。
            if mode == "flf2v" and "last" in _norm_label(node.get("title")):
                widgets[0] = last_image_name
                stats["last_image"] = stats.get("last_image", 0) + 1
            else:
                widgets[0] = image_name
                stats["first_image"] = stats.get("first_image", 0) + 1
            stats["load_image"] = stats.get("load_image", 0) + 1
        elif node_type == "LoadAudio" and isinstance(widgets, list) and widgets:
            widgets[0] = audio_name
            stats["load_audio"] = stats.get("load_audio", 0) + 1
        elif node_type in {"UnetLoaderGGUF", "UNETLoader"} and isinstance(widgets, list) and widgets:
            widgets[0] = model_file
            stats["model"] = stats.get("model", 0) + 1
        elif node_type == "LatentUpscaleModelLoader" and isinstance(widgets, list) and widgets:
            widgets[0] = UPSCALER
            stats["upscaler"] = stats.get("upscaler", 0) + 1

        for field, value in values_by_field.items():
            _set_exact_widget(owner, node, field, value, stats)

    # Contract checks: fail here rather than silently generating with stale defaults.
    required = ["prompt", "width", "height", "seconds", "fps", "seed", "model"]
    if mode in {"i2v", "ia2v", "flf2v"}:
        required.append("load_image")
    if mode == "flf2v":
        required += ["first_image", "last_image"]
    missing = [name for name in required if stats.get(name, 0) == 0]
    if missing:
        raise RuntimeError(
            f"Workflow patch contract failed for mode={mode}: missing controls/nodes {missing}. "
            f"Patch stats={stats}"
        )
    return ui, stats


_OBJECT_INFO_CACHE = {"at": 0.0, "data": None}


def get_object_info_all(max_age=60):
    now = time.time()
    if _OBJECT_INFO_CACHE["data"] is None or now - _OBJECT_INFO_CACHE["at"] > max_age:
        _OBJECT_INFO_CACHE["data"] = comfy_get("/object_info", timeout=60).json()
        _OBJECT_INFO_CACHE["at"] = now
    return _OBJECT_INFO_CACHE["data"]


def convert_workflow(ui_workflow):
    response = comfy_post("/workflow/convert", json=ui_workflow, timeout=120)
    payload = response.json()
    if not isinstance(payload, dict) or not any(
        isinstance(v, dict) and "class_type" in v for v in payload.values()
    ):
        raise RuntimeError(f"Workflow converter returned unexpected payload: {payload}")
    return payload


def normalize_nested_random_noise(api_workflow):
    """Use local Gaussian noise that preserves nested video/audio structure."""
    converted = 0
    for node in api_workflow.values():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") == "RandomNoise":
            node["class_type"] = "LTX25NestedRandomNoise"
            converted += 1
    if converted == 0:
        raise RuntimeError("Converted workflow contains no RandomNoise nodes to normalize.")
    return converted


def normalize_api_workflow_for_gguf(api_workflow, model_file):
    # Place GGUF diffusion on GPU 0 and encoders/VAEs on GPU 1.
    # 將 GGUF Diffusion 指定至 GPU 0，文字編碼器與 VAE 指定至 GPU 1。
    counts = {'transformer': 0, 'text_encoder': 0, 'vae': 0, 'upscaler': 0}
    for node in api_workflow.values():
        kind = node.get('class_type')
        inputs = node.get('inputs', {})
        if kind in {'UNETLoader', 'UnetLoaderGGUF'}:
            node['class_type'] = 'LTX25GGUFLoaderGPU'
            node['inputs'] = {'unet_name': model_file, 'device': MODEL_GPU_DEVICE}
            counts['transformer'] += 1
        elif kind == 'CLIPLoader':
            node['class_type'] = 'LTX25CLIPLoaderGPU'
            node['inputs'] = {**inputs, 'device': AUX_GPU_DEVICE}
            counts['text_encoder'] += 1
        elif kind == 'VAELoader':
            '''
            Correct a legacy FLF2V Video VAE name after UI-to-API conversion.
            Workflow 轉換成 API 格式後，再修正舊版 FLF2V Video VAE 名稱。
            '''
            vae_name = inputs.get('vae_name')
            if isinstance(vae_name, str) and vae_name.startswith('ltx-2.5-video-vae-') and vae_name != VIDEO_VAE:
                inputs = {**inputs, 'vae_name': VIDEO_VAE}
                print(f'Video VAE corrected: {vae_name} -> {VIDEO_VAE}', flush=True)
            node['class_type'] = 'LTX25VAELoaderGPU'
            node['inputs'] = {**inputs, 'device': AUX_GPU_DEVICE}
            counts['vae'] += 1
        elif kind == 'LatentUpscaleModelLoader':
            node['class_type'] = 'LTX25UpscalerLoaderGPU'
            node['inputs'] = {**inputs, 'device': AUX_GPU_DEVICE}
            counts['upscaler'] += 1
    # Reject a workflow that accidentally bypasses either GPU or the two-stage upscaler.
    # 若 Workflow 略過任一 GPU 或缺少雙階段 Upscaler，直接拒絕執行。
    if not all(counts.values()):
        raise RuntimeError(f'Missing dual-GPU component loaders in converted workflow: {counts}')
    print('Independent GPU loader mapping:', counts)
    return sum(counts.values())


def inject_frozen_external_audio(api_workflow, audio_name, seconds):
    """Inject existing audio into both stages of the distilled AV workflow.

    Local-only path:
      LoadAudio -> TrimAudioDuration -> VAEEncodeAudio
      -> LTXVSetAudioRefTokens -> frozen_audio
      -> every active LTXVConcatAVLatent audio input

    The normal positive/negative conditioning graph is left unchanged; only the
    node's frozen_audio output is used. For audio-driven modes, both samplers are
    switched to plain Euler.
    """
    if not audio_name:
        raise RuntimeError("External audio injection requires audio_name.")

    audio_vae_loader = None
    conditioning_node = None
    for node_id, node in api_workflow.items():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") == "VAELoader" and (node.get("inputs") or {}).get("vae_name") == AUDIO_VAE:
            audio_vae_loader = str(node_id)
        if conditioning_node is None and node.get("class_type") == "LTXVConditioning":
            conditioning_node = str(node_id)

    if audio_vae_loader is None:
        raise RuntimeError(f"Audio VAELoader not found for {AUDIO_VAE!r}.")
    if conditioning_node is None:
        raise RuntimeError("LTXVConditioning not found in converted workflow.")

    def fresh_id(base):
        candidate = base
        n = 1
        while candidate in api_workflow:
            n += 1
            candidate = f"{base}_{n}"
        return candidate

    load_id = fresh_id("ltx25_external_audio")
    trim_id = fresh_id("ltx25_trim_audio")
    encode_id = fresh_id("ltx25_encode_audio")
    freeze_id = fresh_id("ltx25_freeze_audio")

    api_workflow[load_id] = {
        "class_type": "LoadAudio",
        "inputs": {"audio": audio_name},
        "_meta": {"title": "LTX25 External Audio"},
    }
    api_workflow[trim_id] = {
        "class_type": "TrimAudioDuration",
        "inputs": {
            "audio": [load_id, 0],
            "start_index": 0.0,
            "duration": float(seconds),
        },
        "_meta": {"title": "LTX25 Trim External Audio"},
    }
    api_workflow[encode_id] = {
        "class_type": "VAEEncodeAudio",
        "inputs": {
            "audio": [trim_id, 0],
            "vae": [audio_vae_loader, 0],
        },
        "_meta": {"title": "LTX25 Encode External Audio"},
    }
    api_workflow[freeze_id] = {
        "class_type": "LTXVSetAudioRefTokens",
        "inputs": {
            "positive": [conditioning_node, 0],
            "negative": [conditioning_node, 1],
            "audio_latent": [encode_id, 0],
        },
        "_meta": {"title": "LTX25 Freeze External Audio"},
    }

    concat_count = 0
    sampler_count = 0
    for node in api_workflow.values():
        if not isinstance(node, dict):
            continue
        class_type = node.get("class_type")
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        if class_type == "LTXVConcatAVLatent":
            # Official distilled A2V keeps the same encoded audio frozen in both stages.
            inputs["audio_latent"] = [freeze_id, 2]
            concat_count += 1
        elif class_type == "KSamplerSelect":
            inputs["sampler_name"] = "euler"
            sampler_count += 1

    if concat_count < 2:
        raise RuntimeError(
            "Expected a two-stage AV workflow with at least two LTXVConcatAVLatent nodes; "
            f"found {concat_count}. The pinned workflow may have changed."
        )
    if sampler_count < 2:
        raise RuntimeError(
            "Expected at least two KSamplerSelect nodes for the two-stage audio path; "
            f"found {sampler_count}."
        )

    return {
        "frozen_audio_concat_nodes": concat_count,
        "euler_samplers": sampler_count,
    }


def _is_connection(value):
    return (
        isinstance(value, list) and len(value) == 2
        and isinstance(value[0], (str, int)) and isinstance(value[1], int)
    )


def validate_api_workflow(api_workflow):
    """Structural validation against ComfyUI /object_info without queueing GPU work.\n\n    Supports normal required inputs plus newer grouped/dynamic inputs\n    (for example Autogrow values.a / values.b / ...).\n    """
    object_info = get_object_info_all()
    errors = []
    for node_id, node in api_workflow.items():
        if not isinstance(node, dict) or "class_type" not in node:
            continue
        class_type = node["class_type"]
        spec = object_info.get(class_type)
        if not isinstance(spec, dict):
            errors.append(f"node {node_id}: class_type {class_type!r} is not registered")
            continue
        inputs = node.get("inputs") or {}
        groups = spec.get("input") or {}
        required = groups.get("required") or {}
        optional = groups.get("optional") or {}
        for name in required:
            if name in inputs:
                continue

            # Switch branches are lazy/conditional inputs. Only the branch
            # selected by `switch` is requested by current ComfyUI.
            if class_type in {"ComfySwitchNode", "ComfySoftSwitchNode"} and name in {"on_false", "on_true"}:
                switch_value = inputs.get("switch")
                if isinstance(switch_value, bool):
                    selected = "on_true" if switch_value else "on_false"
                    if name != selected:
                        continue
                    # If the statically selected branch is missing, fall through
                    # and report it. A linked/dynamic switch is deferred.
                else:
                    continue

            # ComfyUI's newer schema supports grouped/dynamic inputs such as
            # io.Autogrow.Input("values", ...). The converted API workflow does
            # not contain a literal "values" key; it contains children such as
            # "values.a", "values.b", ... instead.
            #
            # Treat the required group as present when at least one child key
            # exists. This is generic and is not hard-coded to ComfyMathExpression.
            dynamic_prefix = f"{name}."
            has_dynamic_child = any(
                isinstance(input_name, str) and input_name.startswith(dynamic_prefix)
                for input_name in inputs
            )
            if has_dynamic_child:
                continue

            errors.append(f"node {node_id} {class_type}: missing required input {name!r}")

        definitions = dict(optional)
        definitions.update(required)
        for name, value in inputs.items():
            # LoadImage/LoadAudio file lists are dynamic. /object_info may have
            # been cached before a request uploaded its file, so do not use the
            # cached combo list as our own file-existence validator. ComfyUI's
            # node validation remains authoritative when /prompt is queued.
            if (class_type == "LoadAudio" and name == "audio") or (class_type == "LoadImage" and name == "image"):
                continue

            definition = definitions.get(name)
            if not isinstance(definition, (list, tuple)) or not definition:
                continue
            choices = definition[0]
            if isinstance(choices, list) and not _is_connection(value):
                if value not in choices:
                    preview = choices[:20]
                    errors.append(
                        f"node {node_id} {class_type}.{name}: {value!r} not in selectable choices {preview!r}"
                    )
    if errors:
        raise RuntimeError("ComfyUI structural preflight failed:\n" + "\n".join(errors[:50]))
    return True


def queue_prompt(api_workflow):
    response = comfy_post(
        "/prompt",
        json={"prompt": api_workflow, "client_id": str(uuid.uuid4())},
        timeout=120,
    )
    payload = response.json()
    if payload.get("node_errors"):
        raise RuntimeError(
            "ComfyUI rejected workflow:\n"
            + json.dumps(payload["node_errors"], ensure_ascii=False, indent=2)
        )
    prompt_id = payload.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI did not return prompt_id: {payload}")
    return prompt_id


def comfy_crash_diagnostics():
    parts = []

    pid = None
    try:
        if COMFY_PID_PATH.is_file():
            pid = int(COMFY_PID_PATH.read_text(encoding="utf-8").strip())
            try:
                os.kill(pid, 0)
                parts.append(f"ComfyUI PID {pid} still exists.")
            except OSError:
                parts.append(f"ComfyUI PID {pid} is no longer running.")
    except Exception as exc:
        parts.append(f"PID check failed: {exc}")

    try:
        meminfo = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meminfo[key] = value.strip()
        parts.append(
            "Host memory after failure: "
            f"MemAvailable={meminfo.get('MemAvailable', '?')}, "
            f"SwapFree={meminfo.get('SwapFree', '?')}."
        )
    except Exception:
        pass

    try:
        if COMFY_LOG_PATH.is_file():
            tail = COMFY_LOG_PATH.read_text(errors="replace")[-7000:]
            parts.append("ComfyUI log tail:\n" + tail)
    except Exception as exc:
        parts.append(f"Could not read ComfyUI log: {exc}")

    return "\n".join(parts)


def _looks_like_connection_loss(exc):
    text = str(exc).lower()
    return (
        "connection refused" in text
        or "failed to establish a new connection" in text
        or "max retries exceeded" in text
    )


def wait_prompt(prompt_id):
    while True:
        try:
            payload = comfy_get(
                f"/history/{prompt_id}",
                timeout=60,
            ).json()
        except Exception as exc:
            if _looks_like_connection_loss(exc):
                raise RuntimeError(
                    "ComfyUI became unreachable during generation. "
                    "The ComfyUI process probably exited or was killed by memory pressure.\n"
                    + comfy_crash_diagnostics()
                ) from exc
            raise

        if prompt_id in payload:
            history = payload[prompt_id]
            status = history.get("status", {})
            if status.get("status_str") == "error":
                # Show only the failing node and traceback, never megabytes of latent tensors.
                # 只輸出失敗節點與 traceback，避免將大型 latent tensor 列印到畫面。
                details = [entry[1] for entry in status.get("messages", []) if entry[0] == "execution_error"]
                if details:
                    error = details[-1]
                    raise RuntimeError(
                        f"ComfyUI node {error.get('node_id')} ({error.get('node_type')}): "
                        f"{error.get('exception_type')}: {error.get('exception_message')}\n"
                        + "".join(error.get('traceback', [])[-12:])
                    )
                raise RuntimeError(f"ComfyUI failed: {status.get('messages', [])[-3:]}")
            return history
        time.sleep(3)


def extract_output_item(history):
    # Prefer video-like outputs. Some nodes use "videos", older wrappers use
    # "gifs", and newer/custom nodes may expose generic "files".
    video_exts = {".mp4", ".webm", ".mov", ".mkv", ".gif"}
    fallback = None

    for output in history.get("outputs", {}).values():
        if not isinstance(output, dict):
            continue
        for key in ("videos", "gifs", "images", "files"):
            items = output.get(key, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict) or not item.get("filename"):
                    continue
                suffix = Path(item["filename"]).suffix.lower()
                if key in {"videos", "gifs"} or suffix in video_exts:
                    return item
                if fallback is None:
                    fallback = item

    if fallback is not None:
        return fallback
    raise RuntimeError("Generation completed but no output file was found in ComfyUI history.")


def materialize_output(job_id, item):
    output_dir = Path(os.environ.get("LTX25_OUTPUT_DIR", str(Path.home() / "ai_course/ltx25_api_outputs")))
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = item.get("filename", f"{job_id}.mp4")
    suffix = Path(filename).suffix or ".mp4"
    target = output_dir / f"{job_id}{suffix}"

    response = comfy_get(
        "/view",
        params=item,
        timeout=600,
    )
    target.write_bytes(response.content)
    return target


def mux_original_audio(job_id, video_path, audio_name):
    """Mux the original uploaded audio back onto the generated video.

    The latent audio drives generation, but the delivered MP4 uses the user's
    original waveform rather than a VAE-decoded reconstruction.
    """
    audio_path = COMFY_DIR / "input" / audio_name
    if not audio_path.is_file():
        raise RuntimeError(f"Uploaded audio disappeared: {audio_path}")

    output_dir = Path(os.environ.get("LTX25_OUTPUT_DIR", str(Path.home() / "ai_course/ltx25_api_outputs")))
    target = output_dir / f"{job_id}_with_input_audio.mp4"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(target),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio mux failed: {result.stderr[:4000]}")
    return target



'''
Read real encoded video properties; a completed model job alone is not proof.
讀取影片實際編碼資訊，模型回報完成並不等於成品通過驗證。
'''
def probe_video_contract(path):
    """Return the measured video stream and duration using FFprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,duration:format=duration",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    data = json.loads(result.stdout)
    streams = data.get("streams") or []
    if not streams:
        raise ValueError("Generated file has no video stream")
    video = streams[0]
    duration = float(video.get("duration") or data.get("format", {}).get("duration") or 0)
    rate = float(Fraction(video.get("avg_frame_rate", "0/1")))
    if duration <= 0 or rate <= 0:
        raise ValueError("Cannot verify video duration or FPS")
    return {"width": int(video["width"]), "height": int(video["height"]),
            "fps": rate, "duration": duration}


'''
Honor final output dimensions without sending invalid half-size LTX inputs.
尊重使用者的最終影片尺寸，不把不合法的半尺寸送入 LTX 模型。
'''
def finalize_video_contract(job_id, path, params):
    """Verify raw output, disclose x2 scaling, and optionally normalize."""
    requested_width, requested_height = validate_dimensions(params["width"], params["height"])
    fps, seconds = int(params["fps"]), float(params["seconds"])
    policy = params.get("output_policy", "exact_final")
    if policy not in ("exact_final", "native"):
        raise ValueError("output_policy must be exact_final or native")
    if fps < 1 or fps > 60 or seconds <= 0:
        raise ValueError("Invalid requested FPS or duration")
    raw = probe_video_contract(path)
    dimensions = (raw["width"], raw["height"])
    requested = (requested_width, requested_height)
    if dimensions not in (requested, (2 * requested_width, 2 * requested_height)):
        raise ValueError(f"Unexpected raw LTX output {dimensions}; requested {requested}; do not silently resize")
    tolerance_seconds = max(0.1, 2.0 / fps)
    if abs(raw["fps"] - fps) > 0.01:
        raise ValueError(f"LTX output FPS {raw['fps']} differs from requested {fps}")
    if abs(raw["duration"] - seconds) > tolerance_seconds:
        raise ValueError(f"LTX output duration {raw['duration']:.3f}s differs from {seconds}s by more than {tolerance_seconds:.3f}s")
    delivered_path = Path(path)
    processed = False
    if policy == "exact_final" and dimensions != requested:
        delivered_path = Path(path).with_name(Path(path).stem + "_final.mp4")
        staging = delivered_path.with_suffix(".part.mp4")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(path),
                 "-vf", f"scale={requested_width}:{requested_height}:flags=lanczos",
                 "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                 "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart",
                 str(staging)],
                check=True, capture_output=True, text=True, timeout=600,
            )
            staging.replace(delivered_path)
        finally:
            staging.unlink(missing_ok=True)
        processed = True
    final = probe_video_contract(delivered_path)
    if policy == "exact_final" and (final["width"], final["height"]) != requested:
        raise ValueError("Normalized final video does not match requested dimensions")
    if abs(final["fps"] - fps) > 0.01 or abs(final["duration"] - seconds) > tolerance_seconds:
        raise ValueError("Final video FPS/duration verification failed")
    audit = {
        "requested": {"width": requested_width, "height": requested_height, "fps": fps, "seconds": seconds},
        "provider_input": {"width": requested_width, "height": requested_height},
        "raw_output": raw,
        "delivered_output": final,
        "spatial_scale": {"width": raw["width"] / requested_width, "height": raw["height"] / requested_height},
        "output_policy": policy,
        "postprocessed": processed,
        "duration_tolerance_seconds": tolerance_seconds,
    }
    job_update(job_id, media_contract=audit)
    print("LTX media contract:", json.dumps(audit, ensure_ascii=False), flush=True)
    return delivered_path


def looks_like_oom(exc):
    text = str(exc).lower()
    needles = [
        "cuda out of memory",
        "out of memory",
        "not enough memory",
        "failed to allocate",
        "cublas_status_alloc_failed",
        "cudaerror: out of memory",
    ]
    return any(n in text for n in needles)


def choose_workflow(mode):
    if mode == "flf2v":
        if not FLF2V_WORKFLOW.is_file():
            raise RuntimeError(f"FLF2V workflow missing: {FLF2V_WORKFLOW}")
        return FLF2V_WORKFLOW
    if mode not in {"t2v", "i2v", "a2v", "ia2v"}:
        raise RuntimeError(f"Unsupported mode: {mode}")
    if not T2V_I2V_WORKFLOW.is_file():
        raise RuntimeError(f"Base workflow missing: {T2V_I2V_WORKFLOW}")
    return T2V_I2V_WORKFLOW


def prepare_api_workflow(params, tier):
    mode = params["mode"]
    model_file = MODEL_FILES[tier]
    workflow_path = choose_workflow(mode)
    validate_dimensions(params["width"], params["height"])
    ui = json.loads(workflow_path.read_text(encoding="utf-8"))
    ui, patch_stats = patch_workflow(
        ui,
        mode=mode,
        prompt=params["prompt"],
        image_name=params["image_name"],
        last_image_name=params.get("last_image_name"),
        audio_name=params["audio_name"],
        model_file=model_file,
        width=params["width"],
        height=params["height"],
        seconds=params["seconds"],
        fps=params["fps"],
        seed=params["seed"],
        image_strength=params["image_strength"],
        tile_size=params["vae_tile_size"],
        tile_overlap=params["vae_tile_overlap"],
        temporal_size=params["vae_temporal_size"],
        temporal_overlap=params["vae_temporal_overlap"],
    )
    api_workflow = convert_workflow(ui)
    nested_noise_nodes = normalize_nested_random_noise(api_workflow)
    patch_stats["nested_random_noise"] = nested_noise_nodes
    normalized_loaders = normalize_api_workflow_for_gguf(api_workflow, model_file)
    if mode == "flf2v":
        # Both stages must condition on the opening and closing frames.
        # 兩個階段都必須加入起始與結尾影格條件。
        guides = [node for node in api_workflow.values() if node.get("class_type") == "LTXVAddGuide"]
        frame_ids = [node.get("inputs", {}).get("frame_idx") for node in guides]
        if frame_ids.count(0) < 2 or frame_ids.count(-1) < 2:
            raise RuntimeError(f"FLF2V requires first/last guides in both stages: {frame_ids}")
        image_names = {node.get("inputs", {}).get("image") for node in api_workflow.values()
                       if node.get("class_type") == "LoadImage"}
        if not {params["image_name"], params["last_image_name"]}.issubset(image_names):
            raise RuntimeError(f"FLF2V did not bind both images: {image_names}")
    if normalized_loaders:
        patch_stats["api_unet_to_gguf"] = normalized_loaders
    if mode in {"a2v", "ia2v"}:
        audio_stats = inject_frozen_external_audio(
            api_workflow, params["audio_name"], params["seconds"]
        )
        patch_stats.update(audio_stats)
    validate_api_workflow(api_workflow)
    return workflow_path, api_workflow, patch_stats




def stop_comfy_process():
    """Stop the current ComfyUI process after the queue becomes idle."""
    if COMFY_PID is None:
        print('未設定 ComfyUI PID，略過停止服務。', flush=True)
        return False
    try:
        import psutil
        process = psutil.Process(COMFY_PID)
    except Exception as exc:
        print(f'無法取得 ComfyUI 行程，略過停止服務：{exc}', flush=True)
        return False
    try:
        for _ in range(15):
            queue = comfy_get('/queue', timeout=5).json()
            if not queue.get('queue_running') and not queue.get('queue_pending'):
                break
            time.sleep(1)
        else:
            print('警告：ComfyUI 仍有工作，略過停止服務。', flush=True)
            return False
    except Exception as exc:
        if process.is_running():
            print(f'警告：無法確認 ComfyUI 工作是否完成，為避免中斷輸出，本次不停止服務：{exc}', flush=True)
            return False
        print('ComfyUI 已不在執行，無須再次停止。', flush=True)
        return True
    try:
        process.terminate()
        process.wait(timeout=30)
        print('ComfyUI 已停止，將於下一次生成前自動重新啟動。', flush=True)
        return True
    except Exception as exc:
        print(f'停止 ComfyUI 失敗：{exc}', flush=True)
        return False

def run_once(job_id, params, tier):
    model_file = MODEL_FILES[tier]

    loader_ready, gguf_choices, diagnostic = get_gguf_loader_choices()
    if not loader_ready:
        message = diagnostic.get('error', diagnostic)
        raise RuntimeError(
            'ComfyUI 的 LTX25GGUFLoaderGPU 尚未就緒；請先重新啟動 ComfyUI 啟動 Cell。'
            f' 診斷資訊：{message}'
        )
    if model_file not in gguf_choices:
        raise RuntimeError(
            f"Model exists on disk but LTX25GGUFLoaderGPU cannot select {model_file!r}. "
            f"Choices={gguf_choices}"
        )

    job_update(job_id, status="preparing", message=f"Patching/validating workflow with {tier}.")
    workflow_path, api_workflow, patch_stats = prepare_api_workflow(params, tier)
    job_update(
        job_id,
        workflow=str(workflow_path),
        patch_stats=patch_stats,
        message=f"Workflow structurally validated with {tier}; queueing ComfyUI.",
    )

    prompt_id = queue_prompt(api_workflow)
    job_update(
        job_id,
        prompt_id=prompt_id,
        status="running",
        message=f"ComfyUI is generating with {tier}.",
    )

    '''
    Finish video output before releasing the models; always clean up after a submitted job.
    先完成影片輸出，工作結束後再清理模型；失敗時也會嘗試安全清理。
    '''
    try:
        history = wait_prompt(prompt_id)
        item = extract_output_item(history)
        result_path = materialize_output(job_id, item)
        if params["mode"] in {"a2v", "ia2v"}:
            result_path = mux_original_audio(job_id, result_path, params["audio_name"])
        return finalize_video_contract(job_id, result_path, params)
    finally:
        if RELEASE_AFTER_GENERATION:
            free_comfy()
        if STOP_AFTER_GENERATION:
            stop_comfy_process()


def worker(job_id, params):
    try:
        job_update(job_id, status="preparing", message="Preparing local ComfyUI workflow.")
        # Model policy comes from this Kaggle notebook.
        configured_chain = [PRIMARY_MODEL_TIER] + [
            tier for tier in FALLBACK_MODEL_TIERS
            if tier != PRIMARY_MODEL_TIER
        ]

        for tier in configured_chain:
            if tier not in MODEL_FILES:
                raise RuntimeError(
                    f"Notebook model policy contains unsupported tier {tier!r}. "
                    f"Supported: {sorted(MODEL_FILES)}"
                )

        # Skip configured fallback tiers that have not been downloaded.
        available_chain = []
        for tier in configured_chain:
            model_path = COMFY_DIR / "models/diffusion_models" / MODEL_FILES[tier]
            if model_path.is_file():
                available_chain.append(tier)

        if not available_chain:
            raise RuntimeError(
                "No configured model tier is downloaded. "
                f"Notebook policy: {configured_chain}"
            )

        result = None
        last_error = None
        for index, tier in enumerate(available_chain):
            try:
                result = run_once(job_id, params, tier)
                break
            except Exception as exc:
                last_error = exc
                is_last = index == len(available_chain) - 1
                if is_last or not looks_like_oom(exc):
                    raise

                next_tier = available_chain[index + 1]
                job_update(
                    job_id,
                    status="retrying",
                    active_model_tier=next_tier,
                    message=f"{tier} failed with an OOM-like error; retrying {next_tier}.",
                    last_tier_error=str(exc),
                )

        if result is None:
            raise RuntimeError(f"All model tiers failed. Last error: {last_error}")

        job_update(
            job_id,
            status="completed",
            result_path=str(result),
            message="Generation completed.",
        )

    except Exception as exc:
        job_update(
            job_id,
            status="failed",
            error=str(exc),
            message="Generation failed.",
        )


def _sample_preflight_params(mode):
    return {
        "mode": mode,
        "prompt": "LTX-2.5 structural preflight",
        "width": 608,
        "height": 352,
        "seconds": 3.0,
        "fps": 24,
        "seed": 42,
        "image_strength": 0.7,
        "vae_tile_size": VAE_TILE_SIZE,
        "vae_tile_overlap": VAE_TILE_OVERLAP,
        "vae_temporal_size": VAE_TEMPORAL_SIZE,
        "vae_temporal_overlap": VAE_TEMPORAL_OVERLAP,
        "image_name": ensure_placeholder_image(),
        "audio_name": ensure_placeholder_audio(),
        "audio_info": None,
    }


_PREFLIGHT_CACHE = {"at": 0.0, "data": None}


def preflight_all_modes(max_age=30):
    now = time.time()
    if _PREFLIGHT_CACHE["data"] is not None and now - _PREFLIGHT_CACHE["at"] <= max_age:
        return _PREFLIGHT_CACHE["data"]
    result = {}
    for mode in ("t2v", "i2v", "a2v", "ia2v"):
        try:
            workflow_path, _, stats = prepare_api_workflow(
                _sample_preflight_params(mode), PRIMARY_MODEL_TIER
            )
            result[mode] = {
                "ok": True,
                "workflow": str(workflow_path),
                "patch_stats": stats,
            }
        except Exception as exc:
            result[mode] = {
                "ok": False,
                "workflow": str(T2V_I2V_WORKFLOW),
                "error": str(exc),
            }
    _PREFLIGHT_CACHE["at"] = now
    _PREFLIGHT_CACHE["data"] = result
    return result


