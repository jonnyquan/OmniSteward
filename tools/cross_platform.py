# 跨平台的工具
# 这里只写跨平台的工具，不写windows或linux特有的工具，实现时请注意不要依赖windows或linux特有的模块或者命令
import os
import subprocess
import requests
import bs4
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from utils.bemfa import BemfaTCPClient
from steward_utils import OmniTool, OmniToolResult, Config
import zipfile


class BemfaControl(OmniTool):
    name = "bemfa_control"
    description = "通过Bemfa平台控制智能家居设备, 但只有一个设备，叫鱼缸灯"
    parameters = {
        "command": {
            "type": "string",
            "description": "cycle:时间, 表示每隔时间切换开关状态,如 cycle:5s, 表示每隔5秒切换一次开关状态, cycle:clear, 表示清除循环，on, 表示打开, off, 表示关闭, update, 表示固件升级",
        }
    }
    config_items = [
        {'key': 'bemfa_uid', 'default': None, 'required': True},
        {'key': 'bemfa_topic', 'default': None, 'required': True},
    ]
    def __init__(self, config: Config):
        super().__init__(config)
        self.last_call_time = 0
        self.min_interval = 2  # 最小调用间隔(秒)

    def __call__(self, command: str):
        """
        通过Bemfa平台控制智能家居
        """
        current_time = time.time()
        while current_time - self.last_call_time < self.min_interval:
            time.sleep(0.1) # 不能太频繁地发消息，不然会丢消息
            current_time = time.time()
        self.last_call_time = current_time
        client = BemfaTCPClient(self.bemfa_uid, self.bemfa_topic)
        if client.send_message(command) == None:
            return "执行失败"
        return "执行成功"


# 这个目前不能用
class BaiduWebSearch(OmniTool):
    name = "baidu_web_search"
    description = "使用百度搜索引擎搜索信息并总结"
    parameters = {
        "query": {
            "type": "string",
            "description": "搜索关键词",
        }
    }
    
    def __call__(self, query: str):
        """使用百度搜索引擎搜索信息并总结
        
        Args:
            query: 搜索关键词
                
        Returns:
            对搜索结果的总结
        """
        client = OpenAI(
                base_url = 'http://localhost:11434/v1',
                api_key='ollama', # required, but unused
        )
        llm_model = 'qwen2.5:7b'
        search_url = f'https://www.baidu.com/s?wd={query}'
        # Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'
        response = requests.get(search_url, headers={'User-Agent': user_agent})
        if response.status_code != 200:
            return f'搜索失败，状态码:{response.status_code}'
        with open('search_result.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"搜索 {query} 成功，开始总结")
        # format response.text to html
        content = response.text
        max_completion_tokens = 500
        soup = bs4.BeautifulSoup(content, 'html.parser')
        # 去掉空行
        clean_text = '\n'.join([line for line in soup.text.splitlines() if line.strip()])
        system_prompt = f'请你总结下面的搜索结果 提取其中的关键信息：\n'
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_text}
            ],
            max_completion_tokens=max_completion_tokens,
        )
        print(f"总结 {query} 成功")
        return response.choices[0].message.content

class StepWebSearch(OmniTool):
    # https://platform.stepfun.com/docs/guide/web_search
    name = "step_web_search"
    description = "使用stepfun平台进行网络搜索"

    def json(self): # 覆盖原本的json方法，因为这是一个特殊工具
        return {
            "type": "web_search",# 固定值
            "function": {
                "description": "这个web_search用来搜索互联网的信息"# 描述什么样的信息需要大模型进行搜索。
            }
        }


class WriteFileTool(OmniTool):
    name = "write_file"
    description = "写入文件内容"
    parameters = {
        "file": {
            "type": "string",
            "description": "文件路径",
        },
        "content": {
            "type": "string",
            "description": "文件内容",
        }
    }
    
    def __call__(self, file: str, content: str):
        """写入文件内容
        
        Args:
            file: 文件路径
            content: 文件内容
            
        Returns:
            执行状态信息
        """
        try:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            return "写入成功"
        except Exception as e:
            return f"写入失败: {str(e)}"


