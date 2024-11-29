# 可用工具

**注意，本文档正在更新中，请以代码为准**

## 内建工具
- `discover_program`: 查找电脑程序，支持模糊匹配
- `launch_program`: 启动程序
- `mihome_control`: 小爱同学智能家居控制
- `bemfa_control`: 巴法云平台设备控制
- `web_search`: 百度搜索信息查询
- `ask_kimi`: 通过Kimi AI助手查询信息, 首次使用需要在弹出的浏览器登录Kimi，然后关闭浏览器
- `browser`: 打开网页
- `cmd`: 执行命令行命令
- `write_file`: 写入文件
- `prepare_download`: 准备下载文件, 返回文件下载链接

## 指定使用哪些工具

在`config.py`中，`tool_names`列表中指定使用哪些工具。

## 创建自定义工具

步骤1. 定义你的工具类
```python
from tools import Tool

class MyTool(Tool):
    """
    你的工具描述
    """
    name = "my_tool"
    description = "你的工具描述"
    parameters = {
        "param1": {
            "type": "string",
            "description": "参数1描述"
        },
        "param2": {
            "type": "any",
            "description": "参数2描述"
        }
    }

    def __call__(self, param1: str, param2: any):
        # 实现你的工具逻辑
        pass


```
步骤2.
```python
# 在config.py中添加你的工具名到工具列表，工具名可以任意，但不要重复
tool_names.append("my_tool") 
```

只要在config.py中导入MyTool，你甚至可以直接在config.py当中定义MyTool也没问题。
