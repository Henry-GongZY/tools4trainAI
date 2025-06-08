from pynput.keyboard import Listener as kb_listener
from pynput.mouse import Listener as mouse_listener
from datetime import datetime
import os
import time

# 获取当前的日期和时间
current_time = datetime.now()
date = current_time.strftime("%Y_%m_%d_%H_%M_%S")
# 保存按键记录的文件路径
log_file = "data"
if not os.path.exists(log_file):
    os.mkdir(log_file)
log = open(os.path.join(log_file, f"{date}.txt"), "w")
log.write("movement,time,paras\n")

# 创建一个函数来处理按键按下事件
def on_press(key):
    timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S.%f")[:-3]  # 截取毫秒
    log.write(f"'kb_p',{timestamp},{key}\n")

# 创建一个函数来处理按键释放事件
def on_release(key):
    timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S.%f")[:-3]  # 截取毫秒
    log.write(f"'kb_r',{timestamp},{key}\n")
    if key == 'esc':  # 按下 escape 键退出监听
        return False

def on_move(x, y):
    timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S.%f")[:-3]  # 截取毫秒
    log.write(f"'ms_m',{timestamp},{x},{y}\n")

def on_click(x, y, button, pressed):
    timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S.%f")[:-3]  # 截取毫秒
    if pressed:
        log.write(f"'ms_p',{timestamp},{x},{y},{button}\n")
    else:
        log.write(f"'ms_r',{timestamp},{x},{y},{button}\n")

def on_scroll(x, y, dx, dy):
    timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S.%f")[:-3]  # 截取毫秒
    log.write(f"'ms_sc',{timestamp},{x},{y},{dx},{dy}\n")

# 启动键盘监听
kb = kb_listener(on_press=on_press, on_release=on_release)
kb.start()
ms = mouse_listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
ms.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("监听器停止")
    # 停止监听器
    kb.stop()
    ms.stop()
    log.close()