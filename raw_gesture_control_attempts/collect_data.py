import cv2
import mediapipe as mp
import numpy as np
import os
import csv
from datetime import datetime

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_drawing = mp.solutions.drawing_utils

# Создаём папки для данных
GESTURES = {'palm': '✋', 'fist': '✊', 'thumb_down': '👎', 'none': 'none'}
for folder in GESTURES.keys():
    os.makedirs(f'raw_gesture_control_attempts/data/{folder}', exist_ok=True)

cap = cv2.VideoCapture(0)
data = []
current_gesture = 'none'


def save_landmarks(landmarks, gesture):
    if landmarks:
        row = list(np.array([[lm.x, lm.y, lm.z] for lm in landmarks]).flatten())
        row.append(gesture)
        with open('gesture_data.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)


while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_image)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark
            save_landmarks(landmarks, current_gesture)

    # Интерфейс управления
    cv2.putText(image, f"Current: {GESTURES[current_gesture]}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(image, "Keys: 1 = Palm 2 = Fist 3 = Thumb Down 4 = none 0 = Exit", (10, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    cv2.imshow('Data Collection', image)

    key = cv2.waitKey(10)
    if key == ord('0'):
        break
    for i, (gesture, _) in enumerate(GESTURES.items()):
        if key == ord(str(i + 1)):
            current_gesture = gesture

cap.release()
cv2.destroyAllWindows()