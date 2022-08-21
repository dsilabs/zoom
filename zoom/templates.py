"""
    templates.zoom
"""

friendly_error = """
    <div class="jumbotron">
        <h1>Whoops!</h1>
        <p>Something went wrong!</p>
        <p>Please try again later or contact {{owner_link}} for assistance.<p>
    </div>
    """

page_not_found = """
    <div class="jumbotron">
        <h1>Page Not Found</h1>
        <p>The page you requested could not be found.
        Please contact the administrator or try again.<p>
    </div>
    """

template_missing = """
<html>
    <head>
    <style>
    body {
      margin: 0;
      padding: 0;
      font: 20px 'RobotoRegular', Arial, sans-serif;
      font-weight: 100;
      height: 100%;
      color: #0f1419;
    }
    h1 {
      padding-top: 0.75em;
      text-align: center;
      font-size: 3.5em;
      margin-bottom: 0.25em;
    }
    div.info {
      display: table;
      background: #e8eaec;
      padding: 20px 20px 20px 20px;
      border: 1px dashed black;
      border-radius: 10px;
      margin: 0px auto auto auto;
      font: 20px Courier;
    }
    div.info p {
        display: table-row;
        margin: 5px auto auto auto;
    }
    div.info p span {
        display: table-cell;
        padding: 10px;
    }
    div.smaller p span {
        color: #3D5266;
    }
    h1, h2 {
      font-weight: 100;
    }
    #footer {
        position: fixed;
        bottom: 36px;
        width: 100%;
        font-size: 0.8em;
    }
    #center {
        width: 400px;
        margin: 0 auto;
        font: 12px Courier;
    }
    </style>
    </head>
    <body>
    <h1>ZOOM</h1>
    <div class="info">
        <p>The theme for this site is configured incorrectly.</p>
        <br>
        <p>Please contact your site administrator or Dynamic Solutions at <support@dynamic-solutions.com> for assistanace.</p>
    </div>
    <div id="footer">
        <div id="center" align="center">
            <img src="https://www.dynamic-solutions.com/images/dynamicsolutions.png">
        </div>
    </div>
    </body>
</html>
"""

internal_server_error_500 = """
<html>
    <head>
    <style>
    body {
      margin: 0;
      padding: 0;
      font: 20px 'RobotoRegular', Arial, sans-serif;
      font-weight: 100;
      height: 100%;
      color: #0f1419;
    }
    h1 {
      padding-top: 0.75em;
      text-align: center;
      font-size: 3.5em;
      margin-bottom: 0.25em;
    }
    div.info {
      display: table;
      background: #e8eaec;
      padding: 20px 20px 20px 20px;
      border: 1px dashed black;
      border-radius: 10px;
      margin: 0px auto auto auto;
      font: 20px Courier;
      padding: 25px;
      width: 64%;
    }
    div.info p {
        margin: 5px auto 10px auto;
    }
    div.info p span {
        padding: 10px;
    }
    div.smaller p span {
        color: #3D5266;
    }
    h1, h2 {
      font-weight: 100;
      font-size: 20px;
    }
    h1 {
      font-weight: 100;
      font-size: 50px;
      margin-left: 16%;
      text-align: left;
    }
    #footer {
        position: fixed;
        bottom: 36px;
        width: 100%;
        font-size: 0.8em;
    }
    #center {
        width: 400px;
        margin: 0 auto;
        font: 12px Courier;
    }
    </style>
    </head>
    <body>
    <h1>Server Error</h1>
    <div class="info">
        <p>We're sorry but something has gone wrong.</p>
        <p>This is most likely an issue on our side, but if you want to you can try again now or in a little while.</p>
        <p>If this issue persists please contact your site administrator or Dynamic Solutions at <a href="mailto:support@dynamic-solutions.com">support@dynamic-solutions.com</a> for assistance.</p>
    </div>
    <div id="footer">
        <div id="center" align="center">
            <img src="https://www.dynamic-solutions.com/images/dynamicsolutions.png">
        </div>
    </div>
    </body>
</html>
"""
