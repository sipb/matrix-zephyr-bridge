import zephyr

zephyr.init()
subs = zephyr.Subscriptions()
subs.add(('rgabriel', 'test', '*'))

while True:
    msg: zephyr.ZNotice = zephyr.receive(True)
    if msg is not None:
        print('New message received!')
        print(msg.__dict__)
        # for k, v in msg:
        #     print(k, v)

