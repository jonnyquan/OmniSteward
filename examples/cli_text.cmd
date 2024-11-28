@echo off
@REM 使用call命令来执行env.cmd文件
call %~dp0env.cmd

python -m core.cli --query "打开网易云音乐" --config configs/cli.py