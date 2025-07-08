# bin/data_loader.py
import json
import os


def load_presets():
    try:
        presets_path = os.path.join(os.path.dirname(__file__), '..', 'presets.json')
        with open(presets_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки пресетов: {e}")
        return {}


def get_presets():
    presets = load_presets()
    return [{"preset": name} for name in presets.keys()]


def get_clicker_cfg_table(preset_name):
    presets = load_presets()
    urls = presets.get(preset_name, [])

    config = []
    for i, item in enumerate(urls):
        # Поддержка старого (просто URL) и нового формата (словарь)
        if isinstance(item, dict):
            config.append({
                "window_name": i + 1,
                "preset": preset_name,
                "task": "url",
                "refresh": 30,
                "window_position": "standard",
                "filter": item['url'],
                "auth_type": item.get('auth_type')
            })
        else:
            # Старый формат (просто URL строка)
            config.append({
                "window_name": i + 1,
                "preset": preset_name,
                "task": "url",
                "refresh": 30,
                "window_position": "standard",
                "filter": item,
                "auth_type": None
            })
    return config

# Заглушки
def get_clicker_filters():
    return []


def get_grafana_urls():
    return []