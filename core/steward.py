import json
from openai import OpenAI
import time
from tools import ToolManager, Config, OmniToolResult, JsonFixer
from core.task import RemoteToolManager

class HistoryManager:
    '''
    管理历史记录, 并自动清理过期的历史记录
    '''
    def __init__(self, max_age_hours: float = 24.0):
        self.history_db = {}
        self.last_access = {}  # 记录每个历史记录的最后访问时间
        self.max_age = max_age_hours * 3600  # 转换为秒
        
    def add(self, history_id: str, history: list[dict]):
        self.history_db[history_id] = history
        self.last_access[history_id] = time.time()
        self._cleanup()  # 添加新记录时清理旧记录

    def has(self, history_id: str):
        return history_id in self.history_db

    def get(self, history_id: str):
        if history_id in self.history_db:
            self.last_access[history_id] = time.time()  # 更新访问时间
            return self.history_db[history_id]
        else:
            return None
    
    def _cleanup(self):
        """清理超过最大存活时间的历史记录"""
        current_time = time.time()
        expired_ids = [
            history_id for history_id, last_access in self.last_access.items()
            if current_time - last_access > self.max_age
        ]
        for history_id in expired_ids:
            del self.history_db[history_id]
            del self.last_access[history_id]

output_type2prefix = {
    "history": "【历史】",
    "content": "【AI】",
    "debug": "【调试信息】",
    "error": "【错误】",
    "action": "【动作】",
}

class StewardOutput:
    def __init__(self, type: str, data: any):
        self.type = type
        self.data = data

    def __str__(self):
        return f"{output_type2prefix[self.type]}: {self.data}"


class OmniSteward:
    '''
    OmniSteward is a powerful AI agent that can use tools to solve problems.
    '''
    def __init__(self, config: Config, tool_manager: ToolManager|RemoteToolManager):
        self.config = config
        self.system_prompt = config.system_prompt_func() # 实时生成系统提示词，因为环境信息会变化
        self.model_name = config.model
        self.max_rounds = config.max_rounds
        self.openai_api_base = config.openai_api_base
        self.openai_api_key = config.openai_api_key
        self.json_fixer = JsonFixer(config) # 修复JSON格式错误
        
        self.client = OpenAI(
            base_url=self.openai_api_base,
            api_key=self.openai_api_key
        )
        self.tool_manager = tool_manager
        self.tools_json = self.tool_manager.json()


    def chat(self, query: str, history: list[dict] = []): 
        if history == []:
            history = [
                {"role": "system", "content": self.system_prompt},
            ]
        messages = [
            *history,
            {"role": "user",  "content": query},
        ]

        for i in range(self.max_rounds):
            start = time.time()
            kwargs = {}
            if "step-" in self.model_name: 
                kwargs['tool_choice'] = "auto"
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.tools_json,
                tool_choice="auto",
                temperature=self.config.get("temperature", 0.1),
                top_p=self.config.get("top_p", 0.95),
                max_tokens=self.config.get("max_tokens", 512),
                extra_body={
                "repetition_penalty": 1.05,
                }
            )
            print(response)
            end = time.time()
            yield StewardOutput("debug", f"耗时: {end - start:.2f}秒")

            # 处理响应
            current_message = response.choices[0].message.model_dump()
            messages.append(current_message)

            tool_calls = current_message.get("tool_calls", None)
            content = current_message.get("content", "")

            if content != "":
                yield StewardOutput("content", content)
            else:
                yield StewardOutput("debug", current_message)

            # 处理工具调用
            if tool_calls is None:  # 没有工具调用
                yield StewardOutput("history", messages)
                break

            for tool_call in tool_calls:
                tool_type = tool_call.get("type")
                if tool_type == "web_search": # 仅在step系列模型中支持step_web_search工具
                    yield StewardOutput("debug", f"step_web_search is called")
                    continue

                fn_call = tool_call.get("function")
                if fn_call:
                    fn_name = fn_call["name"]
                    fn_args = self.json_fixer.get_fn_args(fn_call)
                    if fn_args is None:
                        yield StewardOutput("error", f"工具调用参数解析失败: {fn_call}")
                        break
                    yield StewardOutput("debug", f"正在调用工具: {fn_name}, 参数: {fn_args}")

                    tool_start = time.time()
                    try:
                        fn_res = self.tool_manager.call(fn_name, fn_args)
                        print(f"DEBUG - 工具调用结果: {fn_res}")
                    except Exception as e:
                        yield StewardOutput("error", f"工具调用失败: {e}")
                        break
                    if isinstance(fn_res, OmniToolResult) and fn_res.action is not None:
                        yield StewardOutput("action", fn_res.action) # 创建一个新动作
                        fn_res = fn_res.content

                    tool_time = time.time() - tool_start
                    
                    fn_res = json.dumps(fn_res, ensure_ascii=False)
                    tool_message = {
                        "role": "tool",
                        "content": fn_res,
                        "tool_call_id": tool_call["id"],
                    }
                    messages.append(tool_message)
                    yield StewardOutput("debug", {"fn_name": fn_name, "fn_args": fn_args, "fn_res": fn_res, "time": f"{tool_time:.2f}秒"})



def get_generate(steward: OmniSteward, query: str, history: list[dict]):
    def generate():
        for output in steward.chat(query, history):
            output_type = output.type
            if output_type == "history":
                yield output
                break  # 继续下一轮对话
            elif output_type == "action":
                yield output
            elif output_type == "error":
                yield str(output)
                break
            else:
                yield str(output)
    return generate