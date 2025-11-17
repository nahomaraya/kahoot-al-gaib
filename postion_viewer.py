import pyautogui
import time
import os

os.system("cls")  # clear the terminal

print("Move your mouse around. Press Ctrl+C to stop.\n")

while True:
    try:
        x, y = pyautogui.position()
        screen_width, screen_height = pyautogui.size()

        print(
            f"Pixel: ({x}, {y})   |   Percent: ({x/screen_width:.3f}, {y/screen_height:.3f})",
            end="\r"
        )
        time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopped.")
        break
