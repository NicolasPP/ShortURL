from short_url.config_manager import ConfigManager
from traffic_simulation import run_simulation

CONFIG_FILE: str = r"config.ini"
if __name__ == "__main__":
    ConfigManager.get().load(CONFIG_FILE)
    run_simulation()
