from logging import Logger, getLogger

from api import Result, ShortUrlApi
from config_manager import ConfigManager
from models import User

CONFIG_FILE: str = r"config.ini"


def main() -> None:
    _log: Logger = getLogger("ShortUrlApi")
    api: ShortUrlApi = ShortUrlApi()
    user: Result[User] = api.add_user("add_user_test3@email.com")

    if user.failed:
        _log.error(user.reason)
        return

    print(user.value)


if __name__ == "__main__":
    ConfigManager.get().load(CONFIG_FILE)
    main()
