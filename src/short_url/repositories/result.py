from dataclasses import dataclass
from typing import Optional, Self


@dataclass(slots=True, frozen=True)
class Result[T]:

    @classmethod
    def success(cls, value: T) -> Self:
        return cls(value, "")

    @classmethod
    def failure(cls, reason: str) -> Self:
        return cls(None, reason)

    _value: Optional[T]
    reason: str

    @property
    def failed(self) -> bool:
        return self._value is None

    @property
    def value(self) -> T:
        assert self._value is not None
        return self._value
