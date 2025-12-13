# test_trigger.py
import socketio
import time

# 這是模擬 Dashboard 的行為
sio = socketio.Client()

SERVER_URL = 'http://localhost:5000'

# 設定題目：密碼 "003699" (6位數)
# MD5("003699") = 47855353697960305086580556156730
TARGET_HASH = "98ff8943c652e4b68734299ee673cfc0"
PASSWORD_LENGTH = 6

@sio.event
def connect():
    print("Dashboard (模擬) 已連線")
    
    # 等待一下確保連線穩定
    time.sleep(1)
    
    print(f"發送破解任務... 目標長度: {PASSWORD_LENGTH}")
    # 觸發 Server 的 'start_task' 事件
    sio.emit('start_task', {
        'target_hash': TARGET_HASH,
        'length': PASSWORD_LENGTH
    })

@sio.on('task_completed')
def on_complete(data):
    print(f"🎉 收到任務完成通知！")
    print(f"   - 贏家: {data.get('winner')}")
    print(f"   - 密碼: {data.get('secret')}")
    sio.disconnect()

if __name__ == '__main__':
    try:
        sio.connect(SERVER_URL)
        sio.wait()
    except KeyboardInterrupt:
        pass