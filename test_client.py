# test_client.py
# 這是用來測試 Server 功能的假 Client
import socketio

# 初始化 Client
sio = socketio.Client()

@sio.event
def connect():
    print("已連線到 Server!")
    # 連線成功後立刻註冊
    sio.emit('register', {'name': 'Test_Bot_1'})

@sio.event
def assign_task(data):
    print(f"\n[收到任務] ID: {data['task_id']}")
    print(f"範圍: {data['range_start']} ~ {data['range_end']}")
    print("假裝正在努力計算中...")
    
    # --- 模擬情境：假設密碼是 '123456' ---
    # 如果 123456 在我的範圍內，我就回報找到了
    # 假設我們只要測試「找到」的情況
    found_it = True 
    secret = "123456" 
    
    if found_it:
        print("!!! 找到了 !!! 回報 Server")
        sio.emit('submit_result', {
            "task_id": data['task_id'],
            "found": True,
            "result": secret
        })

@sio.event
def stop_task(data):
    print(f"\n[任務終止] 贏家是: {data['winner']}")

# 連線到本機 (localhost) 的 5000 port
try:
    sio.connect('http://localhost:5000')
    sio.wait() # 讓程式一直跑，等待事件
except Exception as e:
    print(f"連線失敗: {e}")