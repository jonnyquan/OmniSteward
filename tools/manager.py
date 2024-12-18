from steward_utils import OmniToolMetaclass, Config, get_omni_tool_class

class ToolManager:
    def __init__(self, config: Config):
        # filter tools by current os
        self.name2fn = {}
        for name in config.tool_names:
            updated_tool_name, tool_class = get_omni_tool_class(name)
            if updated_tool_name != name:
                print(f"INFO - 工具名已更新: {name} -> {updated_tool_name}")
            if tool_class.is_supported():
                self.name2fn[updated_tool_name] = tool_class(config)
            else:
                print(f"ERROR - 工具 {name} 当前系统环境不支持")
            
        self.tool_names = list(self.name2fn.keys())

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
        return list(OmniToolMetaclass.registered_tools.keys())
    

    @staticmethod
    def get_all_supported_tool_names():
        return [tool for tool in OmniToolMetaclass.registered_tools.values() if tool.is_supported()]

    

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

