from logging import Logger, getLogger

from short_url.config_manager import ConfigManager

CONFIG_FILE: str = r"config.ini"


def main() -> None:
    _log: Logger = getLogger("ShortUrlApi")


if __name__ == "__main__":
    ConfigManager.get().load(CONFIG_FILE)
    main()
