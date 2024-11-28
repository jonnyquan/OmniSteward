import requests
from datetime import datetime, timedelta
import json


if __name__ == "__main__":
    # 加一分钟
    schedule_time = (datetime.now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S") 
    # load access_token from tmp_config.json
    with open('tmp_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    access_token = config['access_token']
    payload = {
        "schedule_time": schedule_time,
        "tool_name": "browser",
        "tool_params": {"url": "https://www.baidu.com"},
    }
    url = f'http://localhost:8000/api/schedule_task'
    
    # with access_token
    response = requests.post(url, json={
        **payload,
        "access_token": access_token    
    })
    print(response.json())
    
    # with no access_token
    response = requests.post(url, json = payload)
    print(response.status_code)
    print(response.json())
    