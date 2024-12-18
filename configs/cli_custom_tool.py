from configs.cli import * # 导入configs/cli配置

from steward_utils import OmniTool

class SimplePrintTool(OmniTool): # 继承就会自动注册
    """
    一个简单的打印工具
    """
    name = "simple_print" # 工具名，要添加到tool_names列表中的关键字
    description = "一个简单的打印工具"
    parameters = {
        "text": {
            "type": "string",
            "description": "文本描述"
        }
    }

    def __call__(self, text: str):
        print(text)
        return '打印成功'

tool_names.append('simple_print') # 添加到启用的工具列表中
