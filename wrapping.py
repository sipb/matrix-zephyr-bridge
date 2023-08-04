import re
import textwrap

"""
this code was stolen from https://github.com/zulip/python-zulip-api/blob/main/zulip/integrations/zephyr/zephyr_mirror_backend.py
"""

def wrap_lines(body: str) -> str:
    wrapper = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)
    wrapped_content = "\n".join(
        "\n".join(wrapper.wrap(line)) for line in body.replace("@", "@@").split("\n")
    )
    return wrapped_content


# Checks whether the pair of adjacent lines would have been
# linewrapped together, had they been intended to be parts of the same
# paragraph.  Our check is whether if you move the first word on the
# 2nd line onto the first line, the resulting line is either (1)
# significantly shorter than the following line (which, if they were
# in the same paragraph, should have been wrapped in a way consistent
# with how the previous line was wrapped) or (2) shorter than 60
# characters (our assumed minimum linewrapping threshold for Zephyr)
# or (3) the first word of the next line is longer than this entire
# line.
def different_paragraph(line: str, next_line: str) -> bool:
    words = next_line.split()
    return (
        len(line + " " + words[0]) < len(next_line) * 0.8
        or len(line + " " + words[0]) < 50
        or len(line) < len(words[0])
    )

# Linewrapping algorithm based on:
# http://gcbenison.wordpress.com/2011/07/03/a-program-to-intelligently-remove-carriage-returns-so-you-can-paste-text-without-having-it-look-awful/ #ignorelongline
def unwrap_lines(body: str) -> str:
    lines = body.split("\n")
    result = ""
    previous_line = lines[0]
    for line in lines[1:]:
        line = line.rstrip()
        if re.match(r"^\W", line, flags=re.UNICODE) and re.match(
            r"^\W", previous_line, flags=re.UNICODE
        ):
            result += previous_line + "\n"
        elif (
            line == ""
            or previous_line == ""
            or re.match(r"^\W", line, flags=re.UNICODE)
            or different_paragraph(previous_line, line)
        ):
            # Use 2 newlines to separate sections so that we
            # trigger proper Markdown processing on things like
            # bulleted lists
            result += previous_line + "\n\n"
        else:
            result += previous_line + " "
        previous_line = line
    result += previous_line
    return result