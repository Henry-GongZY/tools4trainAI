from pyinterception import Interception, KeyState, Filter
import time

interception = Interception()
interception.set_filter(interception.is_keyboard, Filter.KEY_ALL)
interception.set_filter(interception.is_mouse, Filter.MOUSE_ALL)

with open("input_log.txt", "a", encoding="utf-8") as log_file:
    print("开始监听（ESC 退出）")
    try:
        while True:
            device = interception.wait()
            stroke = interception.receive(device)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            if interception.is_keyboard(device):
                key_code = stroke.code
                state = "DOWN" if stroke.state == KeyState.DOWN else "UP"
                line = f"[{timestamp}] Keyboard {state} - Code: {key_code}\n"
                print(line.strip())
                log_file.write(line)
                log_file.flush()
                if key_code == 1 and stroke.state == KeyState.DOWN:  # ESC 退出
                    print("检测到 ESC，退出监听。")
                    break

            elif interception.is_mouse(device):
                line = f"[{timestamp}] Mouse - X:{stroke.x}, Y:{stroke.y}, Flags:{stroke.flags}, State:{stroke.state}\n"
                print(line.strip())
                log_file.write(line)
                log_file.flush()

    except KeyboardInterrupt:
        print("手动中断。")
