import json, pyaudio
from vosk import Model, KaldiRecognizer

model = Model("./vosk-model-ru-0.42")
rec = KaldiRecognizer(model, 16000) #Создаётся объект распознавателя (KaldiRecognizer) с частотой дискретизации 16000 Гц (стандарт для Vosk).
p = pyaudio.PyAudio() #создаёт доступ к аудиоустройствам
stream = p.open( #открывает аудиопоток с нужными параметрами
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True, #говорим, что читаем с микрофона
    frames_per_buffer=8000
)
stream.start_stream() #запускает запись.


def listen():
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

# вместо этих функций будут функции для запуска пресетов из других модулей
# решили сделать так для удобсвта интегрирования
def comand_one():
    pass

def comand_two():
    pass

def comand_three():
    pass

def comand_four():
    pass

def comand_five():
    pass

def comand_six():
    pass

def comand_seven():
    pass

def comand_eight():
    pass


comands = {
    "режим один": comand_one,
    "режим два": comand_two,
    "режим три": comand_three,
    "режим четыре": comand_four,
    "режим пять": comand_five,
    "режим шесть": comand_six,
    "режим семь": comand_seven,
    "режим восемь": comand_eight,
}

for text in listen():
    print(text)

    if text == "пока":
        quit()

    if text in comands:
        print(f"Выполняется {text}")
        comands[text]() 