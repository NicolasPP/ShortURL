from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func
from sqlalchemy.exc import DBAPIError, IntegrityError

from short_url.models import Click, Surl
from short_url.repositories.repository import PostgresRepository
from short_url.repositories.result import Result


@dataclass(slots=True, frozen=True)
class PostgresClickRepository(PostgresRepository):
    def add(self, surl: Surl) -> Result[Click]:
        click: Click = Click(
            surl=surl.surl,
            clicked_at=datetime.now(timezone.utc)
        )

        try:
            self._session.add(click)
            self._session.flush()
            return Result.success(click)

        except (IntegrityError, DBAPIError) as err:
            return Result.failure(str(err))

    def get_count(self, surl: Surl) -> Result[int]:
        try:
            query: Select[tuple[int]] = Select(func.count(Click.id)) \
                .where(Click.surl == surl.surl)
            click_count: int = self._session.scalar(query) or 0
            return Result.success(click_count)

        except (IntegrityError, DBAPIError) as err:
            return Result.failure(str(err))

    def get_traffic(self, surl: Surl, window: timedelta) -> Result[float]:
        if (minutes := window.total_seconds() / 60.0) <= 0:
            return Result.failure("Time Window must be greater than 0")

        try:
            query: Select[tuple[int]] = Select(func.count(Click.id)) \
                .where(Click.surl == surl.surl) \
                .where(Click.clicked_at >= datetime.now(timezone.utc) - window)

            clicks: int = self._session.scalar(query) or 0
            return Result.success(clicks / minutes)

        except (IntegrityError, DBAPIError) as err:
            return Result.failure(str(err))
