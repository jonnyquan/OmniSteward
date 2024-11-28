@echo off
@REM 使用call命令来执行env.cmd文件
call %~dp0env.cmd

python -m core.cli --config configs/cli.py