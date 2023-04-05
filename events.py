# Postponed evaluation of annotations (https://stackoverflow.com/questions/33837918/type-hints-solve-circular-dependency)
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ClientEvent:
    content: dict
    event_id: str
    origin_server_ts: int
    room_id: str
    sender: str
    type: str
    state_key: Optional[str] = None
    unsigned: Optional[UnsignedData] = None


@dataclass_json
@dataclass
class UnsignedData:
    age: Optional[int] = None
    prev_content: Optional[dict] = None
    redacted_because: Optional[ClientEvent] = None
    transaction_id: Optional[str] = None