class ReadFileTool(OmniTool):
    name = "read_file"
    description = "读取文件内容"
    parameters = {
        "file": {
            "type": "string",
            "description": "文件路径",
        }
    }
    # pip install python-docx

    def read_word(self, file: str):
        from docx import Document
        doc = Document(file)  # 读取word文档（docx格式，目前不支持doc格式word）
        return [
            p.text for p in doc.paragraphs
        ]
    

    def read_raw(self, file: str):
        with open(file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def __call__(self, file: str):
        try:
            if file.endswith('.docx'):
                return self.read_word(file)
            else:
                return self.read_raw(file)
        except Exception as e:
            return f"读取失败: {str(e)}"

class CMDTool(OmniTool):
    name = "cmd"
    description = "windows command prompt，能够完成对计算机的操控，一些git命令也可以使用它, 也可以通过它来执行命令以关闭某些程序"
    parameters = {
        "cmd": {
            "type": "string",
            "description": "要执行的命令行命令",
        }
    }
    
    def __call__(self, cmd: str):
        """执行命令行命令
        
        Args:
            cmd: 要执行的命令行命令
            
        Returns:
            命令行执行结果
        """
        confirm = input(f"你确定要执行命令吗？{cmd} (y/n)")
        if confirm != 'y':
            return "命令已取消"
        
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            return f'执行失败: {result.stderr}'
        return result.stdout


def has_finished(driver):
    # 查找所有button, 如果有一个button的文本是"停止输出"，则返回True
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    for button in buttons:
        if button.text.strip() == "停止输出":
            return False # 说明还在输出
    return True


def wait_until_finished(driver, timeout=120):
    print('等待KIMI AI助手回答结束...', end='')
    start_time = time.time()
    while not has_finished(driver):
        time.sleep(0.5)
        print('.', end='')
        if time.time() - start_time > timeout:
            raise TimeoutError(f"等待完成超时，超时时间: {timeout}秒")
    print('KIMI AI助手回答结束')


class AskKimi(OmniTool):
    name = "ask_kimi"
    description = "使用强大的Kimi AI助手进行在线检索和信息查询，他可以回答各种问题，并提供详细的解释, 有不懂的问题都可以问他，只要是在线可以查询到的信息都可以问他"
    parameters = {
        "query": {
            "type": "string",
            "description": "查询内容",
        }
    }
    config_items = [
        {'key': 'kimi_profile_path', 'default': './chrome_data', 'required': False}
    ]
    def __init__(self, config: Config):
        super().__init__(config)
        self.profile_path = os.path.abspath(self.kimi_profile_path).replace('\\', '/')
        self.create_driver()

    def create_driver(self, force=False):
        if getattr(self, 'driver', None) is not None and not force:
            return
        if getattr(self, 'driver', None) is not None and force:
            del self.driver
        chrome_options = webdriver.ChromeOptions()
        
        chrome_options.add_argument(f"--user-data-dir={self.profile_path}")
        chrome_options.add_argument("--remote-debugging-pipe")
        chrome_options.add_argument('--no-sandbox')  # fix:DevToolsActivePort file doesn't exist
        chrome_options.add_argument('--disable-gpu')  # fix:DevToolsActivePort file doesn't exist
        chrome_options.add_argument('--disable-dev-shm-usage')  # fix:DevToolsActivePort file doesn't exist
        chrome_options.add_argument('--remote-debugging-port=9222')  # fix:DevToolsActivePort file doesn't
        # 禁用日志
        chrome_options.add_argument('--log-level=3')  # 只显示致命错误
        chrome_options.add_argument('--silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用日志

        self.driver = webdriver.Chrome(options=chrome_options)

    def search(self, query: str):
        """使用Kimi AI助手查询信息
        
        Args:
            query: 查询内容
            
        Returns:
            查询结果
        """
        try:
            self.create_driver()
            print(f"开始查询: {query}")
            url = 'https://kimi.moonshot.cn/'
            self.driver.get(url)
            self.driver.implicitly_wait(10)
            time.sleep(1)
            # class =myAgentToolIconNew___DBZrW
            self.driver.find_element(By.CLASS_NAME, 'myAgentToolIconNew___DBZrW').click()
            time.sleep(1)
            self.driver.find_element(By.CLASS_NAME, 'editorContentEditable___FZJd9').send_keys(query)
            time.sleep(1)
            # <button class="MuiButtonBase-root MuiIconButton-root MuiIconButton-sizeMedium css-1uviwf" tabindex="0" type="button" data-testid="msh-chatinput-send-button" id="send-button"><span role="img" class="anticon MuiBox-root css-0"><svg width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false" class=""><use xlink:href="#mshd-fasong"></use></svg></span><span class="MuiTouchRipple-root css-w0pj6f"></span></button>
            send_button = self.driver.find_element(By.ID, 'send-button')
            send_button.click()
            time.sleep(3)
            wait_until_finished(self.driver)
            all_messages = self.driver.find_elements(By.CLASS_NAME, 'pop-content')

            for message in all_messages[2:]:
                # html代码
                html = message.get_attribute('innerHTML')

            # <p class="last-node">根据最新的搜索结果，截至2024年11月22日，全球人口数量约为82.39亿<span class="docQuote___YIW6w" data-testid="msh-ref-entrance"><span role="img" class="anticon MuiBox-root css-0"><svg width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false" class=""><use xlink:href="#mshd-seg-quote"></use></svg></span></span>。</p>
            # 提取其中的文本
            # div id="chat-markdown-csvv1gi6k6fmu8bfa72g-0-1" id starts with chat-markdown-
            soup = bs4.BeautifulSoup(html, 'html.parser')
            div = soup.find('div', id=lambda x: x and x.startswith('chat-markdown-'))
            if div:
                simple_text = div.text.strip()
                links = [a for a in div.find_all('a')]
                formatted_links = {
                    link.text.strip(): link.get('href') for link in links
                }
                return {
                    "text": simple_text,
                    "links": formatted_links,
                }
            else:
                return "没有找到查询结果"
        except Exception as e:
            print(f"查询失败: {e}")
            return None
        
    
    def __call__(self, query: str):
        for _ in range(3):
            result = self.search(query)
            if result:
                return result
            else:
                print("查询失败，重新创建浏览器")
                self.create_driver(force=True)
        return "查询失败"

class ListDir(OmniTool):
    name = "list_dir"
    description = "列出文件夹内容"
    parameters = {
        "dir": {
            "type": "string",
            "description": "文件夹路径",
        }
    }
    
    def __call__(self, dir: str):
        return os.listdir(dir)

class ZipDir(OmniTool):
    name = "zip_dir"
    description = "压缩文件夹"
    parameters = {
        "folder": {
            "type": "string",
            "description": "文件夹路径",
        },
        "zip_file": {
            "type": "string",
            "description": "压缩文件路径",
        }
    }
    
    def __call__(self, folder: str, zip_file: str):
        zip_file = os.path.abspath(zip_file).replace('\\', '/')
        folder = os.path.abspath(folder).replace('\\', '/')
        if not os.path.exists(folder):
            return f"文件夹不存在: {folder}"
        # 使用python的zipfile模块来压缩文件夹
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder))
        return "压缩成功"

