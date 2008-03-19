class Context(dict):
    def copy(self):
        return Context(self)

    def add(self, **kwargs):
        result = self.copy()
        result.update(kwargs)
        return result




def printpage(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <head>
      <title>%(title)s</title>
    </head>
      <body>
        %(body)s
      </body>
    </html>
    """ % context





def page(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <head>
      <title>%(title)s</title>
      <script type="text/javascript" src="/static/jquery.js"></script>
      <script type="text/javascript" src="/static/jquery.timers.js"></script>
      <script type="text/javascript" src="/static/jquery.bgiframe.js"></script>
      <script type="text/javascript" src="/static/jquery.dimensions.js"></script>
      <script type="text/javascript" src="/static/jquery.autocomplete.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.base.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.mouse.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.slider.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.tabs.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.draggable.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.draggable.ext.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.droppable.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/ui.droppable.ext.js"></script>
      <script type="text/javascript" src="/static/jquery-ui/datepicker/core/ui.datepicker.js"></script>
      <script type="text/javascript" src="/static/inheritance.js"></script>
      <script type="text/javascript" src="/static/json2.js"></script>
      <script type="text/javascript" src="/static/main.js"></script>
      <link rel="stylesheet" type="text/css" href="/static/style.css">
      <link rel="stylesheet" href="/static/jquery-ui/themes/flora/flora.all.css" type="text/css" media="screen">
    </head>
      <body>
        %(body)s
      </body>
    </html>
    """ % context

def navpane(context):
    return """
    <div id="navpane">
      <div id="innernavpane">
        <div id="logo">Synoptic</div>
        <div id="history_nav">
          <div style="white-space:nowrap;">
            <label for="edit_date" accesskey="t"><img src="/static/time.png" alt="Time" class="inlineimg"/></label>
            <input type="text" id="edit_date" size="10"/>
            <span id="history_time"></span>
            <img src="/static/go-last.png" id="btn_go_present" class="imagebutton"/>
          </div>
          <div id="slider_container">
            <div id="history_slider" class="ui-slider-1" style="margin:10px;">
              <div class="ui-slider-handle"></div>
            </div>
          </div>
        </div>

        <div id="messagearea">
        </div>

        <div id="navtabs" class="flora">
          <ul>
            <li><a href="#fragment-1"><span>Tags</span></a></li>
            <li><a href="#fragment-2"><span>Sub-Tags</span></a></li>
            <li><a href="#fragment-3"><span>Search</span></a></li>
          </ul>
          <div id="fragment-1">
            <div id="tagcloud"> </div>
            <input type="checkbox" id="chk_tagcloud_show_hidden"/>
            <label for="chk_tagcloud_show_hidden">Show hidden (.<i>tag</i>)</label>
          </div>
          <div id="fragment-2">
            <div id="subtagcloud_search_tags"> </div>
            <div id="subtagcloud"> </div>
          </div>
          <div id="fragment-3">
            <div id="viewlist"> </div>
          </div>
          </div>
        </div>
      </div>
    </div>
    """

def mainpane(context):
    return """
    <div id="mainpane">
      <div id="innermainpane">
        <div style="white-space:nowrap;">
          <label for="search" accesskey="s">Search: </label>
          <input type="text" size="50" id="search"/>
          <img src="/static/edit-clear.png" alt="Clear search bar" id="btn_search_clear" class="imagebutton"/>
          <img src="/static/print.png" alt="Print" id="btn_print" class="imagebutton"/>
        </div>
        <div id="items>
        </div>
      </div>
    </div>
    """

def mainpage(context):
    return page(context.add(
        title="Synoptic",
        body='<div id="main_container">%s</div>' % (navpane(context)+mainpane(context))
        ))
