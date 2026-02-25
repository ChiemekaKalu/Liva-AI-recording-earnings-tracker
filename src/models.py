from dataclasses import dataclass, field    
from sortedcontainers import SortedKeyList
from typing import Literal

@dataclass
class UserInterval:
    start_time: int
    end_time: int
    recording_id: str

@dataclass
class EarningsEntry:
    recording_id: str
    amount_cents: int 
    reversed: bool = False

def _make_interval_list():
    return SortedKeyList(key=lambda x: x.start_time)


@dataclass
class User:
    id: str
    balance_cents: int = 0
    earnings_log: list = field(default_factory=list)
    intervals: SortedKeyList = field(default_factory=_make_interval_list)

@dataclass
class Recording:
    id: str
    start_time: int
    end_time: int
    participants: list[str]
    status: Literal["active", "ended"] = "active"

    