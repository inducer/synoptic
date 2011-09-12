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
    <html>
    <head>
      <title>%(title)s</title>
      <link rel="stylesheet" type="text/css" href="../static/content.css">
    </head>
    <body>
        %(body)s
    </body>
    </html>
    """ % context





def calendar_page(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <html>
    <head>
      <title>Synoptic Calendar</title>
      <link rel="stylesheet" type="text/css" href="static/jquery-ui-css/smoothness/jquery-ui-1.8.9.custom.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="static/fullcalendar.css"/>
      <link rel="stylesheet" type="text/css" href="static/calendar.css" />
      <link rel="stylesheet" type="text/css" href="tag-color-css?calendar=true" />
      <script type="text/javascript" src="static/jquery.js"></script>
      <script type="text/javascript" src="static/jquery-ui.js"></script>
      <script type="text/javascript" src="static/fullcalendar.js"></script>
      <script type="text/javascript" src="static/calendar.js"></script>
      <link rel="icon" type="image/png" href="static/calendar-favicon.png"/>
    </head>
    <body>
      <div id="calendar"></div>
      <div class="keyhelp">
      Keyboard shortcuts:
      <span class="key">H</span> previous
      <span class="key">L</span> next
      <span class="key">W</span> week view
      <span class="key">M</span> month view
      <span class="key">U</span> update
      </div>
    </body>
    </html>
    """ % context




