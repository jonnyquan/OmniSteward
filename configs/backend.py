import os
import uuid
from .default import get_default_system_prompt_func, get_model_list

# backend config
frontend_url = "http://localhost:3000" # 前端服务器地址
port = 8000
access_token = str(uuid.uuid4()) # 用于验证用户身份，确保不会被外部调用

# steward config
openai_api_base = os.environ["OPENAI_API_BASE"] # 查看docs/PLATFORM.md获取更多信息
openai_api_key = os.environ["OPENAI_API_KEY"]

model_list = get_model_list(openai_api_base) # 获取模型列表
model = os.getenv("LLM_MODEL", "Qwen2.5-7B-Instruct") # 选用的大语言模型，这只是一个默认值，实际要看前端传回来的 

assert model in [m["id"] for m in model_list], f"model {model} not found in {model_list}"

# tool config
silicon_flow_api_key = os.environ["SILICON_FLOW_API_KEY"] # 用于discover_program(文本重排序), 和语音转写

# used in bemfa_control
# bemfa_uid = os.environ["BEMFA_UID"]
# bemfa_topic = os.environ["BEMFA_TOPIC"]

# used in kimi_profile
kimi_profile_path = os.getenv("KIMI_PROFILE_PATH", None)

system_prompt_func = get_default_system_prompt_func(os.environ["LOCATION"])

# used in omni_ha(homeassistant)
ha_url = os.environ["HA_URL"]
ha_token = os.environ["HA_TOKEN"]

tool_names = [
    'discover_program',
    'launch_program',
    # 'bemfa_control',
    'write_file',
    'read_file',
    'list_dir',
    'zip_dir',
    'cmd',
    'ask_kimi',
    'browser',
    'enhanced_everything',
    'timer',
    'prepare_download',
    'omni_ha.HomeAssistant', # https://github.com/OmniSteward/omni-ha
    # 'steward_utils.tools.example.ListAllTools' # 未导入的工具，可以直接写全路径，会自动导入
    # 'step_web_search', # 仅在step系列模型中支持
]