class PrepareDownload(OmniTool):
    name = "prepare_download"
    description = "提供文件供用户下载，请注意，这个只能下载文件，如果需要下载文件夹，请先压缩文件夹"
    parameters = {
        "file": {
            "type": "string",
            "description": "文件路径",
        }
    }
    config_items = [
        {'key': 'port', 'default': 8000, 'required': True},
        {'key': 'access_token', 'default': None, 'required': True},
    ]
    def __init__(self, config: Config):
        super().__init__(config)
        self.prepare_file_url = f'http://localhost:{self.port}/api/prepare_download'
        self.download_url = f'/api/download' # 因为不知道是不是从外网访问，因此不加host
        self.kwargs = {'access_token': self.access_token}
    
    def __call__(self, file: str):
        """提供下载文件
        返回一个file_id，供用户下载
        Args:
            file: 文件路径
            
        Returns:
            下载结果
        """
        file = os.path.abspath(file).replace('\\', '/')
        # ask server to prepare file
        response = requests.post(self.prepare_file_url, json={'file': file, **self.kwargs})
        if response.status_code != 200:
            return OmniToolResult(status='error', content=f"准备文件失败: {response.text}")
        file_id = response.json()['file_id']
        return OmniToolResult(status='success', content=f"准备文件成功，现在可以在网页上点击下载", action={
            'type': 'create_download',
            'url': f'/api/download?file_id={file_id}&access_token={self.access_token}',
            'file_name': os.path.basename(file),
        })