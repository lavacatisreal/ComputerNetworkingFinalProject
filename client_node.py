import socketio
import time
import argparse
import random
import sys
import hashlib
from colorama import init, Fore, Style

# 初始化顏色輸出
init(autoreset=True)

sio = socketio.Client()
NODE_NAME = ""
SERVER_URL = ""

# 用來控制是否要停止目前的運算 (例如別人先找到了)
stop_flag = False

# --- 輔助函式 ---
def log_info(msg):
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {msg}")

def log_success(msg):
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {msg}")

def log_working(msg):
    print(f"{Fore.YELLOW}[WORKING]{Style.RESET_ALL} {msg}")

def log_error(msg):
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {msg}")

# --- WebSocket 事件 ---

@sio.event
def connect():
    log_success(f"Connected to server at {SERVER_URL}")
    register_data = {'name': NODE_NAME} # Server 預期 data.get('name')
    log_info(f"Sending registration: {register_data}")
    sio.emit('register', register_data)

@sio.event
def disconnect():
    log_error("Disconnected from server.")

# 修改 1: 對應 Server 的 'registration_success'
@sio.on('registration_success')
def on_registration_success(data):
    log_success(f"Server response: {data.get('msg')}")
    log_info("Waiting for tasks...")

# 修改 2: 新增 'stop_task' 處理
@sio.on('stop_task')
def on_stop_task(data):
    global stop_flag
    winner = data.get('winner', 'Unknown')
    log_info(f"🛑 Task stopped! Winner is: {winner}")
    stop_flag = True # 設定旗標，讓運算迴圈停下來

# 修改 3: 對應 Server 的 'assign_task'
@sio.on('assign_task')
def on_assign_task(data):
    global stop_flag
    stop_flag = False # 重置停止旗標
    
    task_id = data.get('task_id')
    target_hash = data.get('target_hash')
    
    # 讀取 Server 傳來的參數名稱
    range_start = data.get('range_start') 
    range_end = data.get('range_end')
    prefix_length = data.get('prefix_length', 6) # 密碼長度，用於補零
    
    log_working(f"Task [{task_id}] Received.")
    log_info(f"Scanning: {range_start} ~ {range_end} (Length: {prefix_length})")
    
    start_time = time.time()
    found_password = None
    
    # --- 暴力破解迴圈 ---
    for i in range(range_start, range_end): # 注意 Python range 不包含結尾，Server 邏輯若是包含則需 +1
        # 檢查是否收到停止指令
        if stop_flag:
            log_info("Received stop signal. Aborting task...")
            return

        # 格式化密碼：例如 i=5, length=6 => "000005"
        candidate = str(i).zfill(prefix_length)
        
        # 計算 Hash
        candidate_hash = hashlib.md5(candidate.encode()).hexdigest()
        
        if candidate_hash == target_hash:
            found_password = candidate
            log_success(f"🔥 FOUND IT! Password: {candidate}")
            break # 找到就跳出
            
        # 為了避免完全卡死 SocketIO 的心跳包，每 1000 次稍微讓出 CPU (選擇性)
        if i % 5000 == 0:
            sio.sleep(0) 

    # --- 準備回傳結果 ---
    if stop_flag:
        return # 如果是被中止的，就不回傳結果了

    # 修改 4: 對應 Server 的 'submit_result' 格式
    response = {
        "task_id": task_id,
        "found": bool(found_password),
        "result": found_password if found_password else ""
    }
    
    sio.emit('submit_result', response)
    
    if not found_password:
        log_info(f"Range scanned. Nothing found.")
    
    log_info("Returning to IDLE state...")

# --- 主程式 ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, default=f"Node_{random.randint(1000, 9999)}")
    parser.add_argument('--server', type=str, default='http://localhost:5000')
    args = parser.parse_args()
    
    NODE_NAME = args.name
    SERVER_URL = args.server
    
    print(f"{Fore.MAGENTA}=== Distributed Client Node (Adapted) ==={Style.RESET_ALL}")
    print(f"Node: {NODE_NAME} | Server: {SERVER_URL}")
    
    try:
        # 強制使用 websocket 以避免 polling 問題
        sio.connect(SERVER_URL, transports=['websocket'])
        sio.wait()
    except Exception as e:
        log_error(f"Connection Error: {e}")