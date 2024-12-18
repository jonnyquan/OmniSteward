from everytools import EveryTools
from steward_utils import OmniTool, Config
import os
from openai import OpenAI
from .utils import get_fn_args

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



class Everything(OmniTool):
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
    
# https://github.com/elliottzheng/everytools
abstract_everything_description = """
使用everything检索文件, 可能的参数有三个:
1. search_func: 所使用的检索函数
2. keywords: 检索关键词
3. path: 检索路径，注意有些函数可以指定，有些不能

如果你不知道待检索的文件类型, 你可以使用以下函数:
- search(keywords): 检索文件
- search_folder(keywords): 搜索文件夹

如果想检索特定类型的文件, 但是不知道路径，你可以使用以下函数:
- search_audio(keywords): 搜索音频文件
- search_video(keywords): 搜索视频文件
- search_pic(keywords): 搜索图片文件
- search_doc(keywords): 搜索文档文件
- search_exe(keywords): 搜索可执行文件
- search_zip(keywords): 搜索压缩包
- search_ext(keywords): 搜索指定扩展名的文件

如果想在指定文件夹下搜索文件, 你可以使用以下函数:
- search_in_located(self, path, keywords): 在指定文件夹下搜索文件


"""

class InternalEverything(Everything):
    name = 'internal_everything'
    description = abstract_everything_description
    parameters: dict = {
        "search_func": {
            "type": "string",
            "description": "所使用的检索函数",
        },
        "keywords": {
            "type": "string",
            "description": "检索关键词",
        },
        "path": {
            "type": "string",
            "description": "检索路径",
        }
    }
    
    def __call__(self, search_func: str, keywords: str, path: str = None):
        print(f"DEBUG - 调用内部检索函数: {search_func}, 关键词: {keywords}, 路径: {path}")
        if path is not None:
            getattr(self.es, search_func)(keywords=keywords, path=path) # 调用检索函数
        else:
            getattr(self.es, search_func)(keywords=keywords) # 调用检索函数
        result_df = self.es.results()
        files = []
        for index, row in result_df.iterrows():
            name = row['name']
            path = row['path']
            files.append(os.path.join(path, name).replace('\\', '/'))
        return files
        
    


def get_desktop_path():
    return os.path.expanduser('~') + r'\Desktop'

desktop_path = get_desktop_path().replace('\\', '/')
documents_path = os.path.join(os.path.expanduser('~'), 'Documents').replace('\\', '/')
username = os.getlogin()

everything_system_prompt = """
你是一个文件检索专家，你的任务是根据用户的描述，从计算机中检索出最相关的文件或文件夹。
以下是一些可能用到的信息:
用户名: {username}
桌面路径: {desktop_path}
文档路径: {documents_path}

"""
everything_system_prompt = everything_system_prompt.format(username=username, desktop_path=desktop_path, documents_path=documents_path)

class EnhancedEverything(OmniTool):
    '''
    使用自然语言增强检索， 这相当于是一个子Agent, 专门负责检索文件
    '''
    config_items = [
        {'key': 'openai_api_key', 'default': None, 'required': True},
        {'key': 'openai_api_base', 'default': None, 'required': True},
        {'key': 'model', 'default': None, 'required': True},
    ]
    name = 'enhanced_everything'
    description = '用自然语言检索计算机中的文件或文件夹'
    parameters: dict = {
        "query": {
            "type": "string",
            "description": "用自然语言描述你想要搜索的内容",
        }
    }
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.openai_api_base,
        )
        self.internal_everything = InternalEverything(config)

        

    def __call__(self, query):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": everything_system_prompt},
                {"role": "user", "content": query},
            ],
            tools=[self.internal_everything.json()],
        )
        message = response.choices[0].message.model_dump()
        content = message['content']
        print(f"DEBUG - 自然语言增强检索: {message}")
        tool_calls = message['tool_calls']
        if tool_calls is None:
            return '检索失败'
        for tool_call in tool_calls:
            fn_call = tool_call['function']
            fn_name = fn_call['name']
            if fn_name != 'internal_everything':
                return '检索失败'
            fn_args = get_fn_args(fn_call)
            files = self.internal_everything(**fn_args)
            return files
            


        