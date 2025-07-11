import json, pyaudio, threading
from vosk import Model, KaldiRecognizer

from clicker.bin.config_parse import get_item_from_config

# Импортируем функции управления пресетами
from clicker.bin.funcs import run_preset
from clicker.bin.glob import bot  # Для отправки уведомлений в Telegram

# Инициализация модели Vosk
model = Model("/Users/Valerij/Downloads/sadom/clicker/voice_module/vosk-model-ru-0.42")
rec = KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=8000
)
stream.start_stream()

# ID чата для уведомлений (можно задать в конфиге или получить из бота)
ADMIN_CHAT_ID = get_item_from_config('CHAT_ID')['chat_id']


def listen():
    """Функция прослушивания голосовых команд"""
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data) and len(data) > 0:
            result = json.loads(rec.Result())
            text = result.get("text", "").lower()
            if not text:
                continue

            if text.startswith("миша"):
                command_text = text.replace("миша", "", 1).strip()
                yield command_text
            else:
                continue


def execute_preset(preset_name):
    """Выполняет пресет и отправляет уведомление"""
    try:
        print(f"[Голосовое управление] Активация пресета: {preset_name}")

        # Запускаем пресет
        run_preset(preset_name)

        # Отправляем уведомление в Telegram
        if bot and ADMIN_CHAT_ID:
            bot.send_message(
                ADMIN_CHAT_ID,
                f"🎤 [Голосовая команда] Активирован пресет: {preset_name}"
            )

    except Exception as e:
        print(f"[Голосовое управление] Ошибка: {e}")


# Сопоставление голосовых команд с пресетами
comands = {
    "режим один": "1",
    "режим два": "2",
    "режим три": "bmstu",
}


def start_voice_control():
    """Запускает систему голосового управления"""
    print("[Голосовое управление] Система активирована")
    for text in listen():
        print(f"[Голосовое управление] Распознано: {text}")

        if text == "пока":
            print("[Голосовое управление] Система отключена")
            quit()

        # Ищем соответствие в командах
        preset_name = comands.get(text)
        if preset_name:
            execute_preset(preset_name)
        else:
            print(f"[Голосовое управление] Неизвестная команда: {text}")


# Запуск в отдельном потоке
voice_thread = threading.Thread(target=start_voice_control, daemon=True)
voice_thread.start()