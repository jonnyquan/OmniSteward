import os
from steward_utils import OmniTool
from datetime import datetime
import subprocess

class Timer(OmniTool):
    name = "timer"
    description = "在指定时间执行CMD命令（注意是CMD命令，不是tool调用）"
    parameters = {
        "time_str": {
            "type": "string",
            "description": "预定时间，格式: YYYY-MM-DD HH:MM:SS"
        },
        "command": {
            "type": "string",
            "description": "CMD命令",
        }
    }
    support_os = ["windows"]

    def __call__(self, time_str: str, command: str):
        schedule_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        print(f"预定时间: {schedule_time}")
        formatted_time = time_str.replace(" ", "_").replace(":", "-")
        task_name = f'world_schedule_{formatted_time}'
        print(f"任务名: {task_name}")
        sd, st = str(schedule_time).split()
        bat_path = create_bat_file(task_name, command)

        sp = subprocess.run(
            f"SchTasks /Create /SC ONCE /TN {task_name} /TR {bat_path} /ST {st} /SD {sd}",
            shell=True,
            capture_output=True,
        )
        if '成功' in sp.stdout.decode('gbk'):
            return '创建计划任务成功'
        else:
            return '创建计划任务失败'


def create_bat_file(task_name: str, command: str):
    """
    创建一个bat文件，在指定时间执行命令，并在执行完毕后删除自身
    """
    bat_path = os.path.abspath(f"bat/{task_name}.bat")
    os.makedirs(os.path.dirname(bat_path), exist_ok=True)
    with open(bat_path, "w") as f:
        f.write(command)
        f.write("\n")
        f.write(f'schtasks /delete /tn "{task_name}" /f\n') # 删除计划任务的命令
        f.write(f"del {bat_path}\n") # 删除自身
    return bat_path


if __name__ == "__main__":
    Timer()("2024-11-27 17:12:00", 'start https://www.baidu.com')