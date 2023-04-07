import zephyr

zephyr.init()

notice = zephyr.ZNotice(
    cls='thisclassdoesnotexist',
    instance='test',
    sender='fakeuser',
    message='Hello world!',
    opcode='AUTO',
    auth=False, # FOR SCRIPTS
)
notice.send()