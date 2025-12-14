# trigger_task.py
import socketio
import time

# 建立 client 實例
sio = socketio.Client()

try:
    # 連線到本機 Server
    sio.connect('http://localhost:5000')
    print("成功連線到 Server，準備發送任務...")

    # 發送開始指令
    # 這裡我們模擬要破解 MD5 為 "e10adc3949ba59abbe56e057f20f883e" (即 "123456")
    sio.emit('start_task', {
        "target_hash": "e10adc3949ba59abbe56e057f20f883e", 
        "length": 6
    })
    print("任務指令已發送！")
    
    # 等一下下讓訊息送出去再斷線
    time.sleep(1)
    sio.disconnect()

except Exception as e:
    print(f"連線失敗: {e}")
    print("請檢查 server.py 是否已經在執行中？")