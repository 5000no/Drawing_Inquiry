@echo off
setlocal
chcp 65001 >nul
title View Blueprint - Start Tunnel

REM 检查 5000 端口是否监听，如果未监听则启动 Web 服务
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R ":5000\>" ^| findstr LISTENING') do set LISTEN_PID=%%p
if not defined LISTEN_PID (
  echo INFO: starting local web server (python run_web.py)
  start "" cmd /c "python run_web.py"
  timeout /t 2 /nobreak >nul
)

REM 如果 cloudflared 已在运行，则跳过
tasklist /FI "IMAGENAME eq cloudflared.exe" | find /I "cloudflared.exe" >nul
if %ERRORLEVEL% EQU 0 (
  echo INFO: cloudflared is already running, skip starting tunnel.
  goto :eof
)

REM 启动 Cloudflare Tunnel（优先 PATH，其次常见安装路径）
where cloudflared >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  echo INFO: starting Cloudflared tunnel from PATH
  cloudflared tunnel --url http://localhost:5000
  goto :eof
)

set "CF_PATH_X86=C:\Program Files (x86)\cloudflared\cloudflared.exe"
set "CF_PATH_X64=C:\Program Files\Cloudflare\cloudflared\cloudflared.exe"

if exist "%CF_PATH_X86%" (
  echo INFO: starting Cloudflared tunnel from "%CF_PATH_X86%"
  "%CF_PATH_X86%" tunnel --url http://localhost:5000
  goto :eof
)

if exist "%CF_PATH_X64%" (
  echo INFO: starting Cloudflared tunnel from "%CF_PATH_X64%"
  "%CF_PATH_X64%" tunnel --url http://localhost:5000
  goto :eof
)

echo ERROR: cloudflared not found. Install with:
echo   winget install -e --id Cloudflare.cloudflared
pause