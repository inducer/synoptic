class Context(dict):
    def copy(self):
        return Context(self)

    def add(self, **kwargs):
        result = self.copy()
        result.update(kwargs)
        return result




def page(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <head>
      <title>%(title)s</title>
      <script type="text/javascript" src="/static/jquery.js"></script>
      <script type="text/javascript" src="/static/inheritance.js"></script>
      <script type="text/javascript" src="/static/main.js"></script>
      <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
      <body>
        %(body)s
      </body>
    </html>
    """ % context

def navpane(context):
    return """
    <div id="navpane">
      <ul>
        %(taglist)s
      </ul>
    </div>
    """

def mainpane(context):
    return """
    <div id="mainpane">
      <label for="search" accesskey="s">Search: </label><input type="text" size="50" id="search"/>

      <div id="items>
      </div>
    </div>
    """

def mainpage(context):
    return page(context.add(
        title="Zapp",
        body=navpane(context)+mainpane(context)
        ))
