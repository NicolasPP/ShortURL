from configparser import ConfigParser, SectionProxy
from pathlib import Path
from typing import Any, NamedTuple, Optional, Self, Type, get_type_hints


class ConfigManager:
    _config: Optional[Self] = None

    @classmethod
    def get(cls) -> Self:
        if ConfigManager._config is None:
            ConfigManager._config = cls()

        return ConfigManager._config

    def __init__(self) -> None:
        self._parser: ConfigParser = ConfigParser()
        self._params: dict[str, NamedTuple] = {}
        self._loaded: bool = False

    def load(self, file_dir: str) -> None:
        if not (path := Path(file_dir).absolute()).exists():
            raise ValueError(f"Config file dir: {file_dir} does not exists")

        if path.suffix != ".ini":
            raise ValueError(f"Expected .ini file got {path.absolute()}")

        if not self._parser.read(path):
            raise Exception(f"Could not load {path.absolute()}")

        self._loaded = True

    def get_params[T: NamedTuple](self, section_name: str, param_type: Type[T]) -> T:
        if not self._loaded:
            raise Exception("config file has not been loaded")

        if section_name in self._params:
            return self._params[section_name]

        if not self._parser.has_section(section_name):
            raise ValueError(f"Expected [{section_name}] section in config file")

        section: SectionProxy = self._parser[section_name]
        values: dict[str, Any] = {}
        for name, type_ in get_type_hints(param_type).items():
            if (val := section.get(name)) is None:
                raise ValueError(f"Expected {name} option inside [{section_name}] section in .ini file")

            values[name] = type_(val)

        self._params[section_name] = (params := param_type(**values))
        return params


POSTGRES_SECTION: str = "POSTGRESS"


class PostgresParams(NamedTuple):
    password: str
    user_name: str
    database_name: str
    port: int
    host: str


def get_postgres_params() -> PostgresParams:
    return ConfigManager.get().get_params(POSTGRES_SECTION, PostgresParams)
