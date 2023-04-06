import requests
from config import config
import json
import sys

def api_query(method: str, path: str, params={}, body={}, user_id=None):
    """
    Make a query to the REST API with given method and path (must begin with /).

    Allows overriding the username using the client-server API extension
    for application services.

    Returns a tuple with response (JSON) and status code
    """
    if not path.startswith('/'):
        raise ValueError(f'path should start with /')

    if user_id is not None:
        params |= {'user_id': user_id}

    response = requests.request(
        method=method,
        url=config.homeserver_url + path,
        params=params,
        json=body,
        headers={
            'Authorization': f'Bearer {config.as_token}'
        }
    )

    # TODO: this may throw an error if not JSON
    return json.loads(response.content.decode()), response.status_code
    

def get_state_event(room_id, event_type, state_key='') -> dict:
    """
    Returns the state event with given characteristics, or none if not found
    """
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


def get_room_id(room_alias) -> str:
    """
    Inverse of get_room_alias: given a room alias, return the room ID

    Returns None if alias does not exist
    """
    response, code = api_query('GET', f'/_matrix/client/v3/directory/room/{room_alias}')
    if code == 404:
        return None
    elif code == 200:
        return response['room_id']
    else:
        print(f"ERROR WHILE TRYING TO GET ROOM ID FOR {room_alias}:", response)


def get_display_name(room_id, user_id) -> str | None:
    """
    Gets the display name of the given user in the given room
    """
    state = get_state_event(room_id, 'm.room.member', user_id)
    if state:
        return state.get('displayname')
    

def create_room(alias_localpart = None, name = None, preset = None):
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

    response, code = api_query('POST', '/_matrix/client/v3/createRoom', body)
    if code == 200:
        return response['room_id']
    else:
        print(f"COULD NOT CREATE ROOM {alias_localpart}: {response}", file=sys.stderr)