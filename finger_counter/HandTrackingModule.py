import cv2
import mediapipe as mp
import math


class HandDetector:
    def __init__(self, static_image_mode=False, max_num_hands=2,
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """Инициализация детектора рук"""
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.results = None

        # ID кончиков пальцев (большой, указательный, средний, безымянный, мизинец)
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw=True):
        """Обнаружение рук на изображении"""
        if img is None:
            return img

        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            self.results = self.hands.process(img_rgb)

            if self.results.multi_hand_landmarks and draw:
                for hand_landmarks in self.results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                        self.mp_draw.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2)
                    )
        except Exception as e:
            print(f"Ошибка при обнаружении рук: {e}")

        return img

    def get_landmarks(self, img, hand_number=0, draw=False):
        """Получение позиций ключевых точек руки"""
        landmarks = []
        if not self.results or not self.results.multi_hand_landmarks:
            return landmarks

        if hand_number < len(self.results.multi_hand_landmarks):
            hand = self.results.multi_hand_landmarks[hand_number]
            h, w = img.shape[:2]

            for id, landmark in enumerate(hand.landmark):
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                landmarks.append([id, cx, cy])

                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 0), cv2.FILLED)

        return landmarks

    def count_fingers_up(self, landmarks):
        """Подсчет поднятых пальцев"""
        fingers = []

        if not landmarks or len(landmarks) < 21:
            return [0, 0, 0, 0, 0]

        if landmarks[self.tip_ids[0]][1] < landmarks[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        for tip in self.tip_ids[1:]:
            if len(landmarks) > tip and len(landmarks) > tip - 2:
                if landmarks[tip][2] < landmarks[tip - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
            else:
                fingers.append(0)

        return fingers
