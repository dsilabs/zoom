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

        >>> test_site = get_test_site()
        >>> api = API(test_site, 'admin', 'admin')
        >>> api.get('ping')
        True
        >>> api.close()

    """

    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.username = username
        self.password = password
        self.session = session = requests.Session()
        session.headers.update({'Accept': 'application/json'})
        response = session.get(f'{site_url}/api')
        args = response.json()
        token = args['csrf_token']
        data = dict(
            username=self.username,
            password=self.password,
            csrf_token=token,
        )
        self.response = session.post(f'{site_url}/api', data=data)

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
