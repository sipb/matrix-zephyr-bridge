from config import config
import sys
import matrix
import zephyr
from constants import *

def get_zephyr_localpart(cls, instance):
    """
    Gets the localpart to use for the room with given Zephyr class and instance
    """
    return f'{config.zephyr_room_prefix}{cls}{config.class_instance_separator}{instance}'


def create_zephyr_room_if_needed(cls, instance):
    """
    Create a Matrix room corresponding to the given Zephyr class and instance
    (or do nothing if it already exists). 

    Also, subscribe on the Zephyr side to the given class and instance

    Returns the room ID of the new (or existing) room (or None)
    """
    alias_localpart = get_zephyr_localpart(cls, instance)
    id_if_already_exists = matrix.get_room_id(f'#{alias_localpart}:{config.homeserver}')
    if id_if_already_exists:
        return id_if_already_exists
    
    # TODO: subscribe using zephyr_client.py
    # But how can we communicate to the other process to update its subscriptions?
    # "Message passing": we'll find out good design ways in 6.102!
    # A hacky way would be to kill the other half, update the file then restart it
    # (good enough ONLY for testing purposes: Ctrl+C then re run)
    # https://pymotw.com/2/multiprocessing/communication.html ??!~
    # https://github.com/gorakhargosh/watchdog#example-api-usaget
    # other things: sockets, or simply literally refreshing the subscriptions file every 5 minutes?

    # TODO: tweak room options for good user experience (history visibility, public, do we want federation? etc)
    return matrix.create_room(
        alias_localpart=alias_localpart,
        name=f'-c {cls} -i {instance}', # TODO: use a friendlier name
        preset='public_chat',
    )


def extract_mxid(mxid: str):
    """
    Given an MXID, return a tuple containing the localpart
    and homeserver
    """
    array = mxid[1:].split(':')
    assert len(array) == 2, 'MXID must have one (and only one) colon'
    return tuple(array)


def get_zephyr_user(mxid: str):
    """
    Given a Matrix user, return the corresponding Zephyr user
    """
    user_localpart, user_homeserver = extract_mxid(mxid)
    
    # Local users will use the default realm (ATHENA.MIT.EDU)
    if user_homeserver == config.homeserver:
        return f'{user_localpart}@{DEFAULT_REALM}'
    
    # Otherwise, just keep the mxid unchanged, since
    # that does not mislead or let people impersonate MIT users by
    # using accounts on other homeservers (at least from our bridge,
    # coming from our hostname)
    return mxid


def get_zephyr_location(mxid: str) -> tuple[str] | bool:
    """
    Get Zephyr class and instance for the given Matrix
    room ID, or False if not found

    Behavior is currently hardcoded to parsing the format
    #z/classname/instancename (with prefix and separator in config)
    """
    # Resolve canonical ID
    if mxid.startswith('!'):
        mxid = matrix.get_room_alias(mxid)
    # Could not find canonical ID
    if mxid is None:
        return False
    
    if mxid.startswith('#' + config.zephyr_room_prefix):
        localpart, homeserver = extract_mxid(mxid)
        if homeserver != config.homeserver:
            print(f"Unknown homeserver {homeserver}, skipping", file=sys.stderr)
            return False
        array = localpart[len(config.zephyr_room_prefix):].split(config.class_instance_separator)
        if len(array) != 2:
            print(f"Room {localpart} has extra slash, skipping", file=sys.stderr)
        return tuple(array)
    else:
        print(f"Unknown zephyr triplet for {mxid}", file=sys.stderr)
        return False


def strip_default_realm(user: str):
    """
    If `user` ends with ATHENA.MIT.EDU, remove it
    """
    if user.endswith(DEFAULT_REALM):
        return user[:-len(DEFAULT_REALM)-1]
    else:
        return user
