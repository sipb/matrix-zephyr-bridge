from flask import Flask, request, Response
from decorators import *
from events import ClientEvent
from config import config
from util import get_zephyr_location, get_zephyr_user, create_zephyr_room, mxc_to_url, renew_kerberos_tickets
import sys
import matrix
from constants import *
from zephyr_client import Zephyr

renew_kerberos_tickets()

app = Flask(__name__)

# https://spec.matrix.org/v1.6/application-service-api/#put_matrixappv1transactionstxnid
@app.put('/transactions/<string:txn_id>')
@app.put('/_matrix/app/v1/transactions/<string:txn_id>')
@authenticated
# @idempotent # there is a specific order we want, (if someone runs an unauthenticated query, we don't want it logged as already fulfilled)
# To be fair, the bridge will run fine most of the time without needing this
def process_events(txn_id):
    print("processing event", txn_id)
    events: list[ClientEvent] = (ClientEvent.from_dict(event) for event in request.json["events"])
    for event in events:
        # Ignore our own messages!
        if event.sender.startswith('@' + config.zephyr_user_prefix):
            continue
        # Ignore banned usernames (for other bridges)
        for mxid_prefix in config.blocked_mxid_prefixes:
            if event.sender.startswith('@' + mxid_prefix):
                continue
        if event.type == 'm.room.message' or event.type == 'm.sticker':
            message_type = event.content.get('msgtype')
            zephyr_content = event.content['body']
            zephyr_location = get_zephyr_location(event.room_id)
            if not zephyr_location:
                print(f"Not bridging unknown event from {event.sender} in {event.room_id}", file=sys.stderr)
            
            # Handle "emotes"
            if message_type == 'm.emote':
                zephyr_content = '/me ' + zephyr_content
            # Handle media
            if event.type == 'm.sticker' or message_type in ('m.image', 'm.file', 'm.audio'):
                # Zulip likes the Markdown format and it should be readable enough for other clients
                # although (TODO: investigate) Zulip ignores our Markdown even if it has the same format
                # maybe here? https://github.com/zulip/zulip/blob/946b4e73ca6dbc34788b8799d9d8de04a2b17809/web/src/markdown.js#L99
                # Either way, I guess this is good enough
                zephyr_content = f"[{zephyr_content}]({mxc_to_url(event.content.get('url'))})"

            cls, instance = zephyr_location
            print(cls, instance, zephyr_content)
            Zephyr.send_message(
                message=zephyr_content, # TODO: handle formatting, m.emote, etc
                cls=cls,
                instance=instance,
                display_name=matrix.get_room_display_name(event.room_id, event.sender),
                sender=get_zephyr_user(event.sender),
            )
    return {}, 200


# https://spec.matrix.org/v1.6/application-service-api/#get_matrixappv1roomsroomalias
# Using separate methods because by default, slashes are part of the alias itself
# and Flask won't parse it otherwise
zephyr_class_instance_mxid = f'#{config.zephyr_room_prefix}<string:cls>{config.class_instance_separator}<string:instance>:{config.homeserver}'
@app.get(f'/rooms/{zephyr_class_instance_mxid}')
@app.get(f'/_matrix/app/v1/rooms/{zephyr_class_instance_mxid}')
@authenticated
def create_instance_room(cls, instance):
    # TODO: handle special characters by following this encoding:
    # https://spec.matrix.org/v1.5/appendices/#mapping-from-other-character-sets
    # and convert to and from the format in all relevant places
    print("Requested room", cls, instance)
    room_id = create_zephyr_room(cls, instance)
    if not room_id:
        return {'errcode': 'edu.mit.sipb.unknown'}, 500
    print("Done creating", cls, instance)
    return {}


# TODO: implement "thirdparty endpoints" (revert commit 4b12a963aa26f1f422eada928ac644dfcc394d87)
# I will not prioritize them since they don't seem to be used, even