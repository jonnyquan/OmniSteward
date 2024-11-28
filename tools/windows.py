from collections import OrderedDict
from utils.reranker import Reranker
import os
import subprocess
import time
from .base import Tool, Config

class DiscoverProgram(Tool):
    name = "discover_program"
    description = "根据用户描述，发现用户需要的程序, 供launch_program使用, 如果你认为用户需要打开电脑程序，则调用它来发现程序,关键词尽量用完整的程序名，快捷方式的名称可能和程序名不一致，你应该选择最可能的快捷方式"
    parameters = {
        "keyword": {
            "type": "string",
            "description": "用户描述的关键词",
        }
    }
    support_os = ["windows"]
    config_items = [
        {'key': 'silicon_flow_api_key', 'default': None, 'required': True}
    ]

    def __init__(self, config: Config):
        super().__init__(config)
        self.reranker = Reranker(api_key=self.silicon_flow_api_key)
        self.min_relevance_score = 0.6
    
    def __call__(self, keyword: str):
        """根据用户描述，发现用户需要的程序
        
        Args:
            keyword: 用户描述的关键词
            
        Returns:
        程序快捷方式列表
        """
        program_list = []
        keyword = keyword.lower()
        desktop_root = os.path.join(os.path.expanduser('~'), 'Desktop')
        start_menu_root = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'
        most_roots = [
            start_menu_root,
            desktop_root,
        ]
        exts = set(['.lnk', '.exe', '.cmd', '.bat'])

        print(f"正在搜索 {keyword} 相关的程序")
        name2path = OrderedDict()
        for most_root in most_roots:
            for root, dirs, files in os.walk(most_root):
                for file_name in files:
                    ext = os.path.splitext(file_name)[1]
                    if ext in exts: # 只搜索常见的可执行文件
                        abs_path = os.path.join(root, file_name)
                        file_lower = file_name.lower()
                        file_lower = os.path.splitext(file_lower)[0]
                        name2path[file_lower] = abs_path.replace('\\', '/')
        names = sorted(name2path.keys())
        rerank_results = self.reranker(keyword, names, top_n=20)['results']
        for result in rerank_results:
            if result['relevance_score'] < self.min_relevance_score:
                continue
            name = names[result['index']]
            program_list.append(name2path[name])
        return program_list



class LaunchProgram(Tool):
    name = "launch_program"
    description = "启动程序，不要自己猜测程序路径，必须先调用discover_program以获取程序路径"
    parameters = {
        "program": {
            "type": "string",
            "description": "程序路径, 必须从discover_program中获取，不要自己猜测",
        }
    }
    support_os = ["windows"]
    
    def __call__(self, program: str):
        """启动程序
        
        Args:
            program: 程序路径, 需要从discover_program中获取
            
        Returns:
            启动状态信息
        """    
        if program.endswith('.lnk'):
            command = f'"{program}"'
        else:
            command = f'start "" "{program}"'
        
        # 使用Popen代替run，这样不会阻塞等待程序退出
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        if p.poll() is None:
            return '启动成功'
        elif p.returncode == 0: # 如果程序已经退出，且成功退出
            return '启动成功'
        else:
            # 获取 stderr
            stderr = p.stderr.read().decode('gbk')
            return f'启动失败: {stderr}'
        
        



class BrowserTool(Tool):
    name = "browser"
    description = "使用浏览器打开指定网址"
    parameters = {
        "url": {
            "type": "string", 
            "description": "要打开的网址",
        }
    }
    support_os = ["windows"]

    def __call__(self, url: str):
        """使用默认浏览器打开指定网址
        
        Args:
            url: 要打开的网址
            
        Returns:
            执行状态信息
        """
        try:
            os.system(f'start {url}')
            return "网页打开成功"
        except Exception as e:
            return f"打开失败: {str(e)}"


if __name__ == "__main__":
    print(DiscoverProgram()("beyond compare"))
