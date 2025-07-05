import configparser
import os


def get_item_from_config(item):
    _config = configparser.RawConfigParser()
    _config.read(os.path.join(os.getcwd(), 'SAM.cfg'), encoding="utf-8")
    try:
        return dict(_config.items(item))
    except Exception as e:
        print(os.getcwd())
        print(e)
        return dict()


if __name__ == '__main__':
    pass
