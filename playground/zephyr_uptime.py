#!/usr/bin/env python2
# scripts may only have the zephyr library on Python 2

import zephyr
import threading
import time
import os
import sys

"""
This script will send a "echo {request_id}" message to the Zephyr bot, which
will zwrite back the unique request_id. If it is successfully received, exit
successfully. If WAIT_TIME passes, exit unsuccessfully.
"""

# Hardcoded for now, TODO: change if needed
os.system("kinit daemon/matrix.mit.edu@ATHENA.MIT.EDU -k -t daemon_matrix.keytab")

BOT_USERNAME = "daemon/matrix.mit.edu"
WAIT_TIME = 5

# For now, this is just the current time, such as "Sun Dec 22 12:59:28 2024"
request_id = time.ctime()

keep_waiting = True
successfully_received = False

zephyr.init()
subs = zephyr.Subscriptions()
# Apparently you need to be subscribed to at least one class to receive direct messages
subs.add(('dummyclass', '*', '*'))

def send_message():
    notice = zephyr.ZNotice(
        opcode="",
        cls="MESSAGE", instance="PERSONAL", # Signals this is a direct message
        fields=["uptime checker", "echo %s" % request_id],
        recipient=BOT_USERNAME,
        auth=False,
    )
    notice.send()

def wait_for_message():
    global successfully_received, keep_waiting
    while keep_waiting:
        msg = zephyr.receive(True)
        if msg is not None:
            sys.stderr.write("New message received! %s \n" % str(msg.__dict__))
            if msg.sender == BOT_USERNAME + "@ATHENA.MIT.EDU" and msg.fields[1] == request_id:
                successfully_received = True
                keep_waiting = False
                break

thread = threading.Thread(target=wait_for_message)
thread.daemon = True
thread.start()
send_message()
thread.join(WAIT_TIME)
keep_waiting = False

# For some really strange reason, CGI wants \r\n and it isn't working out of the box
# It seems like regular print statements work on Python 3 but not 2
# Maybe Python 3 detects it's running under CGI and gives the \r\n (but not Python 2)
if successfully_received:
    sys.stdout.write(
        "Content-Type: text/plain\r\n"
        "\r\n"
        "The bridge is up! :) \r\n"
    )
    exit(0)
else:
    sys.stdout.write(
        "Status: 503 Service Unavailable\r\n"
        "\r\n"
        "The bridge appears to be down :(\r\n"
    )
    exit(1)
