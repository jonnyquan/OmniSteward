import os
import uuid
from .default import get_system_prompt

# backend config
frontend_url = "http://localhost:3000" # 前端服务器地址
port = 8000
access_token = str(uuid.uuid4()) # 用于验证用户身份，确保不会被外部调用

# steward config
openai_api_base = 'https://api.siliconflow.cn/v1' 
openai_api_key = os.environ["SILICON_FLOW_API_KEY"] # 在这里我也用的是硅基流动的API
model = "Qwen/Qwen2.5-7B-Instruct" # 选用的大语言模型

# tool config
silicon_flow_api_key = os.environ["SILICON_FLOW_API_KEY"] # 用于discover_program(文本重排序), 和语音转写

# used in bemfa_control
bemfa_uid = os.environ["BEMFA_UID"]
bemfa_topic = os.environ["BEMFA_TOPIC"]

# used in kimi_profile
kimi_profile_path = os.environ["KIMI_PROFILE_PATH"]

system_prompt = get_system_prompt(os.environ["LOCATION"])



tool_names = [
    'discover_program',
    'launch_program',
    'mihome_control',
    'bemfa_control',
    'write_file',
    'read_file',
    'cmd',
    'ask_kimi',
    'browser',
    'everything',
    'timer',
    'prepare_download'
]