import requests
from config import config
import json

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
    return get_state_event(room_id, 'm.room.canonical_alias', '')['alias']


def get_display_name(room_id, user_id) -> str | None:
    """
    Gets the display name of the given user in the given room
    """
    return get_state_event(room_id, 'm.room.member', user_id).get('displayname')