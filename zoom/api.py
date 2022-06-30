"""
    api
"""

from urllib.parse import urlencode

import requests


class API:
    """
        Connect to and interact with a ZoomFoundry site.

        Note: request header specifies json but it's up to the app
              to decide whether or not to respect that.

    """

    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.username = username
        self.password = password
        self.session = session = requests.Session()
        session.headers.update({'Accept': 'application/json'})
        url = '%s/api' % site_url
        response = session.get(url)
        args = response.json()
        token = args['csrf_token']
        data = dict(
            username=self.username,
            password=self.password,
            csrf_token=token,
        )
        self.response = session.post(url, data=data)

    def get(self, *args, **kwargs):
        """get a response from the remote site"""
        path = '/'.join(args)
        path = path[1:] if path.startswith('/') else path
        args = urlencode(kwargs)
        url = f'{self.site_url}/{path}?{args}'
        return self.session.get(url)

    def post(self, *args, **kwargs):
        """get a response from the remote site"""
        path = '/'.join(args)
        path = path[1:] if path.startswith('/') else path
        url = f'{self.site_url}/{path}'
        return self.session.post(url, data=kwargs)
