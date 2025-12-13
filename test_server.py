from flask import Flask
from flask_socketio import SocketIO, emit
import time
# 移除 import threading，改用 socketio 的方法

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

TARGET_PASSWORD = "36990" 
TARGET_HASH = "a020312b805eb00036b5b5c530bd4816"


print("=== MD5 Cracking Server Started ===")
print(f"Target Password: {TARGET_PASSWORD}")
print(f"Target Hash: {TARGET_HASH}")

@socketio.on('connect')
def handle_connect():
    print(f"✅ [Server] Client connected.")

@socketio.on('register')
def handle_register(data):
    client_name = data.get('name')
    print(f"📝 [Server] Node Registered: {client_name}")
    emit('registration_ack', {'message': 'Ready to crack'})
    
    # 定義發送任務的函式
    def send_crack_task():
        # 使用 socketio.sleep 替代 time.sleep，確保不會卡住非同步伺服器
        socketio.sleep(2) 
        
        task_payload = {
            'task_id': 'JOB_CRACK_001',
            'target_hash': TARGET_HASH,
            'start': 0,
            'end': 5000
        }
        
        print(f"🚀 [Server] Assigning range [0-5000] to {client_name}...")
        socketio.emit('start_task', task_payload)

    # === 關鍵修改：使用 start_background_task ===
    # 這會根據當前的 async_mode (threading/eventlet/gevent) 自動選擇正確的執行方式
    socketio.start_background_task(send_crack_task)

@socketio.on('task_result')
def handle_result(data):
    node = data.get('node_name')
    found = data.get('found')
    result = data.get('result')
    duration = data.get('duration_ms')
    
    print(f"📩 [Server] Result received from {node}")
    if found:
        print(f"🎉🎉🎉 PASSWORD CRACKED by {node}! The password is: {result}")
    else:
        print(f"💨 {node} scanned the range but found nothing.")
    
    print(f"   (Time taken: {duration} ms)")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)