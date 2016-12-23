"""
    info

    display system info
"""

import json


def app(request):
    def serializable(i):
        _, v = i
        try:
            json.dumps(v)
            return True
        except TypeError:
            return False

    tpl = '<h1>System Info</h1><pre>{}</pre>'
    request_values = dict(filter(serializable, request.__dict__.items()))
    values = dict(request_values, data=request.data)
    return tpl.format(json.dumps(values, indent=4))
