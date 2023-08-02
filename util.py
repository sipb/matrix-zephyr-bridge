from config import config
import sys
import matrix
from zephyr_client import Zephyr
from constants import *
import dns.resolver

def is_reasonable_signature(user, signature):
    """
    Whether the user's signature is reasonable to use as a display name
    """

    # This is a mere heuristic, which can be adapted to be made more useful

    def canonicalize_name(name):
        return [item for item in name.lower().replace('.', '').replace('-', ' ').split(' ') if len(item) > 1]

    def names_similar(name1, name2):
        name1 = canonicalize_name(name1)
        name2 = canonicalize_name(name2)
        return any(word1 == word2 for word1 in name1 for word2 in name2)

    def get_hesiod_entries(type, name):
        try:
            answers = dns.resolver.resolve(f'{name}.{type}.ns.athena.mit.edu', 'TXT')
            # it starts and ends with quotes, remove them
            return [str(answer)[1:-1] for answer in answers]
        except dns.resolver.NXDOMAIN:
            return []

    # IMPORTANT NOTE: This name should NOT be displayed. While we can trust cruft who
    # are familiar with Athena to keep their finger name updated, it may have the wrong
    # name for other people
    # (Change your name here: https://web.mit.edu/rgabriel/names/
    # or with `chfn.moira` on Athena)
    def get_hesiod_name(user):
        try:
            results = get_hesiod_entries('passwd', user)
            # zephyr.py in zulip
            return results[0].split(':')[4].split(',')[0].strip()
        except:
            # If it does not work for any reason, we don't want the bridge to fail
            return ''

    return names_similar(signature, get_hesiod_name(user))


def get_zephyr_localpart(cls, instance):
    """
    Gets the localpart to use for the room with given Zephyr class and instance
    """

    # Ensure we use lowercase
    cls = cls.lower()
    instance = instance.lower()

    return f'{config.zephyr_room_prefix}{cls}{config.class_instance_separator}{instance}'


def create_zephyr_room(cls, instance):
    """
    Create a Matrix room corresponding to the given Zephyr class and instance
    (or do nothing if it already exists). 

    Also, subscribe on the Zephyr side to the given class and instance

    Returns the room ID of the new (or existing) room (or None)
    """
    alias_localpart = get_zephyr_localpart(cls, instance)

    # Subscribe to the room
    # (ab)use command capability of the other half of the bridge
    # TODO: switch to sqlite if sqlite is needed for something else in here
    # (sqlite allows multiple people writing the database at once and listening for changes)
    Zephyr.send_message(f"add {cls} {instance} *", opcode=DEFAULT_OPCODE, recipient=OWN_KERB)

    # TODO: tweak room options for good user experience (history visibility, public, do we want federation? etc)

    # IMPORTANT: don't allow people remove aliases! that breaks the bot - power levels

    # For instance you can set "who can read history?" to "everyone" instead of "members, all messages" (current)
    # or to members, but only history since joining (which would reflect the zephyr behavior), but the point
    # is also what is the best? as opposed to respecting the way zephyr works 1:1
    # Well, I think that having to join is a reasonable compromise
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
    
    # Otherwise, change the format so the homeserver simulates
    # a realm
    return '@'.join(mxid[1:].split(':', maxsplit=1))


def get_zephyr_location(mxid: str) -> tuple[str] | bool:
    """
    Get Zephyr class and instance for the given Matrix
    room ID, or False if not found
    """
    # Resolve canonical ID
    if mxid.startswith('!'):
        # TODO: query all aliases, not just the canonical one
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


def timestamp_matrix_to_zephyr(matrix_ts):
    """
    Convert a Matrix timestamp to a Zephyr timestamp
    (milliseconds to seconds)
    """
    return matrix_ts / 1000


def timestamp_zephyr_to_matrix(zephyr_ts):
    """
    Convert a Zephyr timestamp to a Matrix timestamp
    (seconds to milliseconds)
    """
    return round(zephyr_ts * 1000)


def mxc_to_url(mxc_uri):
    homeserver, media_id = mxc_uri.split('/')[2:]
    if config.media_base_url and homeserver == config.homeserver:
        return config.media_base_url + media_id
    else:
        return f'{config.homeserver_url}/_matrix/media/v3/download/{homeserver}/{media_id}'
