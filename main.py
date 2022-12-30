import logging

from src import Bot
from src.models import Settings


def main():
    settings = Settings()  # type: ignore

    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    if settings.runner_debug:
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=FORMAT)

    logging.info(f"当前配置: {settings.json()}")

    if not settings.input_token.get_secret_value():
        logging.info("无法获得 Token，跳过此次操作")
        return

    bot = Bot(settings)

    bot.run()


if __name__ == "__main__":
    main()
