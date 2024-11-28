from everytools import EveryTools
from .base import Tool, Config
import os

# pip install git+https://github.com/elliottzheng/everytools.git

# Everything.exe               27996 Services                   0     10,280 K
# Everything.exe               12364 Console                    1    906,980 K

def is_everything_running():
    import subprocess
    cmd = 'tasklist | find "Everything"'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    output = result.stdout
    if 'Everything.exe' in output and output.count('Everything.exe') > 1: 
        return True
    else:
        return False
    

default_everything_path = r"C:\Program Files\Everything\Everything.exe"

def start_everything(everything_path: str):
    import subprocess
    cmd = f'start "" "{everything_path}"'
    subprocess.run(cmd, shell=True)



class Everything(Tool):
    """
    使用everything搜索
    """
    name = 'everything'
    description = '使用everything快速搜索本地文件'
    parameters: dict = {
        "query": {
            "type": "string",
            "description": "搜索关键词",
        }
    }
    support_os = ["windows"]
    config_items = [
        {'key': 'everything_path', 'default': default_everything_path, 'required': False}
    ]

    def __init__(self, config: Config):
        super().__init__(config)
        if not is_everything_running():
            start_everything(self.everything_path)
        assert is_everything_running(), "everything未运行, 请启动everything"
        self.es = EveryTools()

    def __call__(self, query):
        self.es.search(query)
        result_df = self.es.results()
        files = []
        
        for index, row in result_df.iterrows():
            name = row['name']
            path = row['path']
            files.append(os.path.join(path, name).replace('\\', '/'))
        return files


if __name__ == '__main__':
    # 检查everything是否正在运行
    if not is_everything_running():
        start_everything()
    assert is_everything_running()
    es = Everything()  # 实例化，只需要第一次就行
    print(es('3D人脸重建冠军'))
