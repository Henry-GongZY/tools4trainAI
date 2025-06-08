#include <windows.h>
#include <iostream>
#include <chrono>
#include <iomanip>
#include <fstream>

// 全局日志文件
std::ofstream logFile("input_log.txt", std::ios::app);

// 格式化当前时间
std::string currentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto t = std::chrono::system_clock::to_time_t(now);
    std::tm tm;
    localtime_s(&tm, &t);

    char buf[64];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tm);
    return std::string(buf);
}
std::wstring CharToWString(const char* str)
{
    int size_needed = MultiByteToWideChar(CP_ACP, 0, str, -1, NULL, 0);
    std::wstring wstrTo(size_needed, 0);
    MultiByteToWideChar(CP_ACP, 0, str, -1, &wstrTo[0], size_needed);
    return wstrTo;
}

// 窗口过程，处理原始输入消息
LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    if (uMsg == WM_INPUT) {
        UINT dwSize = 0;
        GetRawInputData((HRAWINPUT)lParam, RID_INPUT, NULL, &dwSize, sizeof(RAWINPUTHEADER));
        if (dwSize > 0) {
            BYTE* lpb = new BYTE[dwSize];
            if (GetRawInputData((HRAWINPUT)lParam, RID_INPUT, lpb, &dwSize, sizeof(RAWINPUTHEADER)) == dwSize) {
                RAWINPUT* raw = (RAWINPUT*)lpb;

                std::string ts = currentTimestamp();

                if (raw->header.dwType == RIM_TYPEKEYBOARD) {
                    RAWKEYBOARD& kb = raw->data.keyboard;
                    std::string eventType = (kb.Flags & RI_KEY_BREAK) ? "UP" : "DOWN";
                    std::cout << "[" << ts << "] Keyboard " << eventType << " - MakeCode: " << kb.MakeCode
                        << " VKey: " << kb.VKey << std::endl;
                    if (logFile.is_open()) {
                        logFile << "[" << ts << "] Keyboard " << eventType << " - MakeCode: " << kb.MakeCode
                            << " VKey: " << kb.VKey << std::endl;
                        logFile.flush();
                    }
                    if (kb.VKey == VK_ESCAPE && eventType == "DOWN") {
                        // ESC退出
                        PostQuitMessage(0);
                    }
                }
                else if (raw->header.dwType == RIM_TYPEMOUSE) {
                    RAWMOUSE& mouse = raw->data.mouse;
                    /*std::cout << "[" << ts << "] Mouse: ButtonsFlags=" << mouse.usButtonFlags
                        << " LastX=" << mouse.lLastX << " LastY=" << mouse.lLastY << std::endl;
                    if (logFile.is_open()) {
                        logFile << "[" << ts << "] Mouse: ButtonsFlags=" << mouse.usButtonFlags
                            << " LastX=" << mouse.lLastX << " LastY=" << mouse.lLastY << std::endl;
                        logFile.flush();
                    }*/
                }
            }
            delete[] lpb;
        }
        return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

int main() {
    HINSTANCE hInstance = GetModuleHandle(NULL);

    const char CLASS_NAME[] = "RawInputListener";

    WNDCLASS wc = { };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CharToWString(CLASS_NAME).c_str();

    RegisterClass(&wc);

    HWND hwnd = CreateWindowEx(
        0,
        wc.lpszClassName,
        L"Raw Input Listener",
        0,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        NULL,
        NULL,
        hInstance,
        NULL
    );

    if (!hwnd) {
        std::cerr << "CreateWindowEx failed\n";
        std::cerr << "CreateWindowEx failed with error: " << GetLastError() << std::endl;
        return 1;
    }

    // 注册监听键盘和鼠标的原始输入
    RAWINPUTDEVICE rid[2];

    rid[0].usUsagePage = 0x01; // Generic Desktop Controls
    rid[0].usUsage = 0x06;     // Keyboard
    rid[0].dwFlags = RIDEV_INPUTSINK; // 即使程序失去焦点也监听
    rid[0].hwndTarget = hwnd;

    rid[1].usUsagePage = 0x01;
    rid[1].usUsage = 0x02;     // Mouse
    rid[1].dwFlags = RIDEV_INPUTSINK;
    rid[1].hwndTarget = hwnd;

    if (!RegisterRawInputDevices(rid, 2, sizeof(RAWINPUTDEVICE))) {
        std::cerr << "RegisterRawInputDevices failed\n";
        return 1;
    }

    std::cout << "开始监听，按 ESC 退出\n";

    MSG msg = { };
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    if (logFile.is_open()) {
        logFile.close();
    }

    std::cout << "程序退出\n";
    return 0;
}