def page(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
      <title>%(title)s</title>
      <link rel="stylesheet" type="text/css" href="static/jquery-ui-css/smoothness/jquery-ui-1.8.9.custom.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="static/style.css"/>
      <link rel="stylesheet" type="text/css" href="static/content.css"/>
      <link rel="stylesheet" type="text/css" href="tag-color-css" />
      <link rel="icon" type="image/png" href="static/synoptic.png"/>
      <script type="text/javascript" src="app/get_all_js"></script>
      <script type="text/javascript" src="static/main.js"></script>
    </head>
    <body>
        %(body)s
    </body>
    </html>
    """ % context




def mobile_page(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
      <title>%(title)s</title>
      <link rel="icon" type="image/png" href="static/synoptic.png"/>
      <link rel="stylesheet" type="text/css" href="static/jquery-mobile/jquery.mobile-1.0b3.css" media="screen"/>
      <script type="text/javascript" src="app/get_all_js"></script>
      <script type="text/javascript" src="jquery-mobile/jquery.mobile-1.0b3.js"></script>
      <script type="text/javascript" src="static/mobile.js"></script>
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
        <div id="logo"><a href="http://mathema.tician.de/software/synoptic">Synoptic</a></div>
        <div id="history_nav" class="ui-corner-all">
          <div style="white-space:nowrap;">
            <label for="edit_date" accesskey="t"><img src="static/time.png" alt="Time" class="inlineimg"/></label>
            <input type="text" id="edit_date" size="10"/>

            <img src="static/go-last.png" id="btn_go_present" class="imagebutton" alt="Go to present"/>
          </div>
          <div id="history_time" class="ui-widget"></div>
          <div id="slider_container">
            <div id="history_slider"> </div>
          </div>

          <span id="messagearea"></span>
        </div>

        <div id="navtabs">
          <ul id="tagtab_header">
            <li><a href="#fragment-1">Tags</a></li>
            <li><a href="#fragment-2">All Tags</a></li>
          </ul>
          <div id="fragment-1">
            <div id="subtagcloud_search_tags"> </div>
            <div id="subtagcloud" class="tagcloud"> </div>
            <input type="checkbox" id="chk_subtagcloud_show_hidden"/>
            <span id="navtab_size_helper_top_1"></span>
            <label for="chk_subtagcloud_show_hidden">Show hidden (.<i>tag</i>)</label>
          </div>
          <div id="fragment-2">
            <div id="tagcloud" class="tagcloud"> </div>
            <input type="checkbox" id="chk_tagcloud_show_hidden"/>
            <span id="navtab_size_helper_top_2"></span>
            <label for="chk_tagcloud_show_hidden">Show hidden (.<i>tag</i>)</label>
          </div>
        </div>
        <span id="navtab_size_helper_bottom"></span>
      </div>
    </div>
    """

def mainpane(context):
    return """
    <div id="mainpane">
      <div id="innermainpane">
        <div id="searchbar">
          <span id="search-wrapper">
            <input type="text" size="50" id="search"/>
            <input type="button" id="btn_search_clear"/>
          </span>
          <img src="static/time.png" alt="Calendar" title="Calendar" id="btn_calendar" class="imagebutton"/>
          <img src="static/print.png" alt="Print" title="Print" id="btn_print" class="imagebutton"/>
          <img src="static/expand-all.png" alt="Expand all" title="Expand all" id="btn_expand" class="imagebutton"/>
          <img src="static/collapse-all.png" alt="Collapse all" title="Collapse all" id="btn_collapse" class="imagebutton"/>
          <img src="static/export.png" alt="Export" title="Export" id="btn_export" class="imagebutton"/>
          <img src="static/quit.png" alt="Quit" title="Quit" id="btn_quit" class="imagebutton"/>
          <img src="static/copy.png" alt="Copy (relative) link URL" title="Copy (relative) link URL" id="btn_copy" class="imagebutton"/>
          <div id="linkurl">
            <input type="text" readonly="readonly" id="linkurl_edit"/>
          </div>
        </div>
        <div id="items">
        </div>
        <div id="hiddenitems">
        </div>
      </div>
    </div>
    """

def popups():
    return """
    <div id="tag_context_menu">
      <ul>
        <li id="tag-menu-rename">Rename</li>
        <li id="tag-menu-restrict">Restrict search</li>
        <li id="tag-menu-search">Search for only this tag</li>
      </ul>
    </div>
    <div id="out_of_date_notifier" class="ood_hidden">
      <img src="static/warning.png" alt="Warning"/>
      <p>Currently displayed results are out of date.</p>

      <input type="button" id="ood_reload_btn" value="Reload"/>
    </div>
    """

def main_page(context):
    return page(context.add(
        title="Synoptic",
        body='<div id="main_container">%s</div>%s' % (
            navpane(context)+mainpane(context),
            popups())
        ))




def mobile_body():
    return """
    <!-- Start of first page: #one -->
    <div data-role="page" id="foo">

        <div data-role="header">
            <h1>Multi-page</h1>
        </div><!-- /header -->

        <div data-role="content" id="one">
            <h2>One</h2>

            <p>I have an id of "one" on my page container. I'm first in the source order so I'm shown when the page loads.</p>

            <p>This is a multi-page boilerplate template that you can copy to build you first jQuery Mobile page. This template contains multiple "page" containers inside, unlike a <a href="page-template.html"> single page template</a> that has just one page within it.</p>
            <p>Just view the source and copy the code to get started. All the CSS and JS is linked to the jQuery CDN versions so this is super easy to set up. Remember to include a meta viewport tag in the head to set the zoom level.</p>

            <p>You link to internal pages by referring to the ID of the page you want to show. For example, to <a href="#two" >link</a> to the page with an ID of "two", my link would have a <code>href="#two"</code> in the code.</p>

            <h3>Show internal pages:</h3>
            <p><a href="#two" data-role="button">Show page "two"</a></p>
            <p><a href="#popup"data-role="button" data-rel="dialog" data-transition="pop">Show page "popup" (as a dialog)</a></p>
        </div><!-- /content -->


        <div data-role="footer" data-theme="d">
            <h4>Page Footer</h4>
        </div><!-- /footer -->
    </div><!-- /page one -->


    <!-- Start of second page: #two -->
    <div data-role="page" id="two" data-theme="a">

        <div data-role="header">
            <h1>Two</h1>

        </div><!-- /header -->

        <div data-role="content" data-theme="a">
            <h2>Two</h2>
            <p>I have an id of "two" on my page container. I'm the second page container in this multi-page template.</p>
            <p>Notice that the theme is different for this page because we've added a few <code>data-theme</code> swatch assigments here to show off how flexible it is. You can add any content or widget to these pages, but we're keeping these simple.</p>
            <p><a href="#one" data-direction="reverse" data-role="button" data-theme="b">Back to page "one"</a></p>

        </div><!-- /content -->


        <div data-role="footer">
            <h4>Page Footer</h4>
        </div><!-- /footer -->
    </div><!-- /page two -->


    <!-- Start of third page: #popup -->
    <div data-role="page" id="popup">

        <div data-role="header" data-theme="e">
            <h1>Dialog</h1>

        </div><!-- /header -->

        <div data-role="content" data-theme="d">
            <h2>Popup</h2>
            <p>I have an id of "popup" on my page container and only look like a dialog because the link to me had a <code>data-rel="dialog"</code> attribute which gives me this inset look and a <code>data-transition="pop"</code> attribute to change the transition to pop. Without this, I'd be styled as a normal page.</p>
            <p><a href="#one" data-rel="back" data-role="button" data-inline="true" data-icon="back">Back to page "one"</a></p>
        </div><!-- /content -->


        <div data-role="footer">
            <h4>Page Footer</h4>
        </div><!-- /footer -->
    </div><!-- /page popup -->
    """




def mobile_main_page(context):
    return mobile_page(context.add(
        title="Synoptic Mobile",
        body=mobile_body()
        ))
