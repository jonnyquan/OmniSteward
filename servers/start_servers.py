import subprocess


if __name__ == "__main__":
    servers = [
        'servers.asr',
        'servers.vad_rpc'
    ]

    subprocesses = []
    for server in servers:
        subprocesses.append(subprocess.Popen(['python', '-m', server]))

    try:
        while True:
            for process in subprocesses:
                process.wait()
    except KeyboardInterrupt:
        print("\n正在终止所有子进程...")
        for process in subprocesses:
            process.kill()  # 强制终止子进程
        
        # 等待所有进程完全终止
        for process in subprocesses:
            process.wait()
        print("所有子进程已终止")