import yaml
from config import config

# https://spec.matrix.org/v1.6/application-service-api/#registration
registration = {
    "as_token": config.as_token,
    "hs_token": config.hs_token,
    "id": "zephyr",
    "namespaces": {
        "aliases": [
            {"exclusive": True, "regex": f"#{config.zephyr_room_prefix}.+:{config.homeserver}"},
            {"exclusive": True, "regex": f"#{config.zephyr_space_prefix}.+:{config.homeserver}"},
        ],
        "rooms": [],
        "users": [
            {"exclusive": True, "regex": f"@{config.zephyr_user_prefix}.+"},
        ],
    },
    "rate_limited": False,
    "sender_localpart": config.username,
    "url": config.url,
}

if config.enable_thirdparty_reporting:
    registration["protocols"] = ["zephyr"]

yaml.dump(registration, open("registration.yaml", "w"), yaml.Dumper)