"""
Code converted from original Pidgin C code.

https://github.com/Intika-Pidgin/Pidgin/blob/master/libpurple/protocols/zephyr/zephyr.c#L614 (mirror that still has Zephyr)
"""


class _ZFrame:
    # true for everything but @color, since inside the parens of that one is the color
    has_closer: bool

    # }, ], ), >
    closer: str

    # </i>, </font>, </b>, etc.
    closing: str

    # text including the opening html thingie.
    text: str

    # href for links
    # NOTE: this is unused, copied from original code
    is_href: bool
    href: str

    enclosing: object # _ZFrame but I can't use itself as a type


def zephyr_to_html(message):
    """
    Convert Zephyr to idiomatic Matrix HTML per https://spec.matrix.org/v1.13/client-server-api/#mroommessage-msgtypes

    >>> zephyr_to_html("hello@@world.com")
    'hello@world.com'

    >>> zephyr_to_html("@{@color(blue)@i(hello)}")
    '<span data-mx-color="blue"><i>hello</i></span>'

    >>> zephyr_to_html("@b[hello @i{world @color(blue)this is a test}]")
    '<b>hello <i>world <span data-mx-color="blue">this is a test</span></i></b>'

    >>> zephyr_to_html("hello@bold.com, someone forgot to escape the @")
    'hello@bold.com, someone forgot to escape the @'
    """

    frames: _ZFrame

    frames = _ZFrame()
    frames.text = ""
    frames.enclosing = None
    frames.closing = ""
    frames.has_closer = False
    frames.closer = None

    while message:
        if message[0] == '@' and len(message) > 1 and message[1] == '@':
            frames.text += "@"
            message = message[2:]
        elif message[0] == '@':
            end = 1
            while end < len(message) and (message[end].isalnum() or message[end] == '_'):
                end += 1
            if end < len(message) and (message[end] in "{[(" or message[end:].startswith("&lt;")):
                buf: str = message[1:end]
                message = message[end:]
                new_f = _ZFrame()
                new_f.enclosing  = frames
                new_f.has_closer = True
                new_f.closer = (
                    ")" if message[0] == '(' else
                    "]" if message[0] == '[' else
                    "}" if message[0] == '{' else
                    "&gt;"
                )
                message = message[(4 if message[0] == '&' else 1):]
                if buf.lower() in ("italic", "i"):
                    new_f.text = "<i>"
                    new_f.closing = "</i>"
                elif buf.lower() == "huge":
                    new_f.text = "<h1>"
                    new_f.closing = "</h1>"
                elif buf.lower() == "large":
                    new_f.text = "<h2>"
                    new_f.closing = "</h2>"
                elif buf.lower() == "medium":
                    # Presumably this is normal size, leaving the same for now
                    # TODO: do something better
                    new_f.text = "<font size=\"3\">"
                    new_f.closing = "</font>"
                elif buf.lower() == "small":
                    # subscript is probably the closest thing
                    new_f.text = "<sub>"
                    new_f.closing = "</sub>"
                elif buf.lower() in ("bold", "b"):
                    new_f.text = "<b>"
                    new_f.closing = "</b>"
                elif buf.lower() == "font":
                    # Changing the font is not currently supported by Matrix, leaving the same for now
                    # https://spec.matrix.org/v1.13/client-server-api/#mroommessage-msgtypes
                    extra_f = _ZFrame()
                    extra_f.enclosing = frames
                    new_f.enclosing = extra_f
                    extra_f.text = ""
                    extra_f.has_closer = False
                    extra_f.closer = frames.closer
                    extra_f.closing = "</font>"
                    new_f.text = "<font face=\""
                    new_f.closing = "\">"
                elif buf.lower() == "color":
                    extra_f = _ZFrame()
                    extra_f.enclosing = frames
                    new_f.enclosing = extra_f
                    extra_f.text = ""
                    extra_f.has_closer = False
                    extra_f.closer = frames.closer
                    extra_f.closing = "</span>"
                    new_f.text = "<span data-mx-color=\""
                    new_f.closing = "\">"
                else:
                    new_f.text = ""
                    new_f.closing = ""
                frames = new_f
            else:
                # Not a formatting tag, add the character as normal.
                frames.text += message[0]
                message = message[1:]
        elif frames.closer and message.startswith(frames.closer):
            popped: _ZFrame
            last_had_closer: bool = False
            
            message = message[len(frames.closer):]
            if frames.enclosing:
                while True:
                    popped = frames
                    frames = frames.enclosing
                    frames.text += popped.text
                    frames.text += popped.closing
                    popped.text = ""
                    last_had_closer = popped.has_closer
                    # simulate do while loop from C code
                    if frames.enclosing is None or last_had_closer:
                        break
            else:
                frames.text += message
        elif message[0] == '\n':
            frames.text += "<br>"
            message = message[1:]
        else:
            frames.text += message[0]
            message = message[1:]
    # go through all the stuff that they didn't close
    while frames.enclosing is not None:
        frames.enclosing.text += frames.text
        frames.enclosing.text += frames.closing
        frames.text = ""
        frames = frames.enclosing
    return frames.text


if __name__ == "__main__":
    import doctest
    doctest.testmod()
