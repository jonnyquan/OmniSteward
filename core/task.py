import time
import threading
from tools.remote_manager import RemoteToolManager

class Task:
    def __init__(self, tool_name:str, params:dict):
        self.tool_name = tool_name
        self.params = params

    def __call__(self, tool_manager: RemoteToolManager):
        return tool_manager.call(self.tool_name, self.params)


class ScheduledTask(Task):
    def __init__(self, schedule_time:str, tool_name:str, params:dict):
        # convert to timestamp
        self.schedule_time = time.mktime(time.strptime(schedule_time, "%Y-%m-%d %H:%M:%S"))
        super().__init__(tool_name, params)
        self.completed = False
    
    def should_run(self):
        return time.time() >= self.schedule_time and not self.completed
    
    def __call__(self, tool_manager: RemoteToolManager):
        if self.should_run():
            super().__call__(tool_manager)
            self.completed = True
            return True
        return False
    
    def __str__(self):
        return f"ScheduledTask(schedule_time={self.schedule_time}, tool_name={self.tool_name}, params={self.params})"

class ScheduledTaskRunner(threading.Thread):
    def __init__(self, tool_manager: RemoteToolManager):
        super().__init__()
        self.tasks = []
        self.lock = threading.Lock()  # 添加线程锁
        self.running = True
        self.daemon = True  # 设置为守护线程
        self.tool_manager = tool_manager

    def add_scheduled_task(self, schedule_time, tool_name, params):
        task = ScheduledTask(schedule_time, tool_name, params)
        with self.lock:
            self.tasks.append(task)
            print(f"Added scheduled task: {task}")

    def run_task(self, tool_name, params):
        task = Task(tool_name, params)
        return task(self.tool_manager)

    def run(self):
        self.running = True
        while self.running:
            with self.lock:
                # 执行到期的任务并移除已完成的任务
                self.tasks = [task for task in self.tasks if not task(self.tool_manager)]
            time.sleep(1)
    
    def stop(self):
        self.running = False
