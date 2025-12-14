# server.py
# 這是你的「工作一」核心程式碼
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import uuid
import math

# 初始化 Flask 和 SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# cors_allowed_origins="*" 非常重要，讓你的隊友(Dashboard/Client)可以從不同電腦連上來
socketio = SocketIO(app, cors_allowed_origins="*")

# --- 全域變數 (In-Memory Database) ---
connected_nodes = {}  # 存節點資料: {'sid': {'name': 'Node A', 'status': 'IDLE'}}

current_task = {
    "id": None,
    "target_hash": "",
    "total_range": 0,
    "status": "IDLE",       # IDLE, RUNNING, COMPLETED
    "winner": None,         # 誰找到了
    "secret_found": None,   # 找到的密碼原文
    "start_time": 0,
    "finished_nodes": 0   # ✅ 新增：已回報的節點數
}

# --- 輔助函式：廣播節點列表給 Dashboard ---
@app.route("/dashboard")
def dashboard():
    # 預設載入時可以先給一些初始資料（也可以先不傳）
    return render_template("dashboard.html")

def broadcast_node_list():
    # 整理一下資料格式，只傳送需要的資訊
    nodes_list = []
    for sid, info in connected_nodes.items():
        nodes_list.append({
            "id": sid,
            "name": info['name'],
            "status": info['status']
        })
    # 發送給所有人 (主要是 Dashboard 會聽這個事件)
    socketio.emit('update_node_list', nodes_list)

# --- 事件 1: 連線與斷線 ---
@socketio.on('connect')
def handle_connect():
    print(f"[系統] 新連線建立: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_nodes:
        name = connected_nodes[request.sid]['name']
        print(f"[系統] 節點斷線: {name}")
        del connected_nodes[request.sid]
        broadcast_node_list()

# --- 事件 2: 節點註冊 (Client -> Server) ---
@socketio.on('register')
def handle_register(data):
    # data 格式預期: {'name': '我的電腦A'}
    node_name = data.get('name', f"Node_{request.sid[:4]}")
    
    connected_nodes[request.sid] = {
        "name": node_name,
        "status": "IDLE"
    }
    print(f"[註冊] {node_name} 加入了戰局")
    emit('registration_success', {'msg': f'Hello {node_name}'})
    broadcast_node_list()

# --- 事件 3: 開始任務 (Dashboard -> Server) ---
@socketio.on('start_task')
def handle_start_task(data):
    # data 預期: {"target_hash": "e10adc3949ba59abbe56e057f20f883e", "length": 6}
    target_hash = data.get('target_hash')
    pwd_length = int(data.get('length', 6))
    
    # 計算總組合數 (假設全是數字)
    total_combinations = 10 ** pwd_length
    
    # 找出所有閒置的節點 (這裡簡化為所有連線中的節點)
    available_nodes = list(connected_nodes.keys())
    node_count = len(available_nodes)
    
    if node_count == 0:
        print("[錯誤] 沒有節點在線，無法開始任務")
        socketio.emit('task_error', {
            "reason": "NO_NODES",
            "message": "目前沒有任何 Worker 在線上，無法開始任務。"
        })
        return

    # 初始化任務狀態
    task_id = str(uuid.uuid4())
    current_task['id'] = task_id
    current_task['target_hash'] = target_hash
    current_task['status'] = "RUNNING"
    current_task['winner'] = None
    current_task['secret_found'] = None
    current_task['finished_nodes'] = 0   # ✅ 重置計數
    
    # 切分任務範圍
    chunk_size = math.ceil(total_combinations / node_count)
    start_index = 0
    
    print(f"[任務] 開始破解! ID: {task_id}, 節點數: {node_count}")
    
    for sid in available_nodes:
        end_index = min(start_index + chunk_size, total_combinations)
        
        # 更新節點狀態
        connected_nodes[sid]['status'] = 'WORKING'
        
        # 發送指令給 Client
        payload = {
            "task_id": task_id,
            "target_hash": target_hash,
            "range_start": start_index,
            "range_end": end_index,
            "prefix_length": pwd_length
        }
        socketio.emit('assign_task', payload, to=sid)
        
        print(f"   -> 分配給 {connected_nodes[sid]['name']}: {start_index} ~ {end_index}")
        start_index = end_index
        
    broadcast_node_list()

# --- 事件 4: 接收結果 (Client -> Server) ---
@socketio.on('submit_result')
def handle_result(data):
    # data 預期: {"task_id": "...", "found": True, "result": "123456"}
    if current_task['status'] != "RUNNING":
        return

    node_name = connected_nodes.get(request.sid, {}).get('name', 'Unknown')
    # 如果這個節點找到密碼（成功情況）
    if data.get('found'):
        secret = data.get('result')
        print(f"[成功] {node_name} 找到了密碼: {secret}")
        
        current_task['status'] = "COMPLETED"
        current_task['winner'] = node_name
        current_task['secret_found'] = secret
        
        # ✅ 統計完成數：一樣算已回報
        current_task['finished_nodes'] += 1
        total_nodes = len(connected_nodes)
        socketio.emit('task_progress', {
            "finished": total_nodes,   # 直接視為全部完成
            "total": total_nodes,
            "status": current_task['status'],
        })

        # 1. 廣播停止指令
        socketio.emit('stop_task', {
            "task_id": current_task['id'],
            "winner": node_name
        })
        
        # 2. 廣播任務完成 (給 Dashboard)
        socketio.emit('task_completed', {
            "success": True,
            "secret": secret,
            "winner": node_name,
            "task_id": current_task['id'],
        })
        
        # 重置狀態
        for sid in connected_nodes:
            connected_nodes[sid]['status'] = 'IDLE'
        broadcast_node_list()
        
    else:
        # 這個節點範圍掃完但沒找到
        print(f"[進度] {node_name} 搜尋完畢，但沒找到")
        connected_nodes[request.sid]['status'] = 'IDLE'
        broadcast_node_list()


        # ✅ 統計「已回報」的節點數
        current_task['finished_nodes'] += 1
        # ✅ 這裡新增 task_progress（沒找到也算進度）
        total_nodes = len(connected_nodes)
        socketio.emit('task_progress', {
            "finished": current_task['finished_nodes'],
            "total": total_nodes,
            "status": current_task['status'],
        })

        # 如果所有節點都回報完了，且沒有贏家，就宣告失敗結束
        if current_task['finished_nodes'] == len(connected_nodes) and current_task['winner'] is None:
            print("[任務結束] 所有節點都搜尋完畢，仍然沒有人找到密碼。")

            current_task['status'] = "COMPLETED"

            socketio.emit('task_completed', {
                "success": False,
                "secret": "",
                "winner": None,
                "task_id": current_task['id'],
            })


if __name__ == '__main__':
    # host='0.0.0.0' 讓同網域的其他電腦連得進來
    print("Server 啟動中... 請按 Ctrl+C 停止")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)