import secrets
import string
from typing import Iterator

AVAILABLE_CHARS: str = string.ascii_letters + string.digits
SURL_SIZE: int = 7


def generate_surl() -> Iterator[str]:
    surl: str = "".join(
        secrets.choice(AVAILABLE_CHARS) for _ in range(SURL_SIZE)
    )
    yield surl
