import importlib
from types import ModuleType, FunctionType, SimpleNamespace
from .default import default_config


class Config(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


def load_and_merge_config(config_path, default_config=default_config) -> Config:
    config = default_config.copy()
    config_path = config_path.replace("/", ".").replace("\\", ".").replace(".py", "")
    imported_config = importlib.import_module(config_path)
    
    valid_config = {}
    for key, value in imported_config.__dict__.items():
        if key.startswith('_'):
            continue
        # 如果是module或者是class就不要
        if isinstance(value, ModuleType) or isinstance(value, FunctionType) or isinstance(value, type):
            continue
        valid_config[key] = value

    config.update(valid_config)
    return Config(**config)


def get_updated_config(config: Config, **kwargs) -> Config:
    updated_config = vars(config).copy()
    updated_config.update(kwargs)
    return Config(**updated_config)


