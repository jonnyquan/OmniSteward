import importlib

platforms = ["siliconflow", "stepfun"]

def create_model_list(models):
    return [
        { "id": model, "name": model } for model in models
    ]

api_base2models = {}
for platform in platforms:
    module = importlib.import_module(f"configs.platforms.{platform}")
    api_base = module.api_base
    models = module.models
    api_base2models[api_base] = create_model_list(models)

def get_model_list(api_base):
    api_base = api_base.strip("/")
    return api_base2models[api_base]

