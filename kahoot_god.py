import keyboard
import pyautogui
import pytesseract
import requests
import json
import traceback
import cv2
import numpy as np
from PIL import Image


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

OPENROUTER_KEY = "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"  # <-- Replace with yours

DEBUG = True

def debug_log(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def preprocess_for_white_text(pil_img):
    # Convert PIL → OpenCV
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Convert to HSV so we can isolate white text
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # White color range (tuned for Kahoot bright backgrounds)
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 60, 255])

    # Mask to keep ONLY white text
    mask = cv2.inRange(hsv, lower_white, upper_white)

    # Optional: dilate to make letters thicker
    kernel = np.ones((2,2), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Convert to OCR-friendly image
    result = cv2.bitwise_and(img, img, mask=mask)
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)

    # Increase contrast
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    return Image.fromarray(gray)

def click_button(button):
    # These Y-coordinates are shifted down to match your new layout
    button_coords = {
        1: (0.23, 0.75),  # Was 0.65
        2: (0.77, 0.75),  # Was 0.65
        3: (0.20, 0.83),  # Was 0.80
        4: (0.87, 0.83)  # Was 0.80
    }
    screen_width, screen_height = pyautogui.size()
    x, y = button_coords[button]
    x, y = int(screen_width * x), int(screen_height * y)

    debug_log(f"Clicking button {button} at pixel: ({x}, {y})")
    pyautogui.click(x, y)

def chatGPT_answer(question_and_answers):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = { "Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json" }
    payload = { "model": "openai/gpt-4o-mini", "messages": [
        { "role": "system",
          "content": "You are a helpful assistant specialized in answering multiple-choice questions. Only respond with an integer (1–4)." },
        {"role": "user", "content": question_and_answers} ] }
    debug_log("==== Sending Payload to OpenRouter ====")
    debug_log(json.dumps(payload, indent=4))
    try:
        response = requests.post(url, headers=headers, json=payload)
        debug_log(f"==== Raw API Response ====\n{response.text}")
        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()
        debug_log(f"Model raw reply: '{reply}'")
        # Try safe conversion
        for c in reply:
            if c.isdigit() and c in "1234":
                debug_log(f"Extracted integer: {c}")
                return int(c)
        debug_log("❌ Model did not return a proper digit 1–4.")
        return None
    except Exception as e:
        print("❌ Error in chatGPT_answer:", e)
        traceback.print_exc()
        return None


def local_lm_answer(question_and_answers):
    url = "http://localhost:1234/v1/chat/completions"  # LM Studio local server

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "model": "local-model",  # LM Studio ignores this value, but it must exist
        "messages": [
            {
                "role": "system",
                "content": """You are a multiple-choice question answering model.
                             The user will give a question and 4 answer options labeled 1, 2, 3, 4.
                                Always respond with **only the number corresponding to the correct answer**.
                                Do not explain, do not add text.
                                Example input:
                                Question: Which fruit floats in water?
                                1: Cranberry
                                2: Pear
                                3: Plum
                                4: Peach
                                Example output:
                                2
                            """
            },
            {
                "role": "user",
                "content": question_and_answers
            }
        ],
        "temperature": 0.1,
        "max_tokens": 5
    }

    debug_log("==== Sending Payload to LM Studio ====")
    debug_log(json.dumps(payload, indent=4))

    try:
        response = requests.post(url, headers=headers, json=payload)

        debug_log(f"==== Raw API Response ====\n{response.text}")

        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()

        debug_log(f"Model raw reply: '{reply}'")

        # Extract the answer (1-4)
        for c in reply:
            if c in "1234":
                debug_log(f"Extracted integer: {c}")
                return int(c)

        debug_log("❌ Model did not return a proper digit 1–4.")
        return None

    except Exception as e:
        print("❌ Error in chatGPT_answer:", e)
        traceback.print_exc()
        return None

def kahoot_god():
    # Updated normalized coordinates for 2560X1440
    question_and_answers = {
        0: {"top_left": (0.042, 0.667), "bottom_right": (1.0, 0.742)},
        1: {"top_left": (0.042, 0.7), "bottom_right": (0.458, 0.8)},
        2: {"top_left": (0.542, 0.7), "bottom_right": (1.0, 0.8)},
        3: {"top_left": (0.042, 0.8), "bottom_right": (0.458, 0.875)},
        4: {"top_left": (0.542, 0.8), "bottom_right": (1.0, 0.875)},
    }

    screen_width, screen_height = pyautogui.size()
    print(screen_width, screen_height)
    full_prompt = ""

    debug_log("==== Starting OCR Capture ====")

    for index in question_and_answers:
        coords = question_and_answers[index]
        x1, y1 = coords["top_left"]
        x2, y2 = coords["bottom_right"]

        # Convert normalized → actual pixels
        x1 = int(x1 * screen_width)
        y1 = int(y1 * screen_height)
        x2 = int(x2 * screen_width)
        y2 = int(y2 * screen_height)
        width = x2 - x1
        height = y2 - y1

        debug_log(f"Region {index}: ({x1}, {y1}) to ({x2}, {y2}) size ({width}x{height})")

        screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        #screenshot.save(f"debug_region.png")
        processed = preprocess_for_white_text(screenshot)
        text = pytesseract.image_to_string(
            processed,
            config="--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789?"
        ).strip()

        debug_log(f"OCR output for region {index}: '{text}'")

        if index == 0:
            full_prompt += f"Question: {text}\n"
        else:
            full_prompt += f"{index}: {text}\n"

        # screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        # screenshot.save(f"debug_region_{index}.png")  # SAVE THE IMAGE

    debug_log("==== Final prompt sent to model: ====")
    debug_log(full_prompt)


    answer = chatGPT_answer(full_prompt)
    #answer = local_lm_answer(full_prompt)

    if answer:
        click_button(answer)
        print(f"✔ Answer selected: {answer}")
    else:
        print("❌ Failed to determine answer.")

# Hotkey
keyboard.add_hotkey("alt+a", kahoot_god)
keyboard.wait()
