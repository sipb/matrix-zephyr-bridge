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
    state_key: Optional[str] = None
    type: str
    unsigned: UnsignedData


@dataclass_json
@dataclass
class UnsignedData:
    age: int
    prev_content: dict
    redacted_because: ClientEvent
    transaction_id: str
