# matrix-zephyr-bridge

[Zephyr](https://en.wikipedia.org/wiki/Zephyr_(protocol)) bridge for Matrix

## How to run?

1. Install dependencies (`pip install .` in python-zephyr)
2. Copy `config.sample.yaml` to `config.yaml` and edit to suit your needs
3. Using `pwgen -s 64 1`, generate the tokens and add them to the `config.yaml`
4. Run `generate_registration.py` to generate a `registration.yaml`. Use it to register the appservice with the Matrix homeserver (i.e. <https://docs.mau.fi/bridges/general/registering-appservices.html>)
5. Create an empty `zephyr.subs` file. You may fill it with content like `.zephyr.subs` to pre-subscribe it to some classes and/or instances.

This bridge is 2 halves: the Matrix-to-Zephyr half is a Flask REST API located on `matrix_receive.py`, and the Zephyr-to-Matrix half is located in `zephyr_receive.py`.

<!-- TODO: add more specific instructions on how to run -->

## How to use?

This is a Matrix application service which will automatically create rooms as needed.

* To join the zephyr room for the class `sipb` and instance `other`, ask your Matrix client to join the room `#z/sipb/other:matrix.mit.edu`. If it does not exist on the Matrix side, the bridge will automatically subscribe to it and start bridging all future messages from and to Zephyr.*

* To subscribe to all instances of the class `sipb`, you can ask your Matrix client to join the room `#Z/sipb:matrix.mit.edu`. This will be a **space** containing a room for each instance (_not implemented yet_).

* To subscribe to the entire class `weather` using a single room, ask your Matrix client to join the room `#z/weather:matrix.mit.edu`. Messages sent to any instance of `weather` will be sent to the room (_not implemented yet_).

*prefix, separator and homeserver may vary if `config.yaml` was changed

## Roadmap

 - [x] Bridge specific instances
 - [ ] Bridge all instances of specific class
 - [x] Zephyr signatures <-> Matrix display name
 - [x] Ignore messages from specific hosts (such as mattermost.mit.edu, to avoid double bridging)
 - [ ] Import Gravatar/Zulip profile pictures
 - [ ] Zephyr->Matrix metadata (whether the message is authentic, mostly)
 - [ ] Support authentic messages (using Webathena tickets)
 - [ ] Support unauthenticated DMs (via bot account as proxy)
 - [ ] Support authenticated DMs (via user through Webathena tickets)
 - [ ] Support unclasses and `.d` instances (convention for off-topic conversations) (bridge as threads?)
 - [ ] Matrix->Zephyr images, stickers, etc via URL
 - [ ] Matrix->Zephyr formatting (HTML/MD to custom Zephyr syntax)
 - [ ] Zephyr->Matrix formatting (parse custom Zephyr syntax into HTML)
 - [ ] (only if you file an issue/PR) Test that this works for other Zephyrs outside of ATHENA.MIT.EDU

Features that Zephyr does not support:

 - [ ] Matrix->Zephyr reactions(?) (SMS-style message + AUTO opcode)
 - [ ] Matrix->Zephyr edits and deletions(?) (probably like reactions, send a text message explaining the change)
 - [ ] Matrix->Zephyr replies(?) (perhaps a text saying "in reply to"?)
