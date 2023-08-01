import requests
from config import config
import json
import sys
import uuid

def get_unique_transaction_id():
    """
    Get a unique transaction ID for API requests

    https://spec.matrix.org/v1.6/client-server-api/#transaction-identifiers
    """
    # a simpler counter is recommended, but we'd need somewhere to store the counter
    return str(uuid.uuid4())


def api_query(method: str, path: str, body=None, params=None, user_id=None, timestamp=None):
    """
    Make a query to the REST API with given method and path (must begin with /).

    Allows overriding the username and timestamp using the client-server API
    extensions for application services.

    Returns a tuple with response (JSON) and status code
    """
    # As we learned in 6.101, Python initializes default parameters only ONCE
    # so setting a default param to {} may cause aliasing errors if mutating it
    if params is None:
        params = {}
    if body is None:
        body = {}

    if not path.startswith('/'):
        raise ValueError(f'path should start with /')

    if user_id is not None:
        params |= {'user_id': user_id}
    if timestamp is not None:
        params |= {'ts': timestamp}

    response = requests.request(
        method=method,
        url=config.homeserver_url + path,
        params=params,
        json=body,
        headers={
            'Authorization': f'Bearer {config.as_token}'
        },
    )

    # TODO: this may throw an error if not JSON
    response_content = response.content.decode()
    try:
        return json.loads(response_content), response.status_code
    except json.JSONDecodeError:
        print(f"Query {path} returned invalid JSON: {response_content}", file=sys.stderr)
        return {'response': response_content}, response.status_code
    

def get_state_event(room_id, event_type, state_key='') -> dict:
    """
    Returns the state event with given characteristics, or none if not found
    """
    # Resolve alias first, if necessary
    if room_id.startswith('#'):
        room_id = get_room_id(room_id)

    response, code = api_query('GET', f'/_matrix/client/v3/rooms/{room_id}/state/{event_type}/{state_key}')
    if code != 200:
        return None
    return response


def get_room_alias(room_id) -> str:
    """
    Gets the canonical alias of the given room
    """
    state = get_state_event(room_id, 'm.room.canonical_alias', '')
    if state:
        return state['alias']


def get_room_id(room_alias: str) -> str:
    """
    Inverse of get_room_alias: given a room alias, return the room ID

    Returns None if alias does not exist
    """
    # Do some (relevant) URL encoding
    room_alias_encoded = room_alias \
        .replace('/', '%2F') \
        .replace('#', '%23') \
        .replace(':', '%3A')

    response, code = api_query('GET', f'/_matrix/client/v3/directory/room/{room_alias_encoded}')
    if code == 404:
        return None
    elif code == 200:
        return response['room_id']
    else:
        # TODO: it does seem to struggle with slashes
        print(f"ERROR WHILE TRYING TO GET ROOM ID FOR {room_alias}:", response)


def get_room_display_name(room_id, user_id) -> str | None:
    """
    Gets the display name of the given user in the given room
    """
    # Resolve alias first, if necessary
    if room_id.startswith('#'):
        room_id = get_room_id(room_id)

    state = get_state_event(room_id, 'm.room.member', user_id)
    if state:
        return state.get('displayname')


def set_room_display_name(room_id, user_id, display_name):
    """
    Sets the display name of the given user in the given room
    """
    # send m.room.member state event, idk which one - refer to spec
    raise NotImplementedError('setting room display name not implemented')


def get_global_display_name(user_id) -> str | None:
    """
    Gets the display name of the given user,joining globally
    or None if can't find
    """
    # Some kerbs have slashes on them
    user_id_encoded = user_id.replace('/', '%2F')

    response, code = api_query('GET', f'/_matrix/client/v3/profile/{user_id_encoded}/displayname')
    if code != 200:
        print(f"Error while getting display name for {user_id}: {response}", file=sys.stderr)
    return response.get('displayname')


def set_global_display_name(user_id, display_name) -> bool:
    """
    Sets the displayname of the given user,
    returns True/False depending on success
    """
    # Some kerbs have slashes on them
    user_id_encoded = user_id.replace('/', '%2F')

    response, code = api_query('PUT', f'/_matrix/client/v3/profile/{user_id_encoded}/displayname', {'displayname': display_name}, user_id=user_id)
    if code != 200:
        print(f"Error while setting display name for {user_id}: {response}", file=sys.stderr)
    return code == 200


def join_room(room_id: str, user_id: str) -> bool:
    """
    Joins user to room
    """
    # Resolve alias first, if necessary
    # TODO: this can be a decorator to avoid duplication
    if room_id.startswith('#'):
        room_id = get_room_id(room_id)
    
    # TODO: it would be one less API call to use https://spec.matrix.org/latest/client-server-api/#post_matrixclientv3joinroomidoralias

    response, code = api_query('POST', f'/_matrix/client/v3/rooms/{room_id}/join', user_id=user_id)
    if code != 200:
        print(f"Error while joining {user_id} to {room_id}: {response}", file=sys.stderr)
    return code == 200


def send_text_message(room_id, user_id, message, additional_metadata, timestamp):
    """
    Send a simple text message to the given room
    """
    # Resolve alias first, if necessary
    if room_id.startswith('#'):
        room_id = get_room_id(room_id)

    body = {
        'body': message,
        'msgtype': 'm.text',
    }
    body |= additional_metadata
    
    # TODO: extract into a function to send events in general
    response, code = api_query(
        'PUT',
        f'/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{get_unique_transaction_id()}',
        user_id=user_id,
        body=body,
        timestamp=timestamp,
    )
    if code != 200:
        print(f"Error while sending message from {user_id} to {room_id}: {response}", file=sys.stderr)
    return code == 200


def create_room(alias_localpart = None, name = None, preset = None, **kwargs) -> str | None:
    """
    Creates a room, and returns the room ID of the newly created room

    https://matrix.org/docs/api/#post-/_matrix/client/v3/createRoom
    """
    # TODO: add the rest of the parameters (for now, adding as-needed)
    
    body = {}
    if name:
        body |= {'name': name}
    if alias_localpart:
        body |= {'room_alias_name': alias_localpart}
    # TODO: ideally use an enum
    if preset:
        body |= {'preset': preset}

    body |= kwargs

    response, code = api_query('POST', '/_matrix/client/v3/createRoom', body)
    if code == 200:
        return response['room_id']
    else:
        print(f"COULD NOT CREATE ROOM {alias_localpart}: {response}", file=sys.stderr)


def create_user(username):
    """
    Creates a user, returning True if successful or user already exists
    """
    response, code = api_query('POST', '/_matrix/client/v3/register', {
        'type': 'm.login.application_service',
        'username': username,
        'inhibit_login': True,
    })
    if code == 200:
        return True # successfully created
    elif response.get('errcode') == 'M_USER_IN_USE':
        return True # already exists!
    else:
        print(f"COULD NOT CREATE USER {username}: {response}")
        return False
