import cv2
import time
import os
import sys
import HandTrackingModule as htm


def comand_one():
    print("Активирован режим 1 (1 палец)")

def comand_two():
    print("Активирован режим 2 (2 пальца)")

def comand_three():
    print("Активирован режим 3 (3 пальца)")

def comand_four():
    print("Активирован режим 4 (4 пальца)")

def comand_five():
    print("Активирован режим 5 (5 пальцев)")



comands = {
    1: comand_one,
    2: comand_two,
    3: comand_three,
    4: comand_four,
    5: comand_five,
}
class CameraController:
    def __init__(self, width=640, height=480, device=0):
        self.width = width
        self.height = height
        self.device = device
        self.cap = None
        self.initialize()

    def initialize(self, max_attempts=3, delay=1):
        """Инициализация камеры с несколькими попытками"""
        backends = [
            cv2.CAP_DSHOW,  # Windows DirectShow
            cv2.CAP_MSMF,  # Microsoft Media Foundation
            cv2.CAP_V4L2,  # Linux
            cv2.CAP_ANY  # Автовыбор
        ]

        for backend in backends:
            for attempt in range(max_attempts):
                self.cap = cv2.VideoCapture(self.device, backend)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

                    actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                    if actual_width > 0 and actual_height > 0:
                        print(f"Камера инициализирована ({actual_width}x{actual_height}), backend: {backend}")
                        return True

                    print(f"Предупреждение: некорректное разрешение {actual_width}x{actual_height}")
                    self.cap.release()

                if attempt < max_attempts - 1:
                    print(f"Попытка {attempt + 1} из {max_attempts}...")
                    time.sleep(delay)

        print("Ошибка: не удалось инициализировать камеру")
        return False

    def read_frame(self, max_attempts=3):
        """Чтение кадра с обработкой ошибок"""
        for attempt in range(max_attempts):
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    return True, frame

                print(f"Пустой кадр (попытка {attempt + 1})")
                self.release()
                time.sleep(0.5)
                if self.initialize():
                    continue

            time.sleep(0.1)

        return False, None

    def release(self):
        """Корректное освобождение ресурсов"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def __del__(self):
        self.release()


def load_finger_images(folder_path):
    """Загрузка изображений пальцев с проверкой"""
    if not os.path.exists(folder_path):
        print(f"Ошибка: папка {folder_path} не найдена")
        return None

    overlay_list = []
    for img_name in sorted(os.listdir(folder_path)):
        img_path = os.path.join(folder_path, img_name)
        img = cv2.imread(img_path)
        if img is not None:
            overlay_list.append(img)
        else:
            print(f"Предупреждение: не удалось загрузить {img_name}")

    if not overlay_list:
        print("Ошибка: нет загруженных изображений")
        return None

    return overlay_list


def main():
    camera = CameraController(width=640, height=480)
    if not camera.cap:
        return 1

    overlay_list = load_finger_images("fingers")
    if overlay_list is None:
        camera.release()
        return 1

    detector = htm.HandDetector(min_detection_confidence=0.7)
    total_fingers = 0
    fps_time = time.time()
    last_command_time = 0
    command_delay = 1

    while True:
        success, frame = camera.read_frame()
        if not success:
            print("Критическая ошибка: не удалось получить кадр")
            break

        frame = cv2.flip(frame, 1)
        frame = detector.find_hands(frame)

        finger_count = 0
        if detector.results.multi_hand_landmarks:
            landmarks = detector.get_landmarks(frame)
            if landmarks:
                fingers_up = detector.count_fingers_up(landmarks)
                finger_count = sum(fingers_up)

                current_time = time.time()
                if (finger_count in comands and
                    finger_count != total_fingers and
                    current_time - last_command_time > command_delay):
                    comands[finger_count]()
                    total_fingers = finger_count
                    last_command_time = current_time

        if 0 <= finger_count < len(overlay_list):
            h, w = overlay_list[finger_count].shape[:2]
            frame[0:h, 0:w] = overlay_list[finger_count]

        current_time = time.time()
        fps = 1 / (current_time - fps_time)
        fps_time = current_time
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.rectangle(frame, (20, 225), (120, 325), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, str(finger_count), (45, 300),
                    cv2.FONT_HERSHEY_PLAIN, 5, (255, 0, 0), 10)

        cv2.imshow("Finger Counter", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()
    return 0

if __name__ == "__main__":
    sys.exit(main())