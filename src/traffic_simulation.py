import concurrent.futures
import random
import time
from decimal import Decimal
from logging import Formatter, INFO, Logger, StreamHandler, getLogger

from sqlalchemy import delete

from short_url.app import App
from short_url.databases import Postgres, RedisDatabase
from short_url.models import Surl, Url, User
from short_url.repositories import Result
from short_url.unit_of_work import PostgresUnitOfWork, RedisUnitOfWork

USER_COUNT: int = 10
URL_PER_USER: int = 5
USER_BALANCE: Decimal = Decimal("1000.00")
USER_EMAIL: str = "user_{index}@email.com"
USER_URL: str = "https://example.com/user={user_index}/url={url_index}"
TOTAL_REQUESTS: int = 1000
CONCURRENT_WORKERS: int = 10


def clean(postgres_work: PostgresUnitOfWork, log: Logger) -> None:

    with postgres_work.transaction() as api:
        api.session.execute(delete(Surl))
        api.session.execute(delete(Url))
        api.session.execute(delete(User))

        log.info("Successfully cleaned all Postgres tables.")


def clean_redis(redis_db: RedisDatabase, log: Logger) -> None:
    with redis_db.get_client() as client:
        for key in client.keys("ShortUrl*"):
            client.delete(key)

    log.info("Successfully cleaned redis")


def populate(postgres_work: PostgresUnitOfWork, redis_work: RedisUnitOfWork, log: Logger) -> list[str]:
    surls: list[str] = []
    for user_index in range(USER_COUNT):

        with postgres_work.transaction() as api:
            user_result: Result[User] = api.users.add(
                USER_EMAIL.format(index=user_index)
            )

            if user_result.failed:
                log.warning("Failed to create user %s because: %s", user_index, user_result.reason)
                continue

            log.info("Added user %s", user_index)

            user: User = user_result.value
            user.balance = USER_BALANCE

            for url_index in range(URL_PER_USER):
                raw_url: str = USER_URL.format(
                    user_index=user_index,
                    url_index=url_index
                )

                if (url_result := api.urls.add(raw_url)).failed:
                    log.warning("Failed to add url: %s because: %s",
                                raw_url, url_result.reason)
                    continue

                url: Url = url_result.value
                if (surl_result := api.surls.add(url, user)).failed:
                    log.warning("Failed to add surl for url: %s because: %s",
                                raw_url, surl_result.reason)
                    continue

                surl: Surl = surl_result.value
                log.info("Added surl: %s to url: %s", surl.surl, url.original_url)
                surls.append(surl.surl)

                with redis_work.transaction() as client:
                    client.surls.add(surl.surl, url.original_url)

    return surls


def simulate_traffic(
    postgres: Postgres,
    redis: RedisDatabase,
    surls: list[str],
    log: Logger
) -> None:
    log.info("Starting traffic simulation: %s requests across %s workers...",
             f"{TOTAL_REQUESTS:,}", CONCURRENT_WORKERS)

    requests_per_worker: int = TOTAL_REQUESTS // CONCURRENT_WORKERS

    def worker_task(num_requests: int) -> tuple[int, int]:
        # Each worker thread gets its own Unit of Work & App instances to avoid shared state errors
        postgres_work = PostgresUnitOfWork(postgres)
        redis_work = RedisUnitOfWork(redis)
        local_app = App(_postgres=postgres_work, _redis=redis_work)

        success_count: int = 0
        failure_count: int = 0

        for _ in range(num_requests):
            surl_code: str = random.choice(surls)
            result: Result[str] = local_app.resolve_surl(surl_code)

            if result.failed:
                failure_count += 1
            else:
                success_count += 1

        return success_count, failure_count

    start_time: float = time.perf_counter()
    total_successes: int = 0
    total_failures: int = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [
            executor.submit(worker_task, requests_per_worker)
            for _ in range(CONCURRENT_WORKERS)
        ]

        for future in concurrent.futures.as_completed(futures):
            successes, failures = future.result()
            total_successes += successes
            total_failures += failures

    elapsed_time: float = time.perf_counter() - start_time
    rps: float = TOTAL_REQUESTS / elapsed_time if elapsed_time > 0 else 0.0
    avg_latency_ms: float = (elapsed_time / TOTAL_REQUESTS) * 1000

    log.info("=" * 50)
    log.info("TRAFFIC SIMULATION COMPLETED")
    log.info("Total Requests : %s", f"{TOTAL_REQUESTS:,}")
    log.info("Success Hits   : %s", f"{total_successes:,}")
    log.info("Failure Hits   : %s", f"{total_failures:,}")
    log.info("Execution Time : %.3f seconds", elapsed_time)
    log.info("Throughput     : %.2f req/sec", rps)
    log.info("Avg Latency    : %.3f ms/req", avg_latency_ms)
    log.info("=" * 50)


def setup_logger(name: str) -> Logger:
    log: Logger = getLogger(name)
    log.setLevel(INFO)
    handler: StreamHandler = StreamHandler()
    handler.setFormatter(Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(handler)
    return log


def run_simulation() -> None:
    log: Logger = setup_logger("TrafficSim")

    postgres: Postgres = Postgres.production()
    redis: RedisDatabase = RedisDatabase.production()

    postgres_work: PostgresUnitOfWork = PostgresUnitOfWork(postgres)
    redis_work: RedisUnitOfWork = RedisUnitOfWork(redis)

    app: App = App(_postgres=postgres_work, _redis=redis_work)

    clean(postgres_work, log)
    clean_redis(redis, log)

    surls: list[str] = populate(postgres_work, redis_work, log)
    simulate_traffic(postgres, redis, surls, log)
