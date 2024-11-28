import json
from core.task import RemoteToolManager

if __name__ == "__main__":
    # load access_token from tmp_config.json
    with open('tmp_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    access_token = config['access_token']
    payload = {
        "tool_name": "browser",
        "tool_params": {"url": "https://www.baidu.com"},
    }
    url = f'http://localhost:8000/api/tool'
    remote_tool_manager = RemoteToolManager(url, access_token)

    print(remote_tool_manager.tool_names)

    print(remote_tool_manager.json())

    print(remote_tool_manager.call(payload['tool_name'], payload['tool_params']))

    