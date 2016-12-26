# zoom

The python web platform that does less.

Zoom is a simple application platform for building dynamic web sites quickly and easily.

Create an app:
```python
# app.py
def app(request):
    return 'Hello World!'
```

Run it:
```shell
zoom server .
```

View at: http://localhost


## Installation

clone zoom
```shell
git clone git@github.com:dsilabs/zoom.git
```

add zoom command to your path

Ubuntu example:
```
ln -s /path-to-libs/zoom/utils/zoom/zoom /usr/local/bin/zoom
```
