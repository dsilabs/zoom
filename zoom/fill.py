"""
    fills templates
"""

import re

parts_re = (
    r"""(\w+)\s*=\s*"([^"]*)"|"""
    r"""(\w+)\s*=\s*'([^']*)'|"""
    r"""(\w+)\s*=\s*([^\s]+)\s*|"""
    r"""("")|"([^"]*)"|(\w+)"""
)
tag_parts = re.compile(parts_re)

pattern_tpl = r'%s([a-z0-9_]+)\s*(.*?)%s'
patterns = {}


def _fill(tag_start, tag_end, text, callback):
    """do the actual work of filling in tags
    
    >>> def filler(name, *args, **kwargs):
    ...     if name == 'name':
    ...         return 'Joe'
    >>> _fill('<dz:', '>', 'Hello <dz:name>!', filler)
    'Hello Joe!'
    
    """

    def replace_tag(match):
        """replace a tag"""

        name = match.groups(1)[0].lower()
        rest = match.group(0)[len(name)+len(tag_start):-len(tag_end)]
        parts = tag_parts.findall(rest)
        keywords = dict(
            a and (a, b) or c and (c, d) or e and (e, f)
            for (a, b, c, d, e, f, g, h, i) in parts
            if a or c or e
        )
        args = [
            h or i or ""
            for (_, _, _, _, _, _, g, h, i) in parts
            if h or i or g
        ]

        result = callback(name, *args, **keywords)
        if result is None:
            result = match.group(0)
        return result

    tags = (tag_start, tag_end)
    if tags not in patterns:
        patterns[tags] = re.compile(
            pattern_tpl % (tag_start, tag_end),
            re.IGNORECASE
        )
    innerre = patterns[tags]

    result = []
    lastindex = 0

    for outermatch in re.finditer("<!--.*?-->", text):
        text_between = text[lastindex:outermatch.start()]
        new_text = innerre.sub(replace_tag, text_between)
        result.append(new_text)
        lastindex = outermatch.end()
        result.append(outermatch.group())
    text_after = text[lastindex:]
    result.append(innerre.sub(replace_tag, text_after))

    return ''.join(x for x in result)


def fill(text, callback):
    """fill a tag in the double handlebars style"""
    return _fill('{{', '}}', text, callback)


def dzfill(text, callback):
    """fill a tag in the <dz: style"""
    return _fill('<dz:', '>', text, callback)
