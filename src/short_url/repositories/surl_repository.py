from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import ClassVar, Iterator, Optional

from sqlalchemy import Select
from sqlalchemy.exc import DBAPIError, IntegrityError

from short_url.models import Surl, SurlStatus, Url, User
from short_url.repositories.repository import Repository
from short_url.repositories.result import Result
from short_url.surl_generator import generate_surl

MAX_SURL_RETRIES: int = 5
SURL_FAILED_TO_GENERATE_ERR: str = f"Could not create SURL after {MAX_SURL_RETRIES} attempts"

SURL_COST: Decimal = Decimal("5.00")
INSUFFICIENT_BALANCE_ERR: str = "Insufficient funds: Balance is {user_balance:.2f}, required {surl_cost:.2f}"


@dataclass(slots=True, frozen=True)
class SurlRepository(Repository):
    _surl_generator: ClassVar[Iterator[str]] = generate_surl()

    def add(self, url: Url, user: User, gen: Optional[Iterator[str]] = None) -> Result[Surl]:
        if user.balance < SURL_COST:
            return Result.failure(INSUFFICIENT_BALANCE_ERR.format(
                user_balance=user.balance,
                surl_cost=SURL_COST
            ))

        expiry_duration: timedelta = timedelta(days=30)
        gen = gen or SurlRepository._surl_generator

        for _ in range(MAX_SURL_RETRIES):
            surl_code: str = next(gen)
            created_at: datetime = datetime.now(timezone.utc)

            surl: Surl = Surl(
                surl=surl_code,
                user_id=user.id,
                url_hash=url.url_hash,
                status=SurlStatus.ACTIVE,
                created_at=created_at,
                expires_at=created_at + expiry_duration,
            )

            try:
                with self._session.begin_nested():
                    user.balance -= SURL_COST
                    self._session.add(surl)
                    self._session.flush()
                    return Result.success(surl)

            except IntegrityError:
                continue

            except DBAPIError as err:
                return Result.failure(str(err))

        return Result.failure(SURL_FAILED_TO_GENERATE_ERR)

    def get(self, surl_code: str) -> Result[Surl]:
        try:
            query: Select[tuple[Surl]] = Select(Surl) \
                .where(Surl.surl == surl_code) \
                .where(Surl.status == SurlStatus.ACTIVE)
            if (surl := self._session.scalar(query)) is None:
                return Result.failure(f"Could not find active surl: {surl_code}")

            return Result.success(surl)

        except DBAPIError as err:
            return Result.failure(str(err))
