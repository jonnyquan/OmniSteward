from gevent import monkey
monkey.patch_all()
import socket
print(socket.gethostbyname('localhost'))
from flask import Flask, request, jsonify, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
from core.steward import OmniSteward, HistoryManager, StewardOutput, StewardOutputType
from core.task import ScheduledTaskRunner
from core.file import FileManager
from utils.asr_client import OnlineASR
from configs import load_and_merge_config, get_updated_config, default_config
from tools import ToolManager, RemoteToolManager, OmniToolResult
import requests
import time
import argparse
import os
from flask_socketio import SocketIO, emit

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, default='configs/backend.py')
parser.add_argument('--debug', action='store_true', default=False)
args = parser.parse_args()

config = load_and_merge_config(args.config, default_config)
print(f"access_token: {config.access_token}")


tmp_config_path = '.local/tmp_config.json'
os.makedirs(os.path.dirname(tmp_config_path), exist_ok=True)
with open(tmp_config_path, 'w', encoding='utf-8') as f:
    f.write(config.dump2json())

transcribe = OnlineASR(api_key=config.silicon_flow_api_key) # 转写器
tool_manager = ToolManager(config) # 工具管理器
remote_tool_manager = RemoteToolManager(f'http://localhost:{config.port}/api/tool', config.access_token) # 远程工具管理器
history_manager = HistoryManager() # 管理对话历史记录
task_runner = ScheduledTaskRunner(remote_tool_manager) # 定时任务调度器
task_runner.start()
file_manager = FileManager()


def verify_access_token(data):
    access_token = data.get('access_token', '')
    return access_token == config.access_token

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent') # 不要用eventlet, 那个玩意儿会导致dns解析出问题

# 转发到前端服务器的函数
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    # 排除 /api 开头的请求
    if path.startswith('api/'):
        return "Not Found", 404
        
    target_url = f'{config.frontend_url}/{path}'
    
    # 转发请求到目标服务器
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers={key: value for key, value in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    
    # 返回响应
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for name, value in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    
    return resp.content, resp.status_code, headers



@app.route('/api/transcribe', methods=['POST'])
def transcribe_api():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有上传音频文件'}), 400
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        # 直接从内存中读取文件内容
        audio_content = audio_file.read()
        # 转发请求到转写服务器
        time_start = time.time()
        print(f"开始转写")
        text = transcribe(audio_content)
        print(f"转写时间: {time.time() - time_start:.2f}s")
        return jsonify({
            'success': True,
            'text': text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tool', methods=['POST'])
def tool_api():
    data = request.json
    action_type = data.get('action_type', '')
    if not verify_access_token(data):
        return jsonify({'error': '无效的access_token'}), 401
    if action_type == 'call':
        tool_name = data.get('tool_name', '')
        tool_params = data.get('tool_params', {})
        tool_res = tool_manager.call(tool_name, tool_params)
        if isinstance(tool_res, OmniToolResult):
            return jsonify(tool_res.to_dict())
        else:
            return jsonify(tool_res)
    elif action_type == 'list':
        return jsonify(tool_manager.tool_names)
    elif action_type == 'json':
        return jsonify(tool_manager.json())
    else:
        return jsonify({'error': '无效的action_type'}), 400


@app.route('/api/schedule_task', methods=['POST'])
def schedule_task_api():
    data = request.json
    if not verify_access_token(data):
        return jsonify({'error': '无效的access_token'}), 401
    task_runner.add_scheduled_task(data.get('schedule_time', ''), data.get('tool_name', ''), data.get('tool_params', {}))
    return jsonify({'success': True})

@app.route('/api/prepare_download', methods=['POST'])
def prepare_download_api():
    data = request.json
    if not verify_access_token(data):
        return jsonify({'error': '无效的access_token'}), 401
    try:
        file_id = file_manager.add(data.get('file', ''))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'file_id': file_id})

@app.route('/api/download', methods=['GET'])
def download_api():
    file_id = request.args.get('file_id', '')

    if not verify_access_token(request.args):
        return jsonify({'error': '无效的access_token'}), 401
    file_path = file_manager.get(file_id)
    print(f"DEBUG - 下载文件: {file_path}, file_id: {file_id}")
    if file_path is None:
        return jsonify({'error': '文件不存在'}), 404
    return send_file(file_path, as_attachment=True)


@app.route('/api/models', methods=['GET'])
def models_api():
    return jsonify(config.model_list)

def chat(query, model, history_id):
    namespace = '/'
    print(f"DEBUG - 选择的模型: {model}")
    tmp_config = get_updated_config(config, model=model)
    steward = OmniSteward(tmp_config, tool_manager)
    if history_id is not None:
        history = history_manager.get(history_id)
        if history is None:
            socketio.emit('error', {'error': f"历史记录不存在: {history_id}"}, namespace=namespace)
            return
    else:
        history = []
    try:
        for output in steward.chat(query, history):
            assert isinstance(output, StewardOutput)
            if output.type == StewardOutputType.HISTORY:
                new_history_id = f"{time.time():.6f}"
                history_manager.add(new_history_id, output.data)
                message = {"type": "history", "history_id": new_history_id}
            elif output.type == StewardOutputType.ACTION:
                print(f"DEBUG - 创建动作: {output.data}")
                message = {"type": "action", "action": output.data}
            elif output.type == StewardOutputType.CONTENT:
                message = {"type": "content", "data": output.data}
            else:
                message = {"type": str(output.type), "data": str(output.data)}
            timestamp_in_ms = int(time.time() * 1000)
            kwargs = {"send_time": timestamp_in_ms}
            message.update(kwargs)
            socketio.emit('message', message, namespace=namespace)
            socketio.sleep(0)
    except Exception as e:
        socketio.emit('error', {'error': str(e)}, namespace=namespace)
        raise e


@socketio.on('chat')
def handle_chat(data):
    query = data.get('query', '')
    model = data.get('model', config.model)
    history_id = data.get('history_id', None)
    
    socketio.start_background_task(chat, query, model, history_id)


def open_browser(url, delay=0):
    import threading
    def open_browser_thread():
        time.sleep(delay)
        os.system(f"start {url}")
    threading.Thread(target=open_browser_thread).start()


if __name__ == '__main__':
    URL = f"http://localhost:{config.port}"
    open_browser(URL, delay=5)
    print(f"INFO - 服务已运行在{config.port}端口，请访问 {URL}")
    socketio.run(app, host='0.0.0.0', port=config.port, debug=args.debug)
