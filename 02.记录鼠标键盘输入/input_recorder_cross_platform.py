#!/usr/bin/env python3
"""
跨平台输入记录器（统一使用 pynput）
需求：
- 鼠标：仅监听左键、右键与中键的按下和抬起时间
- 键盘：监听所有按键的按下与抬起时间
- 以启动时间命名一个 .txt 文件，逐行写入事件
"""

import sys
from datetime import datetime

from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse


def now_iso() -> str:
    return datetime.now().isoformat()


class InputRecorder:
    def __init__(self) -> None:
        # 以启动时间创建日志文件名
        start_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"input_{start_str}.txt"
        self.running = False

        # 监听器占位
        self.keyboard_listener: pynput_keyboard.Listener | None = None
        self.mouse_listener: pynput_mouse.Listener | None = None

        # 降噪配置
        self.move_min_interval_ms: int = 50   # 鼠标移动最小记录间隔（毫秒）
        self.move_min_distance: int = 5       # 鼠标移动最小位移（像素）
        self.ignore_key_auto_repeat: bool = True  # 忽略按键自动连发（长按时不重复记 press）

        # 降噪状态
        self._last_move_ts_ms: int = 0
        self._last_move_pos: tuple[int, int] | None = None
        self._pressed_keys: set[str] = set()

    def _write_line(self, line: str) -> None:
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()

    def _log(self, device: str, action: str, detail: str) -> None:
        # 统一行格式： [ISO时间] 设备 动作 详情
        # 例如： [2025-09-29T12:00:00.123456] K PRESS key=A
        #       [2025-09-29T12:00:00.234567] M RELEASE button=left
        line = f"[{now_iso()}] {device} {action} {detail}"
        print(line)
        self._write_line(line)

    # ------------------- 键盘事件 -------------------
    def on_key_press(self, key) -> None:
        # 优先处理控制字符（如 Ctrl+C -> '\x03'）
        ctrl_combo = self._try_parse_control_combo(key)
        if ctrl_combo is not None:
            key_name, letter = ctrl_combo  # e.g. ("ctrl+c", "c")
            if self.ignore_key_auto_repeat:
                if key_name in self._pressed_keys:
                    return
                self._pressed_keys.add(key_name)
            self._log("K", "PRESS", f"key={key_name}")
            if letter == "c":
                self.stop()
                return False
            return

        key_name = self._key_to_string(key)
        # 忽略自动连发：仅第一次 press 记录，直到 release
        if self.ignore_key_auto_repeat:
            if key_name in self._pressed_keys:
                return
            self._pressed_keys.add(key_name)
        self._log("K", "PRESS", f"key={key_name}")

        # 组合键退出：Ctrl + C
        if self._is_ctrl_active() and key_name.lower() == "c":
            self.stop()
            return False

    def on_key_release(self, key):
        key_name = self._key_to_string(key)
        self._log("K", "RELEASE", f"key={key_name}")
        # 释放时从集合移除
        if key_name in self._pressed_keys:
            self._pressed_keys.remove(key_name)

        # 不再使用 ESC 退出，避免误触

    @staticmethod
    def _key_to_string(key) -> str:
        # 优先使用字符键，否则使用特殊键名字
        try:
            if hasattr(key, "char") and key.char is not None:
                return key.char
        except Exception:
            pass
        try:
            return key.name  # type: ignore[attr-defined]
        except Exception:
            return str(key)

    def _is_ctrl_active(self) -> bool:
        # 兼容多种 ctrl 名称
        ctrl_names = {"ctrl", "ctrl_l", "ctrl_r", "left_ctrl", "right_ctrl"}
        return any(name in self._pressed_keys for name in ctrl_names)

    @staticmethod
    def _is_control_char(ch: str) -> bool:
        return len(ch) == 1 and 1 <= ord(ch) <= 26

    @staticmethod
    def _control_char_to_letter(ch: str) -> str:
        # \x01 -> a, \x02 -> b, ... \x1a -> z
        return chr(ord('a') + (ord(ch) - 1))

    def _try_parse_control_combo(self, key):
        # 返回 ("ctrl+<letter>", "<letter>") 或 None
        try:
            if hasattr(key, "char") and key.char is not None:
                ch = key.char
                if self._is_control_char(ch):
                    letter = self._control_char_to_letter(ch)
                    return f"ctrl+{letter}", letter
        except Exception:
            pass
        return None

    # ------------------- 鼠标事件 -------------------
    def on_mouse_click(self, x: int, y: int, button, pressed: bool):
        # 仅关注 left/right/middle 的 press/release
        btn_name = self._button_to_lrm(button)
        if btn_name is None:
            return
        action = "PRESS" if pressed else "RELEASE"
        self._log("M", action, f"button={btn_name}")

    @staticmethod
    def _button_to_lrm(button) -> str | None:
        if button == pynput_mouse.Button.left:
            return "left"
        if button == pynput_mouse.Button.right:
            return "right"
        if button == pynput_mouse.Button.middle:
            return "middle"
        return None

    # ------------------- 控制 -------------------
    def start(self) -> None:
        self.running = True
        print("开始监听（ESC 退出）")
        print(f"日志文件: {self.log_filename}")

        self.keyboard_listener = pynput_keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release,
        )
        self.mouse_listener = pynput_mouse.Listener(
            on_click=self.on_mouse_click,
            on_move=self.on_mouse_move,
        )

        self.keyboard_listener.start()
        self.mouse_listener.start()

        # 阻塞直到键盘监听结束（例如 ESC 触发 stop）
        self.keyboard_listener.join()

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        if self.keyboard_listener is not None:
            try:
                self.keyboard_listener.stop()
            except Exception:
                pass
        if self.mouse_listener is not None:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
        print("记录已停止")

    # 移动事件放在 stop 下方仅为布局，不影响功能
    def on_mouse_move(self, x: int, y: int) -> None:
        now_ms = self._now_ms()
        last_ts = self._last_move_ts_ms
        last_pos = self._last_move_pos

        if last_pos is None:
            should_log = True
        else:
            dt_ok = (now_ms - last_ts) >= self.move_min_interval_ms
            dist_ok = self._manhattan_distance(last_pos, (x, y)) >= self.move_min_distance
            should_log = dt_ok or dist_ok

        if should_log:
            self._log("M", "MOVE", f"x={x} y={y}")
            self._last_move_ts_ms = now_ms
            self._last_move_pos = (x, y)

    @staticmethod
    def _manhattan_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now().timestamp() * 1000)


def main() -> None:
    recorder = InputRecorder()
    try:
        recorder.start()
    except KeyboardInterrupt:
        recorder.stop()
    except Exception as e:
        print(f"发生错误: {e}")
        recorder.stop()


if __name__ == "__main__":
    main()
