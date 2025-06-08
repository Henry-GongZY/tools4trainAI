#include <iostream>
#include <fstream>
#include <chrono>
#include <thread>
#include <iomanip>
#include <windows.h>
#include "interception.h"

std::ofstream logFile("input_log.txt", std::ios::app);

// 获取当前时间戳
std::string timestamp() {
    auto now = std::chrono::system_clock::now();
    auto t = std::chrono::system_clock::to_time_t(now);
    std::tm tm;
    localtime_s(&tm, &t);
    char buf[64];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tm);
    return std::string(buf);
}

int main() {
    InterceptionContext context = interception_create_context();

    interception_set_filter(context, interception_is_keyboard, INTERCEPTION_FILTER_KEY_ALL);
    interception_set_filter(context, interception_is_mouse, INTERCEPTION_FILTER_MOUSE_ALL);

    InterceptionStroke stroke;
    InterceptionDevice device;

    std::cout << "Logging started. Press ESC to exit.\n";

    while (true) {
        device = interception_wait(context);
        if (interception_receive(context, device, &stroke, 1) > 0) {
            std::string ts = timestamp();

            if (interception_is_keyboard(device)) {
                InterceptionKeyStroke &kstroke = *(InterceptionKeyStroke *)&stroke;

                logFile << "[" << ts << "] "
                        << "Key "
                        << (kstroke.state & INTERCEPTION_KEY_UP ? "UP" : "DOWN")
                        << " Code: " << kstroke.code << std::endl;

                if (kstroke.code == 1 && !(kstroke.state & INTERCEPTION_KEY_UP)) { // ESC键按下
                    break;
                }
            }
            else if (interception_is_mouse(device)) {
                InterceptionMouseStroke &mstroke = *(InterceptionMouseStroke *)&stroke;

                logFile << "[" << ts << "] "
                        << "Mouse "
                        << "X: " << mstroke.x << " Y: " << mstroke.y
                        << " Flags: " << mstroke.flags << std::endl;
            }

            interception_send(context, device, &stroke, 1);
        }
    }

    interception_destroy_context(context);
    logFile.close();
    std::cout << "Logging stopped.\n";
    return 0;
}
