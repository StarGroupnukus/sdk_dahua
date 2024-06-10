import logging
import mimetypes
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def setup_logger(name, log_file, level=logging.DEBUG):
    """Настройка и создание логгера с заданными параметрами."""
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Файловый обработчик с фильтром
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Создаем и настраиваем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Уровень DEBUG для сбора всех сообщений
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


os.makedirs('logs', exist_ok=True)
logger = setup_logger("flog", "logs/flog.log")


def send_report(id, file_paths, time, score, status, flogger=logger):
    url = os.getenv('SEND_API')
    data = {
        "camera_id": '31',
        "child_id": str(id),
        "score": str(score),
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
    }
    files_data = []

    try:
        for file_path in file_paths:
            if os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                mime_type, _ = mimetypes.guess_type(file_name)
                files_data.append(
                    ("images[]", (file_name, open(file_path, "rb"), mime_type))
                )
            else:
                flogger.error(f"Файл {file_path} не существует.")

        files = tuple(files_data)
        with requests.post(
                url, data=data, files=files, headers={"Accept": "application/json"}, timeout=10
        ) as response:
            flogger.info(response.status_code)
            if response.status_code != 200:
                flogger.info('sent')
    except Exception as e:

        flogger.error(e)
    finally:
        for _, (filename, file, _) in files_data:
            file.close()
