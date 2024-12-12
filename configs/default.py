import os
from datetime import datetime

default_location = 'your_location'

def get_default_system_prompt_func(location=default_location):
    def system_prompt_func(): # 实时生成系统提示词，因为环境信息会变化
        os_name = os.name
        if os_name == 'nt':
            os_name = 'windows'
        enviroments = [
            f"以下是一些环境信息，在你解决问题时需要充分考虑这些信息：",
            f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"你现在所处的操作系统是：{os_name}",
            f"当前用户是：{os.getlogin()}",
            f"当前目录是：{os.path.abspath(os.getcwd())}",
            f"你的位置是：{location}",
        ]
        enviroment = ",".join(enviroments)
        notices = [
            "以下是一些注意事项，你必须严格遵守：",
            '1. 如果你想打开任何程序，必须先调用discover_program工具。',
            '2. 你的记忆力有限，你其实不知道某些网站的地址，某些文件的路径，某些程序的用法等，不要直接猜测，请先调用工具获取信息。',
            '3. 尽量不要询问我的意见，有疑问你就调用工具来解决。',
        ]
        notices = "\n".join(notices)

        return f"我是一个程序员，而你是一个多功能的机器人管家，可以帮助我管理智能家居或者电脑，你调用工具来获取信息或实现功能以完成我的命令。\n{notices}\n{enviroment}"

    return system_prompt_func

default_config = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "system_prompt_func": get_default_system_prompt_func(default_location),
    "max_rounds": 10,
    "openai_api_base": "https://api.siliconflow.cn/v1",
    "openai_api_key": None,
    "max_tokens": 1024,
}

api_base2models = {
    "https://api.siliconflow.cn/v1": [
        { "id": 'Qwen/Qwen2.5-7B-Instruct', "name": 'Qwen2.5-7B' },
        { "id": 'Qwen/Qwen2.5-14B-Instruct', "name": 'Qwen2.5-14B' },
        { "id": 'Qwen/Qwen2.5-32B-Instruct', "name": 'Qwen2.5-32B' },
        { "id": 'Qwen/Qwen2.5-72B-Instruct', "name": 'Qwen2.5-72B' },
    ],
    "https://api.stepfun.com/v1": [
        { "id": "step-1-8k", "name": "step-1-8k" },
        { "id": "step-1-32k", "name": "step-1-32k" },
        { "id": "step-1v-8k", "name": "step-1v-8k" },
        { "id": "step-1v-32k", "name": "step-1v-32k" },
        { "id": "step-1-128k", "name": "step-1-128k" },
        { "id": "step-1-256k", "name": "step-1-256k" },
        # step2 does not support tool calling yet
    ],
}

def get_model_list(api_base):
    return api_base2models[api_base]

