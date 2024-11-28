from .base import ToolMetaclass, Config

class ToolManager:
    def __init__(self, config: Config):
        # filter tools by current os
        tool_names = config.tool_names
        self.name2fn = {name: ToolMetaclass.registered_tools[name](config) for name in tool_names if ToolMetaclass.registered_tools[name].is_supported()}
        self.tool_names = list(self.name2fn.keys())
        diff = set(tool_names) - set(self.tool_names)
        if diff:
            print(f"以下工具当前环境不支持: {diff}")

    def get_function(self, name):
        return self.name2fn[name]
    
    def json(self):
        return [
            fn.json() for fn in self.name2fn.values()
        ]
        

    def call(self, name, params):
        return self.name2fn[name](**params)

    @staticmethod
    def get_all_tool_names():
        return list(ToolMetaclass.registered_tools.keys())
    

    @staticmethod
    def get_all_supported_tool_names():
        return [tool for tool in ToolMetaclass.registered_tools.values() if tool.is_supported()]

    

if __name__ == "__main__":
    from configs import load_and_merge_config
    tool_names = [
        'discover_program',
        'launch_program',
        'mihome_control',
        'bemfa_control',
        'write_file',
        'cmd',
        'ask_kimi',
        'browser',
    ]
    config = load_and_merge_config('configs/local.py')
    config.tool_names = tool_names

    tool_manager = ToolManager(config)

    launch_program = tool_manager.get_function_by_name("launch_program")
    # "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\QQMusic - 快捷方式.lnk"
    # "D:\\software\\qq_music\\QQMusic\\QQMusic2.exe"

    lnk_path = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\QQMusic - 快捷方式2.lnk'
    exe_path = r'D:\software\qq_music\QQMusic\QQMusic.exe'

    print(launch_program(exe_path))

