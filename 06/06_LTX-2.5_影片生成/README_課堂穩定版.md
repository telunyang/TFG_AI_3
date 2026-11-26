# LTX-2.5 課堂穩定版｜Refine V11

## 設計原則

- **優先穩定，非追求最高生成速度**。Kaggle T4 15 GiB ×2、30 GiB CPU RAM。
- 保留原本的 GPU 0（DiT）／GPU 1（輔助元件）配置與 Q4_K_M 模型。
- `NODE_CACHE_MODE = 'none'`，降低節點輸出在多次生成間累積。
- `RELEASE_AFTER_GENERATION = False`：不再依賴 `/free` 的非同步回收結果。
- `STOP_COMFY_AFTER_GENERATION = True`：每次影片輸出完成、ComfyUI 佇列清空後，停止 ComfyUI 行程。CPU RAM 由作業系統回收。
- 下一次使用 Notebook 生成或遠端 API 生成前，先檢查服務狀態；若已停止，自動啟動並等待全部雙 GPU Loader 註冊。
- 遠端 `/health` 在 ComfyUI 預期停止時會回報 CUDA 可用；真正生成時才啟動 ComfyUI，避免學生在前置健康檢查階段就被拒絕。
- 模型檔案保存在磁碟，不會因為結束 ComfyUI 而重新下載。

## Kaggle 課堂使用

1. **重新啟動 Kaggle Session**，不要把舊版 ComfyUI 行程沿用到新版。
2. 開啟 `06_LTX-2.5_影片生成.ipynb`，依序執行安裝、模型、ComfyUI 啟動及參數設定 Cells。
3. 執行 T2V／I2V／FLF2V 的生成 Cell。第一次生成完成後 ComfyUI 會自動結束。
4. 第二次直接執行生成 Cell，不用再手動執行「ComfyUI 啟動」Cell。
5. 如需學生透過 Client 生成，啟動最後面的遠端 API Cell，填入 Client 的 `API_URL`。

## 注意事項

- 這是針對已實測「關閉 ComfyUI 便會回收約 21.7 GiB RAM」而採取的保守方式，**沒有完成 Kaggle T4 ×2 實機多輪生成驗證，也不能保證完全不 OOM**。
- 下次生成須重新啟動 ComfyUI、重新讀取模型，因此會比模型常駐慢。
- 如果影片生成中發生 OOM，程序仍可能被系統殺死；下一次工作會偵測後重新啟動服務，但無法恢復被中斷的影片。
- 遠端 API 使用單一 FIFO 工作佇列；生成期間不要另外操作 Notebook 的生成 Cell，以免資源競爭。
- 本 ZIP 另附 `ltx25_kaggle_engine.py` 供檢查。Notebook 的「模型與 Workflow」Cell 會自行寫出同內容的引擎，並不需要手動上傳此檔。
