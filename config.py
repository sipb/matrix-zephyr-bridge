import yaml
from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Config:
    # Token used by the homeserver to communicate with the appservice
    hs_token: str

    # Token that the appservice uses to communicate with the homeserver
    as_token: str

    # The homeserver (right part of MXIDs)
    homeserver: str

    # Homeserver URL, where you can actually reach the Matrix REST API
    homeserver_url: str

    # Address for REST API
    listen_address: str

    # Port for REST API
    listen_port: str

    # URL for the Matrix homeserver to connect to the appservice
    url: str

    # Naming conventions / prefixes to claim
    zephyr_user_prefix: Optional[str] = "_zephyr_"
    zephyr_space_prefix: Optional[str] = "Z/" 
    zephyr_room_prefix: Optional[str] = "z/" 
    class_instance_separator: Optional[str] = "/"

    # Tell the homeserver that this appservice bridges the "zephyr" protocol
    enable_thirdparty_reporting: Optional[bool] = False

    # Bot localpart/username
    username: Optional[str] = "zephyrbot"

    # Blocked opcodes for Zephyr
    # (this was going to be blocked hosts but it seems very hard to implement)
    blocked_opcodes: Optional[tuple[str]] = ("matrix",)

    # Media shortened prefix
    media_base_url: Optional[str] = None

    # Block MXIDs from being bridged to Zephyr
    # To prevent double-bridging messages from Mattermost bridge
    blocked_mxid_prefixes: Optional[tuple[str]] = ("mattermost", "_mattermost_")

    # Block certain Zephyr usernames from being bridged to Matrix
    blocked_zephyr_usernames: Optional[tuple[str]] = ("mattermost", "matrix")


config: Config = Config.from_dict(yaml.load(open("config.yaml", "r"), yaml.Loader))

