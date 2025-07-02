import cv2
import mediapipe as mp
import numpy as np
import joblib
import webbrowser
import os
import time
import subprocess

# Загрузка модели
model = joblib.load('gesture_model.pkl')
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)

# Соответствие жестов командам
GESTURE_COMMANDS = {
    'palm': lambda: webbrowser.open('https://vk.com'),
    'fist': lambda: webbrowser.open('https://mail.ru'),
    'thumb_down': lambda: subprocess.run(['pkill', 'Safari']),  # Для macOS
}

cap = cv2.VideoCapture(0)
last_command_time = 0

while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_image)
    gesture_detected = None

    if results.multi_hand_landmarks:
        landmarks = results.multi_hand_landmarks[0].landmark
        input_data = np.array([[lm.x, lm.y, lm.z] for lm in landmarks]).flatten().reshape(1, -1)
        gesture = model.predict(input_data)[0]

        if gesture != 'none':
            cv2.putText(image, f"Gesture: {gesture}", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            gesture_detected = gesture

    cv2.imshow('Gesture Control', image)

    # Обработка команд с задержкой
    current_time = time.time()
    if gesture_detected and current_time - last_command_time > 5:
        if gesture_detected in GESTURE_COMMANDS:
            GESTURE_COMMANDS[gesture_detected]()
            last_command_time = current_time

    if cv2.waitKey(10) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()