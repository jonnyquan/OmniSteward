if "%ENV_FILE%"=="" (
    set OPENAI_API_BASE=your_api_base
    set OPENAI_API_KEY=your_api_key
    set SILICON_FLOW_API_KEY=your_api_key
    set BEMFA_UID=your_bemfa_uid
    set BEMFA_TOPIC=your_bemfa_topic
    set LOCATION=your_location
    set LLM_MODEL=Qwen2.5-7B-Instruct
    echo 直接用本文件进行环境变量设置, 本文件路径为: %~dp0env.cmd
) else (
    echo 已指定另外的环境变量文件: %ENV_FILE%
    call %ENV_FILE%
)
