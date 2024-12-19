from .backend import *

# 仅在step系列模型中支持
model = 'step-1-8k'

# 使用step_web_search工具   
tool_names.append('step_web_search')
# 不使用ask_kimi工具，因为有点慢
if 'ask_kimi' in tool_names:
    tool_names.remove('ask_kimi')
