#!/usr/bin/env python3
"""
手柄输入记录器 (基于 pygame) - macOS 兼容优化版
需求：
- 跨平台支持 (Windows, macOS, Linux)
- 记录所有手柄的轴 (Axes)、按钮 (Buttons) 和方向键 (Hats)
- 自动过滤摇杆死区及微小抖动
- 以启动时间命名 .txt 文件，逐行写入事件
- 可与游戏同时运行，互不干扰
"""

import os
import sys
import time
from datetime import datetime

# 隐藏 pygame 欢迎信息
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

try:
    import pygame
except ImportError:
    print("错误: 未找到 pygame 库。请运行 'pip install pygame' 安装。")
    sys.exit(1)


def now_iso() -> str:
    return datetime.now().isoformat()


class GamepadRecorder:
    def __init__(self) -> None:
        # 日志配置
        start_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"gamepad_{start_str}.txt"
        
        # 记录配置
        self.deadzone = 0.05       # 摇杆死区（0.0-1.0）
        self.min_delta = 0.01      # 轴数值最小变化阈值
        self.poll_interval = 0.01  # 采样间隔 (秒)
        
        self.running = False
        self.joysticks = {}        # 存储已初始化的手柄实例
        self.last_axes = {}        # 存储上一次的轴数值
        self.last_hats = {}        # 存储上一次的方向键状态

    def _write_line(self, line: str) -> None:
        try:
            with open(self.log_filename, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
        except Exception as e:
            print(f"写入日志失败: {e}")

    def _log(self, action: str, detail: str) -> None:
        line = f"[{now_iso()}] G {action} {detail}"
        print(line)
        self._write_line(line)

    def init_joysticks(self):
        """初始化手柄，增加 macOS 兼容性扫描逻辑"""
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        
        # macOS 兼容性：强制刷新事件队列，给系统响应时间
        pygame.event.pump()
        time.sleep(0.1)
        pygame.event.pump()

        count = pygame.joystick.get_count()
        
        # 如果没检测到，尝试重扫描几次
        if count == 0:
            print("正在扫描手柄，请确保手柄已连接...")
            for i in range(10):
                time.sleep(0.5)
                pygame.event.pump()
                count = pygame.joystick.get_count()
                if count > 0:
                    break
                print(f"扫描中... ({i+1}/10)", end="\r")
        
        if count == 0:
            print("\n" + "="*40)
            print("错误: 未检测到任何手柄。")
            print("如果您使用的是 macOS，请检查以下设置：")
            print("1. [系统设置] -> [隐私与安全性] -> [输入监听]")
            print("2. 确保您当前的终端 (Terminal/VSCode) 已勾选并开启")
            print("3. 如果已经开启，请尝试彻底重启终端应用")
            print("="*40)
            return False
        
        print(f"\n检测到 {count} 个手柄。")
        for i in range(count):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                name = joy.get_name()
                guid = joy.get_guid()
                self.joysticks[i] = joy
                self.last_axes[i] = [0.0] * joy.get_numaxes()
                self.last_hats[i] = [(0, 0)] * joy.get_numhats()
                self._log("INFO", f"Initialized [ID={i}] Name={name}")
            except Exception as e:
                print(f"初始化手柄 {i} 失败: {e}")
        
        return True

    def start(self):
        # 初始化 pygame 全局环境
        pygame.init()
        
        # 尝试初始化手柄
        if not self.init_joysticks():
            pygame.quit()
            return

        self.running = True
        print(f"开始录制手柄输入... (按 Ctrl+C 停止)")
        print(f"日志文件: {self.log_filename}")

        try:
            while self.running:
                # 必须定期调用 pump() 以刷新底层 SDL 状态
                pygame.event.pump()
                
                # 处理所有待处理事件
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self._log("BUTTON_DOWN", f"id={event.joy} btn={event.button}")
                    elif event.type == pygame.JOYBUTTONUP:
                        self._log("BUTTON_UP", f"id={event.joy} btn={event.button}")
                    elif event.type == pygame.JOYHATMOTION:
                        self._log("HAT_MOVE", f"id={event.joy} hat={event.hat} val={event.value}")
                    elif event.type == pygame.JOYDEVICEADDED:
                        print(f"\n[检测到新设备插入]")
                        self.init_joysticks()
                    elif event.type == pygame.JOYDEVICEREMOVED:
                        print(f"\n[检测到设备拔出]")
                        self.init_joysticks()

                # 处理轴 (Axes) - 通过轮询获取连续值
                for joy_id, joy in self.joysticks.items():
                    # 注意：如果设备中途断开，joy 可能会失效，init_joysticks 会重新构建列表
                    try:
                        for a in range(joy.get_numaxes()):
                            val = joy.get_axis(a)
                            
                            # 死区过滤
                            if abs(val) < self.deadzone:
                                val = 0.0
                            
                            # 变化率过滤
                            last_val = self.last_axes[joy_id][a]
                            if abs(val - last_val) > self.min_delta:
                                self._log("AXIS_MOVE", f"id={joy_id} axis={a} val={val:.4f}")
                                self.last_axes[joy_id][a] = val
                    except:
                        continue

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"运行出错: {e}")
            self.stop()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self._log("INFO", "Recording stopped.")
        pygame.joystick.quit()
        pygame.quit()
        print("\n记录已停止。")


if __name__ == "__main__":
    recorder = GamepadRecorder()
    recorder.start()
