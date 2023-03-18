import zephyr

zephyr.init()

notice = zephyr.ZNotice(
    cls='rgabriel',
    instance='test',
    sender='fakeuser',
    message='Hello world!',
    opcode='AUTO', # I don't know what this is
)
notice.send()