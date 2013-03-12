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
      <link rel="stylesheet" type="text/css" href="static/jquery-ui-css/smoothness/jquery-ui-1.10.1.custom.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="static/fullcalendar.css"/>
      <link rel="stylesheet" type="text/css" href="static/calendar.css" />
      <link rel="stylesheet" type="text/css" href="tag-color-css?calendar=true" />
      <script type="text/javascript" src="static/jquery.js"></script>
      <script type="text/javascript" src="static/jquery-migrate.js"></script>
      <script type="text/javascript" src="static/jquery-ui.js"></script>
      <script type="text/javascript" src="static/fullcalendar.js"></script>
      <script type="text/javascript" src="static/gcal.js"></script>
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
      <link rel="stylesheet" type="text/css" href="static/jquery-ui-css/smoothness/jquery-ui-1.10.1.custom.css" media="screen"/>
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




# {{{ mobile pages

def mobile_page(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
      <title>%(title)s</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="icon" type="image/png" href="static/synoptic.png"/>
      <link rel="stylesheet" type="text/css" href="static/jquery-mobile/jquery-mobile.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="static/mobile.css"/>
      <script type="text/javascript" src="app/get_all_js"></script>
      <script type="text/javascript" src="static/jquery-mobile/jquery-mobile.js"></script>
      <script type="text/javascript" src="static/mobile.js"></script>
    </head>
    <body>
        %(body)s
    </body>
    </html>
    """ % context




def mobile_body():
    return """
    <div data-role="page" id="main">

        <div data-role="header">
            <h1>Synoptic Mobile</h1>
        </div>

        <div data-role="content" id="one">
            <div data-role="fieldcontain" class="search-container">
                <input type="search" name="query" id="search" value="" />
            </div>

            <ul data-role="listview">
                <li><a href="#edit">
                    <p>Get money from Cornell trip</p>
                </a></li>
                <li><a href="#edit">
                    <p>Alternatives for stuff:
                    <ul>
                    <li> Alternative 1</li>
                    <li> Alternative 1</li>
                    </ul>
                    </p>
                </a></li>
                <li><a href="#edit">
                    <div class="ui-li-desc itemcontainer">
                    <div class="tagdisplay">now getmoney silly</div>
                    <p><strong>Hidden until 9/14</strong></p>
                    <p>
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    Take out the trash
                    </p>
                    </div>
                </a></li>
                <li><a href="#edit">
                    <p>
                    Water plants
                    </p>
                </a></li>
            </ul>
            <div style="padding-top:15px"></div>

            <div data-role="controlgroup">
              <a href="#edit" data-role="button" data-icon="plus">Add Note</a>
              <a href="/mobile-calendar" rel="external" data-role="button" data-icon="grid">Calendar</a>
              <a href="#quit" data-role="button" data-icon="alert" data-rel="dialog">Quit Synoptic</a>
            </div>
        </div><!-- /content -->

    </div>


    <div data-role="page" id="edit">
        <div data-role="header">
            <a href="#main" data-role="button" data-icon="back" data-rel="back">Cancel</a>
            <h1>Edit Item</h1>
            <a href="#main" data-role="button" data-icon="check">Save</a>
        </div>

        <div data-role="content">
            <form>
            <div data-role="fieldcontain">
                <textarea cols="40" rows="20" name="textarea" id="textarea"></textarea>
            </div>
            <div data-role="fieldcontain">
                <label for="tags">Tags:</label>
                <input type="text" name="tags" id="tags" value="" />
            </div>
            <div data-role="fieldcontain">
                <label for="start_date">Date:</label>
                <input type="text" name="start_date" id="start_date" value="" />
            </div>
            <div data-role="fieldcontain">
                <label for="end_date">End:</label>
                <input type="text" name="end_date" id="end_date" value="" />
            </div>
            <div data-role="fieldcontain">
                <fieldset data-role="controlgroup">
                    <input type="checkbox" name="all_day" id="all_day" class="custom" />
                    <label for="all_day">All day</label>
                </fieldset>
            </div>
            <div data-role="fieldcontain">
                <label for="hide_until">Hide Until:</label>
                <input type="text" name="hide_until" id="hide_until" value="" />
            </div>
            <div data-role="fieldcontain">
                <label for="highlight_at">Highlight At:</label>
                <input type="text" name="highlight_at" id="highlight_at" value="" />
            </div>
            <div data-role="fieldcontain">
                <label for="bump_interval" class="select">Bump interval:</label>
                <select name="bump_interval" id="bump_interval">
                    <option value="day">Day</option>
                    <option value="week">Week</option>
                    <option value="Month">Month</option>
                </select>
            </div>

            <div data-role="controlgroup" data-type="horizontal">
                <a href="#" data-role="button" data-icon="arrow-l" >Bump</a>
                <a href="#" data-role="button" data-icon="arrow-r" >Bump</a>
            </div>
            </form>
        </div>

        <div data-role="footer" class="ui-bar">
            <div data-role="controlgroup" data-type="horizontal">
                <a href="#main" data-role="button" data-icon="check">Save</a>
                <a href="#main" data-role="button" data-icon="delete">Delete</a>
                <a href="#main" data-role="button" data-icon="back" data-rel="back">Cancel</a>
            </div>
        </div>
    </div>


    <div data-role="page" id="calendar" data-theme="a">

        <div data-role="header">
            <h1>Calendar</h1>

        </div><!-- /header -->

        <div data-role="content" data-theme="a">
            <h2>Calendar</h2>
            <p>Who knew--this would be the calendar.</p>
        </div><!-- /content -->


        <div data-role="footer">
            <h4>Page Footer</h4>
        </div><!-- /footer -->
    </div><!-- /page two -->


    <div data-role="page" id="quit">

        <div data-role="header" data-theme="e">
            <h1>Quit Synoptic</h1>
        </div>

        <div data-role="content" data-theme="d">
            <h2>Are you sure?</h2>

            Are you sure you want to quit Synoptic Mobile?

            <div data-role="controlgroup">
            <a href="/app/quit" data-role="button" rel="external" data-icon="check">Yes</a>
            <a href="#main" data-role="button" data-icon="back" data-rel="back">No</a>
            </div>
        </div>
    </div>
    """




def mobile_main_page(context):
    return mobile_page(context.add(
        title="Synoptic Mobile",
        body=mobile_body()
        ))




def mobile_calendar_page(context):
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
         "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    <html>
    <head>
      <title>Synoptic Calendar</title>
      <link rel="stylesheet" type="text/css" href="static/jquery-ui-css/smoothness/jquery-ui-1.10.1.custom.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="static/fullcalendar.css"/>
      <link rel="stylesheet" type="text/css" href="static/mobile-calendar.css" />
      <link rel="stylesheet" type="text/css" href="tag-color-css?calendar=true" />
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script type="text/javascript" src="static/jquery.js"></script>
      <script type="text/javascript" src="static/jquery-migrate.js"></script>
      <script type="text/javascript" src="static/jquery-ui.js"></script>
      <script type="text/javascript" src="static/fullcalendar.js"></script>
      <script type="text/javascript" src="static/mobile-calendar.js"></script>
      <link rel="icon" type="image/png" href="static/calendar-favicon.png"/>
    </head>
    <body>
      <div id="view-nav" class="view-controls">
        <span class="view-nav-button" id="backward">&lt;</span>
        <span class="view-nav-button" id="forward">&gt;</span>
      </div>

      <div id="calendar"></div>

      <div id="view-chooser" class="view-controls">
        <span class="view-button" id="month">Month</span>
        <span class="view-button" id="week">Week</span>
        <span class="view-button" id="day">Day</span>
      </div>

    </body>
    </html>
    """ % context



# }}}

# vim: foldmethod=marker
