import json, pyaudio
from vosk import Model, KaldiRecognizer

model = Model("D:/vosk-model-small-ru-0.4")
rec = KaldiRecognizer(model, 16000) #Создаётся объект распознавателя (KaldiRecognizer) с частотой дискретизации 16000 Гц (стандарт для Vosk).
p = pyaudio.PyAudio() #создаёт доступ к аудиоустройствам
stream = p.open( #открывает аудиопоток с нужными параметрами
    format=pyaudio.paInt16, 
    channels=1, 
    rate=16000, 
    input=True,
    frames_per_buffer=8000 
)
stream.start_stream() #запускает запись.


def listen():
    activated = False
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data) and len(data) > 0:
            result = json.loads(rec.Result())
            text = result.get("text", "").lower()
            if not text:
                continue

            if not activated:
                # Ждём фразу активации
                if "привет помощник" in text:
                    print("Активация: фраза распознана.")
                    activated = True
            else:
                # Уже активирован
                if "помощник пока" in text:
                    print("Деактивация: режим ожидания.")
                    activated = False
                    continue

                # Возвращаем распознанную команду
                yield text


for text in listen():
    print(text)
    if text == "пока":
        quit()


    