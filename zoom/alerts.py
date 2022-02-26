"""
    zoom alerts
"""


from zoom.components import compose


def success(message):
    compose(success=message)

def warning(message):
    compose(warning=message)

def error(message):
    compose(error=message)
