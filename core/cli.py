from tools.manager import ToolManager
from configs import load_and_merge_config
from .steward import OmniSteward, StewardOutput, get_generate
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--config", type=str, default='configs/local.py')
    parser.add_argument("--max_rounds", type=int, default=10)
    args = parser.parse_args()

    config = load_and_merge_config(args.config)

    tool_manager = ToolManager(config)

    if args.query is None:
        from utils.asr_client import ASR, OnlineASR
        transcribe = OnlineASR(api_key=config.silicon_flow_api_key)
        asr = ASR(transcribe, vad_server_url=config.vad_server_url)
        query = asr.auto_record_and_transcribe(duration=5)
        if query == "":
            print("没有检测到语音")
            exit()
    else:
        query = args.query
    # 白金之星 Star Platinum
    # 快用你无敌的白金之星想想办法吧
    star_platinum = OmniSteward(config, tool_manager)
    history = []
    for i in range(args.max_rounds):
        generate = get_generate(star_platinum, query, history)
        for output in generate():
            if isinstance(output, StewardOutput):
                history = output.data
                break
            else:
                print(output)
        query = input("【用户】：")
        if query == "":
            print("用户选择退出")
            exit(0)