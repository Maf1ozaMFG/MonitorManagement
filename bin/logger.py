from logging import getLogger, FileHandler, Formatter, INFO, DEBUG
import os


def create_logger(name):
    logger = getLogger(name)
    logger.setLevel(INFO)
    logger.setLevel(DEBUG)
    log_file_name = f"{name}.log"
    log_path = os.path.join(os.getcwd(), log_file_name)
    fh = FileHandler(log_path, encoding='utf8')
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


if __name__ == '__main__':
    pass
