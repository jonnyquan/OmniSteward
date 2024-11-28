from flask import Flask, request, jsonify, Response, stream_with_context
from werkzeug.middleware.proxy_fix import ProxyFix
from core.steward import OmniSteward, HistoryManager, get_generate, StewardOutput
from core.task import ScheduledTaskRunner
from utils.asr_client import OnlineASR
from configs import load_and_merge_config, get_updated_config
from tools import ToolManager, RemoteToolManager
import requests
import time
import json
import argparse
import os


parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, default='configs/backend.py')
parser.add_argument('--debug', action='store_true', default=False)
args = parser.parse_args()

config = load_and_merge_config(args.config)

print(f"access_token: {config.access_token}")


tmp_config_path = '.local/tmp_config.json'
os.makedirs(os.path.dirname(tmp_config_path), exist_ok=True)
with open(tmp_config_path, 'w', encoding='utf-8') as f:
    json.dump(config.__dict__, f, indent=4, ensure_ascii=False)

transcribe = OnlineASR(api_key=config.silicon_flow_api_key) # 转写器
tool_manager = ToolManager(config) # 工具管理器
remote_tool_manager = RemoteToolManager(f'http://localhost:{config.port}/api/tool', config.access_token) # 远程工具管理器
history_manager = HistoryManager() # 管理对话历史记录
task_runner = ScheduledTaskRunner(remote_tool_manager) # 定时任务调度器
task_runner.start()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

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




def chat(query, model:str, history_id:str|None = None):
    print(f"DEBUG - 选择的模型: {model}")
    tmp_config = get_updated_config(config, model=model)
    sutando = OmniSteward(tmp_config, remote_tool_manager)
    if history_id is not None:
        history = history_manager.get(history_id)
        if history is None:
            return jsonify({'error': f"历史记录不存在: {history_id}"}), 400
    else:
        history = []
    generate = get_generate(sutando, query, history)
    def gen_wrapper():
        for output in generate():
            if isinstance(output, str):
                output = output.strip() + "<split>"
                yield output
            elif isinstance(output, StewardOutput):
                # 时间戳作为history_id
                timestamp = time.time()
                new_history_id = f"{timestamp:.6f}"
                history_manager.add(new_history_id, output.data)
                yield json.dumps({
                    "history_id": new_history_id,
                })
    return Response(stream_with_context(gen_wrapper()), content_type='application/json')


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

# 音频上传API
@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有上传音频文件'}), 400
            
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        selected_model = request.form.get('model', config.model)
        history_id = request.form.get('history_id', None)
        # 直接从内存中读取文件内容
        audio_content = audio_file.read()
        # 转发请求到转写服务器
        time_start = time.time()
        print(f"开始转写")
        query = transcribe(audio_content)
        print(f"转写时间: {time.time() - time_start:.2f}s")
        return chat(query, model=selected_model, history_id=history_id)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    query = data.get('query', '')
    selected_model = data.get('model', config.model)
    history_id = data.get('history_id', None)
    
    return chat(query, model=selected_model, history_id=history_id)


@app.route('/api/tool', methods=['POST'])
def tool_api():
    data = request.json
    action_type = data.get('action_type', '')
    access_token = data.get('access_token', '')
    if access_token != config.access_token:
        return jsonify({'error': '无效的access_token'}), 401
    if action_type == 'call':
        tool_name = data.get('tool_name', '')
        tool_params = data.get('tool_params', {})
        return jsonify(tool_manager.call(tool_name, tool_params))
    elif action_type == 'list':
        return jsonify(tool_manager.tool_names)
    elif action_type == 'json':
        return jsonify(tool_manager.json())
    else:
        return jsonify({'error': '无效的action_type'}), 400


@app.route('/api/schedule_task', methods=['POST'])
def schedule_task_api():
    data = request.json
    access_token = data.get('access_token', '')
    if access_token != config.access_token:
        return jsonify({'error': '无效的access_token'}), 401
    task_runner.add_scheduled_task(data.get('schedule_time', ''), data.get('tool_name', ''), data.get('tool_params', {}))
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.port, debug=args.debug)
