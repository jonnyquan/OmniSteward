import requests
from datetime import datetime, timedelta
import json


if __name__ == "__main__":
    # 加一分钟
    schedule_time = (datetime.now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S") 
    # load access_token from tmp_config.json
    with open('.local/tmp_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    access_token = config['access_token']
    kwargs = {'access_token': access_token}
    payload = {
        "file": r"E:\IOT\NewWorld\assets\logo.png".replace('\\', '/'),
    }
    url = f'http://localhost:8000/api/prepare_download'
    
    # with access_token
    response = requests.post(url, json={
        **payload,
        **kwargs
    })
    print(response.json())

    # download
    file_id = response.json()['file_id']
    url = f'http://localhost:8000/api/download'
    final_url = f'{url}?file_id={file_id}&access_token={access_token}'
    print(final_url)
    
    response = requests.get(final_url)
    print(response.status_code)
    file_name = response.headers['Content-Disposition'].split('filename=')[1]
    with open(file_name, 'wb') as f:
        f.write(response.content)