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
    for i, url in enumerate(urls):
        config.append({
            "window_name": i + 1,
            "preset": preset_name,
            "task": "url",
            "refresh": 30,
            "window_position": "standard",
            "filter": url
        })
    return config

# Заглушки
def get_clicker_filters():
    return []


def get_grafana_urls():
    return []