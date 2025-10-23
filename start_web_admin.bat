@echo off
title 图纸查询系统 - Web版本 (管理员模式)

echo ========================================
echo 图纸查询系统 - Web版本启动器
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 已获得管理员权限，将自动配置防火墙
) else (
    echo ⚠️  未检测到管理员权限
    echo 💡 建议右键选择"以管理员身份运行"以自动配置防火墙
)

echo.
echo 🚀 正在启动Web服务器...
echo.

REM 启动Python Web应用
python run_web.py

echo.
echo 👋 Web服务器已停止
pause