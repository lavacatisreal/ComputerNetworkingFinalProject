# ComputerNetworkingFinalProject
期末實作規劃
根據「社群式分散雲端訓練平台」專案的實作技術與目標，可將工作合理分成三等分，分別聚焦於伺服器端、客戶端與系統整合部分：
## 工作一：控制中心核心（後端邏輯 + 任務管理）
主要負責整個 Flask + WebSocket 伺服器骨架，讓 client 可以連線、註冊、接收任務並回傳結果。
* 建立 Flask 專案與 Flask-SocketIO（或 Flask-Sock）初始化、事件路由（connect、disconnect、自訂 event）。
* 設計 in-memory 資料結構：節點列表（id、名稱、狀態）、當前任務的分片資訊、結果暫存。
* 實作「任務分配與整合」流程：
    * 接收到「開始任務」指令時切分資料。
    * 依節點清單用 emit/broadcast 發送子任務給各節點。
    * 收到節點回傳的 partial result 後更新狀態，全部到齊後計算總結果與統計。
    * 對前端提供必要的 Socket 事件或 REST API（例如：status_update、task_result）。

## 工作二：使用者節點（Client 端程式）
負責開發「節點程式」，讓任意一台電腦啟動 client 就能自動加入系統、接任務、執行、回傳結果，模擬多節點環境。
* 開發 Python client（或簡單的前端 JS client，二擇一即可）與 WebSocket 連線流程。
* 實作節點註冊協定：連線後自動送出 {type: "register", name: "Node_x"}，並處理 server 回覆的確認訊息。
* 實作任務處理：
    * 接收 {task_id, data_chunk} 後執行運算（例如：sum / mean / 模擬延遲），記錄執行時間。
    * 回傳 {task_id, partial_result, duration_ms} 給 server。
    * 加入簡單的 CLI 或小視窗，讓 Demo 時可以看到「節點正在工作 / 完成」的文字輸出。
    * 與工作一同定義好事件名稱與 JSON 格式，確保雙方介面一致。

## 工作三：前端 Dashboard + 整合與測試
負責「看得到的東西」與最終 Demo 的流暢度，包含 web 頁面、資料即時更新，以及整體系統壓力測試與劇本設計。
* 開發伺服器端的 dashboard 頁面（單一 HTML + JS）：
    * 顯示目前在線節點列表、狀態（Idle / Working / Done）、最近任務耗時。
    * 顯示一次任務的總結果（整體 sum/mean 等）與任務完成百分比。
    * 提供一個按鈕「Start Task」透過 WebSocket 或 HTTP 打 API 觸發任務開始。​
    * 用前端 Socket.IO client 收聽 server 的 status_update / task_update，即時更新 DOM。
* 若有時間，加入簡單視覺化（例如用 div 寬度模擬柱狀圖，顯示每個節點貢獻或延遲）。
    * 負責「整體整合與測試」：
    * 規劃 Demo 流程、錄 Demo 影片。
    * 壓測：同時開多個 client、反覆按 Start Task，確認介面與後端都穩定。

## 三種情境
1. 有節點、有解答

* 開 server、啟動 Worker，按 Start Task。

* 其中一個 Worker 找到密碼 → Dashboard 彈出「任務完成」+ 顯示 winner / secret。

2. 有節點、搜尋完但沒找到

* 把 target hash 改成不在 0 ~ 10^length 範圍內的值（例如亂打一個字串）。

* 所有 Worker log 都會印「沒找到」，最後 Dashboard 彈出「任務結束，但沒有人找到密碼」，且狀態顯示 COMPLETED, winner = 無, secret = 未找到。

3. 沒有節點就按 Start

* 不啟動任何 client_node，只開 server 和 Dashboard。

* 直接按 Start Task → server 印 [錯誤] 沒有節點在線，Dashboard 跳出「目前沒有任何 Worker 在線上，無法開始任務。」，狀態保持在 IDLE。
  
1. 啟動控制中心 Server（工作一 + 工作三後端）

在第一個終端機：
```
python server.py
```
看到類似以下訊息代表啟動成功：
```
Running on http://127.0.0.1:5000
```
或同時顯示一個區網 IP（例如 http://140.xxx.xxx.xxx:5000）

2. 啟動一個或多個 Worker 節點（工作二）

在第二個終端機：
```
python client_node.py --name "Worker_1"
python client_node.py --name "Worker_2"
...
```
預期畫面會顯示：
```
已連線到 Server
Registration success / Waiting for tasks...
```
3. 開啟 Dashboard 頁面（工作三前端）

在瀏覽器輸入：
```
http://127.0.0.1:5000/dashboard
```
如果是用別台電腦當 Dashboard，請改成：
```
http://<server-ip>:5000/dashboard
```
（例：http://140.xxx.xxx.xxx:5000/dashboard）

畫面應該會顯示：
上方：連線狀態（連線中 / 已連線）、Start Task 按鈕
中間：節點列表（Worker_1、Worker_2...，狀態為 IDLE）
下方：任務狀態（任務 ID / 狀態 / 贏家 / 密碼）
