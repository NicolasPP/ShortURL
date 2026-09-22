import concurrent.futures
import time
from decimal import Decimal
from logging import Formatter, INFO, Logger, StreamHandler, getLogger

from sqlalchemy import text

from short_url.config_manager import ConfigManager
from short_url.database_manager import DatabaseManager
from short_url.models import Url, User
from short_url.repositories import SurlRepository, UrlRepository, UserRepository
from short_url.unit_of_work import UnitOfWork

EMAIL: str = "user@email.com"
URL: str = "https://example.com/long-page"
BALANCE: str = "5.00"
CONFIG_FILE: str = r"config.ini"
CLEAN_USERS: text = text("DELETE FROM short_url.users WHERE email = :email")
CLEAN_URLS: text = text("DELETE FROM short_url.url WHERE original_url = :url")


def setup_data(uow: UnitOfWork) -> None:
    with uow.transaction() as session:
        users: UserRepository = UserRepository(session)
        urls: UrlRepository = UrlRepository(session)

        user: User = users.add(EMAIL).value
        user.balance = Decimal(BALANCE)
        assert not urls.add(URL).failed, "Expected get url not to fail"
        session.commit()


def add_surl_worker(database: DatabaseManager, request_id: int, fixed: bool, log: Logger) -> None:
    uow: UnitOfWork = UnitOfWork(database)
    with uow.transaction() as session:
        users: UserRepository = UserRepository(session)
        urls: UrlRepository = UrlRepository(session)

        user: User = users.get(EMAIL, fixed).value
        url: Url = urls.get(URL).value

        time.sleep(0.1)

        surls: SurlRepository = SurlRepository(session)
        if (surl := surls.add(url=url, user=user)).failed:
            log.error("Request %s: FAILED -> %s", request_id, surl.reason)
        else:
            log.info("Request %s: SUCCESS -> Created surl %s", request_id, surl.value.surl)


def simulate_race_condition(log: Logger, fixed: bool) -> None:
    log.info("--- STARTING RACE CONDITION DEMO ---")
    log.info("Initial balance for %s: $5.00", EMAIL)
    log.info("Launching 2 concurrent requests to mint SURLs simultaneously...")

    database: DatabaseManager = DatabaseManager.production()
    uow: UnitOfWork = UnitOfWork(database)
    clean_data(uow)
    setup_data(uow)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(add_surl_worker, database, 1, fixed, log),
            executor.submit(add_surl_worker, database, 2, fixed, log)
        ]
        concurrent.futures.wait(futures)

    with uow.transaction() as session:
        user = UserRepository(session).get(EMAIL).value
        log.info("--- FINAL STATE ---")
        log.info(f"Final User Balance: $%s", user.balance)
        log.info(f"Total SURLs created for user: %s", len(user.surls))


def clean_data(uow: UnitOfWork) -> None:
    with uow.transaction() as session:
        session.execute(CLEAN_USERS, {"email": EMAIL})
        session.execute(CLEAN_URLS, {"url": URL})


def setup_logger(name: str) -> Logger:
    log: Logger = getLogger(name)
    log.setLevel(INFO)
    handler: StreamHandler = StreamHandler()
    handler.setFormatter(Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(handler)
    return log


def run_simulation(fixed: bool = False) -> None:
    ConfigManager.get().load(CONFIG_FILE)
    log: Logger = setup_logger("RaceSim")
    simulate_race_condition(log, fixed)
