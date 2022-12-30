import logging

import src.globals as g
from src import Bot
from src.models import Settings


def main():
    g.settings = Settings()  # type: ignore

    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    if g.settings.runner_debug:
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=FORMAT)

    logging.info(f"当前配置: {g.settings.json()}")

    if not g.settings.input_token.get_secret_value():
        logging.info("无法获得 Token，跳过此次操作")
        return

    bot = Bot()
    bot.run()


if __name__ == "__main__":
    main()
