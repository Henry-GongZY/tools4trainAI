@echo off
setlocal enabledelayedexpansion

:: 设置输入文件夹
set "input_folder=C:\path\to\videos"
:: 设置输出文件夹
set "output_folder=C:\path\to\screenshots"

:: 确保 ffmpeg 在系统路径中
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo 请确保已安装 ffmpeg 并将其添加到系统路径中。
    pause
    exit /b
)

:: 遍历视频文件
for %%F in ("%input_folder%\*.mp4") do (
    set "filename=%%~nF"
    set "screenshot_dir=%output_folder%\!filename!"
    
    :: 检查目标文件夹是否存在，存在则跳过
    if exist "!screenshot_dir!" (
        echo 跳过 !filename!，截图文件夹已存在。
        continue
    )
    
    :: 创建目标文件夹
    mkdir "!screenshot_dir!"
    
    :: 执行截图
    ffmpeg -i "%%F" -vf "fps=1" "!screenshot_dir!\frame_%%04d.jpg"
    echo 已处理 !filename!
)

echo 所有视频已处理完成。
pause
