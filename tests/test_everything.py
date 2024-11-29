import json
from configs import Config
from tools.everything import EnhancedEverything

if __name__ == "__main__":
    # load access_token from tmp_config.json
    with open('.local/tmp_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    config = Config(**config)
    everything = EnhancedEverything(config)
    print(everything('查找 3D 相关文件'))