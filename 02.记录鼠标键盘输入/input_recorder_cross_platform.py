#!/usr/bin/env python3
"""
跨平台鼠标键盘输入记录器
支持 Windows、macOS 和 Linux
"""

import sys
import time
import threading
import json
from datetime import datetime

def get_platform():
    """检测当前操作系统"""
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('darwin'):
        return 'macos'
    elif sys.platform.startswith('linux'):
        return 'linux'
    else:
        return 'unknown'

def setup_platform_specific():
    """根据平台设置相应的库"""
    platform = get_platform()
    
    if platform == 'windows':
        try:
            from pyinterception import Interception, KeyState, Filter
            return 'pyinterception', Interception, KeyState, Filter
        except ImportError:
            print("请安装 pyinterception: pip install pyinterception")
            return None, None, None, None
    
    elif platform == 'macos':
        try:
            import pynput
            from pynput import mouse, keyboard
            return 'pynput', mouse, keyboard, None
        except ImportError:
            print("请安装 pynput: pip install pynput")
            return None, None, None, None
    
    elif platform == 'linux':
        try:
            import pynput
            from pynput import mouse, keyboard
            return 'pynput', mouse, keyboard, None
        except ImportError:
            print("请安装 pynput: pip install pynput")
            return None, None, None, None
    
    else:
        print(f"不支持的操作系统: {platform}")
        return None, None, None, None

class InputRecorder:
    def __init__(self, log_file="input_log.txt"):
        self.log_file = log_file
        self.running = False
        self.library, self.mouse_lib, self.keyboard_lib, self.filter_lib = setup_platform_specific()
        
        if not self.library:
            print("无法初始化输入记录器")
            sys.exit(1)
    
    def log_keyboard(self, action, key, key_code=None):
        """记录键盘事件"""
        timestamp = datetime.now().isoformat()
        
        # 控制台输出
        print(f"[{timestamp}] K {action.upper()} {key}")
        
        # 文件记录 - 只记录必要信息
        event = {
            "t": timestamp,
            "k": action,  # press/release
            "key": key,
            "code": key_code
        }
        
        with open("keyboard_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
    
    def log_mouse(self, action, **kwargs):
        """记录鼠标事件"""
        timestamp = datetime.now().isoformat()
        
        # 控制台输出
        if action == "move":
            print(f"[{timestamp}] M MOVE {kwargs['x']},{kwargs['y']}")
        elif action in ["press", "release"]:
            print(f"[{timestamp}] M {action.upper()} {kwargs['button']} {kwargs['x']},{kwargs['y']}")
        elif action == "scroll":
            print(f"[{timestamp}] M SCROLL {kwargs['dx']},{kwargs['dy']} {kwargs['x']},{kwargs['y']}")
        
        # 文件记录 - 只记录必要信息
        event = {"t": timestamp, "m": action}
        event.update(kwargs)
        
        with open("mouse_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
    
    def on_key_press(self, key):
        """按键按下事件"""
        try:
            key_name = key.name if hasattr(key, 'name') else str(key)
            key_code = key.vk if hasattr(key, 'vk') else None
        except AttributeError:
            key_name = str(key)
            key_code = None
        
        self.log_keyboard("press", key_name, key_code)
    
    def on_key_release(self, key):
        """按键释放事件"""
        try:
            key_name = key.name if hasattr(key, 'name') else str(key)
            key_code = key.vk if hasattr(key, 'vk') else None
        except AttributeError:
            key_name = str(key)
            key_code = None
        
        self.log_keyboard("release", key_name, key_code)
        
        # ESC 键退出
        if key == keyboard.Key.esc:
            print("检测到 ESC，退出监听。")
            self.running = False
            return False
    
    def on_mouse_move(self, x, y):
        """鼠标移动事件"""
        self.log_mouse("move", x=x, y=y)
    
    def on_mouse_click(self, x, y, button, pressed):
        """鼠标点击事件"""
        action = "press" if pressed else "release"
        self.log_mouse(action, button=str(button), x=x, y=y)
    
    def on_mouse_scroll(self, x, y, dx, dy):
        """鼠标滚轮事件"""
        self.log_mouse("scroll", x=x, y=y, dx=dx, dy=dy)
    
    def start_recording_windows(self):
        """Windows 平台记录"""
        interception = self.mouse_lib()
        interception.set_filter(interception.is_keyboard, self.filter_lib.KEY_ALL)
        interception.set_filter(interception.is_mouse, self.filter_lib.MOUSE_ALL)
        
        self.log_event("System", "开始监听（ESC 退出）")
        
        try:
            while self.running:
                device = interception.wait()
                stroke = interception.receive(device)
                
                if interception.is_keyboard(device):
                    key_code = stroke.code
                    state = "DOWN" if stroke.state == self.keyboard_lib.DOWN else "UP"
                    self.log_event(f"Keyboard {state}", f"Code: {key_code}")
                    
                    if key_code == 1 and stroke.state == self.keyboard_lib.DOWN:  # ESC
                        self.log_event("System", "ESC detected, stopping...")
                        break
                
                elif interception.is_mouse(device):
                    self.log_event("Mouse", f"X: {stroke.x}, Y: {stroke.y}, Flags: {stroke.flags}, State: {stroke.state}")
        
        except Exception as e:
            self.log_event("Error", f"Windows recording error: {e}")
    
    def start_recording_pynput(self):
        """使用 pynput 的记录（macOS/Linux）"""
        self.log_event("System", "开始监听（ESC 退出）")
        
        # 设置键盘监听器
        keyboard_listener = self.keyboard_lib.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        
        # 设置鼠标监听器
        mouse_listener = self.mouse_lib.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        
        try:
            # 启动监听器
            keyboard_listener.start()
            mouse_listener.start()
            
            # 保持运行
            while self.running:
                time.sleep(0.1)
        
        except Exception as e:
            self.log_event("Error", f"Pynput recording error: {e}")
        finally:
            keyboard_listener.stop()
            mouse_listener.stop()
    
    def start(self):
        """开始记录"""
        self.running = True
        
        if self.library == 'pyinterception':
            self.start_recording_windows()
        elif self.library == 'pynput':
            self.start_recording_pynput()
    
    def stop(self):
        """停止记录"""
        self.running = False
        self.log_event("System", "记录已停止")

def main():
    print("跨平台鼠标键盘输入记录器")
    print(f"当前平台: {get_platform()}")
    print("=" * 50)
    
    recorder = InputRecorder()
    
    try:
        recorder.start()
    except KeyboardInterrupt:
        print("\n手动中断")
        recorder.stop()
    except Exception as e:
        print(f"发生错误: {e}")
        recorder.stop()

if __name__ == "__main__":
    main()
