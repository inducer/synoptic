var UP_TO_DATE_TIMEOUT = 60*1000;
var DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday"];
var SHORT_DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
var SHORT_MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
    "Aug", "Sep", "Oct", "Nov", "Dec"];

var msgnum = 0;

function busy(what)
{
  return '<img src="/static/busy.gif" alt="Busy" /> '+what;
}




function set_message(what, timeout)
{
  ++msgnum;
  $("#messagearea").append(
      ('<div id="msg_[id]" class="message">'+what+'</div>').allreplace("[id]", msgnum));
  var my_msg = $("#msg_"+msgnum);

  if (timeout  == undefined)
    timeout = 10*1000;

  window.setTimeout(function() { my_msg.remove(); }, 10*1000)
}

function report_error(what)
{
  set_message(what);
}




function zero_pad(s, min_length)
{
  while (s.length < min_length)
    s = "0"+s;
  return s
}




function format_editable_timestamp(timestamp, all_day)
{
  var dt = new Date(timestamp*1000);

  if (all_day)
  {
    var result = sprintf("%d/%d/%d",
      dt.getUTCMonth()+1, dt.getUTCDate(), dt.getUTCFullYear());
  }
  else
  {
    var result = sprintf("%d/%d/%d",
      dt.getMonth()+1, dt.getDate(), dt.getFullYear());

    if (!(dt.getHours() == 0 && dt.getMinutes() == 0 && dt.getSeconds() == 0))
      result += sprintf(" %d:%02d", dt.getHours(), dt.getMinutes());
  }

  return result;
}




function format_timestamp(timestamp, all_day)
{
  var dt = new Date(timestamp*1000);
  var now = new Date();

  if (all_day)
  {
    var result = SHORT_DAY_NAMES[dt.getUTCDay()];

    if (dt.getUTCFullYear() == now.getUTCFullYear())
      result += sprintf(" %s %d", SHORT_MONTH_NAMES[dt.getUTCMonth()], dt.getUTCDate());
    else
      result += sprintf(" %s %d %d",
        SHORT_MONTH_NAMES[dt.getUTCMonth()], dt.getUTCDate(), dt.getUTCFullYear());
  }
  else
  {
    var result = SHORT_DAY_NAMES[dt.getDay()];

    if (dt.getFullYear() == now.getFullYear())
      result += sprintf(" %s %d", SHORT_MONTH_NAMES[dt.getMonth()], dt.getDate());
    else
      result += sprintf(" %s %d %d",
        SHORT_MONTH_NAMES[dt.getMonth()], dt.getDate(), dt.getFullYear());

    if (!(dt.getHours() == 0 && dt.getMinutes() == 0 && dt.getSeconds() == 0))
      result += sprintf(" %d:%02d", dt.getHours(), dt.getMinutes());
  }

  return result;
}




// {{{ String extension
String.method("allreplace", function(from, to)
{
  var last, current = this;
  do
  {
    last = current;
    current = last.replace(from, to);
  }
  while (last != current);
  return current;
})

String.method("trim", function()
{
  return this.replace(/^\s*(.*?)\s*$/,"$1");
});

function str(val)
{
  if (val == null)
    return '';
  else
    return val.toString();
}

// }}}

// {{{ misc tools
function re_escape(text) {
  if (!arguments.callee.sRE) {
    var specials = [
      '/', '.', '*', '+', '?', '|',
      '(', ')', '[', ']', '{', '}', '\\'
    ];
    arguments.callee.sRE = new RegExp(
      '(\\' + specials.join('|\\') + ')', 'g'
    );
  }
  return text.replace(arguments.callee.sRE, '\\$1');
}




function find_in_array(ary, item)
{
  for (var i = 0; i < ary.length; ++i)
    if (ary[i] == item)
      return i;
  return -1;
}

// }}}

// {{{ ItemManager
function ItemManager(mgr, arg, is_historic)
{
  this.manager = mgr;

  if (typeof(arg) == "number")
  {
    this.id = id;
    this.load_from_server();
  }
  else if (arg == null)
    this.id = null;
  else
    this.set_from_obj(arg, is_historic);

  this.timeout_id = null;
}




ItemManager.method("set_from_obj", function(arg, is_historic)
{
  this.id = arg.id;
  this.version_id = arg.version_id;
  this.tags = arg.tags;
  this.timestamp = arg.timestamp;
  this.contents = arg.contents;
  this.contents_html = arg.contents_html;

  this.all_day = arg.all_day;
  this.start_date = arg.start_date;
  this.end_date = arg.end_date;
  this.bump_interval = arg.bump_interval;
  this.hide_until = arg.hide_until;
  this.highlight_at = arg.highlight_at;

  this.is_historic = is_historic;
});



ItemManager.method("as_json", function()
{
  return {
    id: this.id,
    tags: this.tags,
    contents: this.contents,

    all_day: this.all_day,
    start_date: this.start_date,
    end_date: this.end_date,
    bump_interval: this.bump_interval,
    hide_until: this.hide_until,
    highlight_at: this.highlight_at
  }
});

ItemManager.method("call_with_item_div", function(inserter, when_created)
{
  inserter('<div id="item_[id]" class="item ui-corner-all"></div>'.replace('[id]', this.id));
  this.div = $("#item_"+this.id);

  if (when_created != undefined)
    when_created(this.div);
  this.fill_item_div();
});




ItemManager.method("fill_item_div", function(history)
{
  var self = this;

  if (self.id == null)
  {
    self.div.html(
      (
      '<div id="item_cursor_[id]" class="cursorfield">&nbsp;</div> '+
      '<div class="editcontrols ui-corner-all">'+
      '<div class="editcontrols_top">'+
      '<input type="button" id="new_[id]" value="New" class="editbutton"/>'+
      '</div>'+
      '</div>'
      ).allreplace('[id]', self.id)
      );
    $('#new_'+self.id).click(function(){ self.begin_edit() });
  }
  else
  {
    // {{{ generate history html, if requested / available
    if (history != null)
    {
      var hist_html = "";

      var hist_format = '<li class="[class]"><a id="hist_itemversion_[itemversion]">[date]</a> ([summary])</li>';
      for (var i = 0; i < history.length; ++i)
      {
        var hist_date = new Date(history[i].timestamp*1000);
        var itemcls = "";
        if (history[i].version_id == self.version_id)
          itemcls = "current_version";

        var summary;
        if (history[i].contents == null)
          summary = "deleted";
        else
          summary = history[i].contents.length + " characters";
        hist_html += (hist_format
        .allreplace("[itemversion]", history[i].version_id)
        .allreplace("[date]", hist_date.toLocaleString())
        .allreplace("[summary]", summary)
        .allreplace("[class]", itemcls)
        );
      }
      hist_html = '<ul>'+hist_html+"</ul>";
    }
    // }}}

    var contents_html = self.contents_html;
    if (contents_html == null)
      contents_html = "(deleted)";

    function get_date_info()
    {
      var date_info = "";
      var now = new Date();

      if (self.start_date)
        date_info += ('<span class="start-date">'
            +format_timestamp(self.start_date, self.all_day)+'</span>');
      if (self.end_date)
        date_info += ('<span class="end-date"> &mdash;'
            +format_timestamp(self.end_date, self.all_day)+'</span>');
      if (self.hide_until && now.getTime()/1000 < self.hide_until)
      {
        date_info += ('<span class="hide-date">Hidden until '
            +format_timestamp(self.hide_until)+'</span>');
      }

      if (date_info.length)
        return '<div class="date-info">'+date_info+'</div>';
      else
        return '';
    }

    // generate item html
    if (!self.is_historic)
    {
      self.div.html(
        (
        '<div id="item_cursor_[id]" class="cursorfield">&nbsp;</div> '+
        '<div class="editcontrols ui-corner-all item-drag-handle">'+
        '<div class="editcontrols_top">'+
        '<input type="button" id="edit_[id]" value="Edit" class="editbutton"/> '+
        '<input type="button" id="delete_[id]" value="Delete" class="deletebutton"/> '+
        '<span id="item_collapser_[id]" class="collapser"/> '+
        '<span class="item_handle"/> '+
        '<span id="item_history_button_[id]" class="item_history_button"/> '+
        ' [tags]'+
        '</div>'+
        '<div id="item_history_[id]" class="item_history ui-corner-all">'+hist_html+'</div>'+
        '</div>'+
        '[dateinfo]'+
        '<div id="item_contents_[id]" class="itemcontents">[contents]</div>'
        ).allreplace('[id]', self.id)
        .allreplace('[tags]', format_tag_links(self.tags))
        .allreplace('[contents]', contents_html)
        .allreplace('[dateinfo]', get_date_info())
        );
      $('#edit_'+self.id).click(function(){ self.begin_edit() });
      $('#delete_'+self.id).click(function(){ self.do_delete() });
    }
    else
    {
      self.div.html(
        (
        '<div id="item_cursor_[id]" class="cursorfield">&nbsp;</div> '+
        '<div class="editcontrols ui-corner-all">'+
        '<div class="editcontrols_top">'+
        '<input type="button" id="btn_revert_[id]" value="Revert"/> '+
        '<input type="button" id="btn_copy_to_present_[id]" value="Copy to Present"/> '+
        '<span id="item_collapser_[id]" class="collapser"/>'+
        '<span id="item_history_button_[id]" class="item_history_button"/> '+
        '[tags]'+
        '</div>'+
        '<div id="item_history_[id]" class="item_history ui-corner-all">'+hist_html+'</div>'+
        '</div>'+
        '[dateinfo]'+
        '<div id="item_contents_[id]" class="itemcontents">[contents]</div>'
        ).allreplace('[id]', self.id)
        .allreplace('[tags]', format_tag_links(self.tags))
        .allreplace('[contents]', contents_html)
        .allreplace('[dateinfo]', get_date_info())
        );
      $('#btn_revert_'+self.id).click(function()
        {
          var data = self.as_json();
          data.current_query = $("#search").val();

          $.ajax({
            type: 'POST',
            dataType: 'json',
            url: 'item/store',
            data: {json: JSON.stringify(data)},
            error: function(req, stat, err) { report_error("Revert failed."); },
            success: function(data, msg) {
              set_message("Revert successful.");
              update_tag_clouds();
            }
          });
        });
      $('#btn_copy_to_present_'+self.id).click(function()
        {
          var data = self.as_json();
          data.current_query = $("#search").val();

          $.ajax({
            type: 'POST',
            dataType: 'json',
            url: 'item/store',
            data: {json: JSON.stringify(data)},
            error: function(req, stat, err) { report_error("Copy failed."); },
            success: function(data, msg) {
              set_message("Copy successful.");
              update_tag_clouds();
            }
          });
        });
    }

    var query = "#item_[id] div.editcontrols .editcontrols_top a.taglink".replace("[id]", self.id);
    add_tag_behavior($(query));

    $("#item_collapser_"+self.id).click(
        function() { item_toggle_collapsed(self.div); }
        );
    $("#item_history_button_"+self.id).click(
        function() { self.toggle_history(); }
        );

    if (history != null)
    {
      var histdiv = $(self.div).find(".item_history");

      function bind_version_click_handler(ver_data, is_historic)
      {
        var ver_id = ver_data.version_id;
        $(histdiv).find("a#hist_itemversion_"+ver_id).click(
            function() {
              $.ajax({
                data: { version_id: ver_id },
                url: 'item/get_version_by_id',
                dataType:"json",
                success: function(data, status)
                {
                  self.set_from_obj(data, is_historic);
                  self.fill_item_div(history);
                },
                error: function(req, stat, err)
                { report_error("Error retrieving version."); },
            });
          });
      }

      for (var i = 0; i < history.length; ++i)
        bind_version_click_handler(history[i], i != 0);
    }

    if (self.highlight_at)
    {
      var now = new Date().getTime()/1000;

      if (now > self.highlight_at)
      {
        self.div.addClass("highlighted");
      }
      else
      {
        // set up a timer to highlight the element when it's time
        self.div.removeClass("highlighted");

        if (self.timeout_id != null)
          window.clearTimeout(self.timeout_id);

        var timeout_value = (self.highlight_at - now)*1000;
        if (timeout_value < 7*24*3600*1000) /* at most a week */
        {
          self.timeout_id = window.setTimeout(function () {
            self.div.addClass("highlighted");
          }, timeout_value);

          // make sure the timeout gets killed when the page is refilled
          self.manager.item_timeouts.push(self.timeout_id);
        }
      }
    }
  }
});


ItemManager.method("set_highlight_for_timestamp", function(timestamp)
{
  if (timestamp > self.highlight_at)
    self.div.addClass("highlighted");
  else
    self.div.removeClass("highlighted");
});


function item_toggle_collapsed(div)
{
  $(div).toggleClass("collapsed");
}


ItemManager.method("toggle_history", function()
{
  var self = this;

  if ($(self.div).hasClass("history_shown"))
  {
    $(self.div).removeClass("history_shown");
    // make sure we're showing the current version
    self.load_from_server(
      function() { self.fill_item_div(); }
      );
  }
  else
  {
    var histdiv = $(self.div).find(".item_history");

    histdiv.html(busy('Loading...'));
    $(self.div).addClass("history_shown");

    $.ajax({
      data: { item_id: self.id },
      url: 'item/history/get',
      dataType:"json",
      success: function(history, status)
      {
        self.fill_item_div(history);
      },
      error: function(req, stat, err)
      { histdiv.html('(Error retrieving history)'); }
      });

  }
})


var edit_count = 0;
ItemManager.method("begin_edit", function()
{
  ++edit_count;
  var self = this;

  var text_height;
  if (self.div.hasClass("editing"))
  {
    // a repeat edit, keep previous height
    text_height = self.div.find("textarea").height();
  }
  else
    text_height = self.div.find(".itemcontents").height();

  if (text_height < 150)
    text_height = 150;

  self.div.html(
    (
    '<div class="editcontrols ui-corner-all">'+
    '<input type="button"  id="edit_ok_[id]"  value="OK"  accesskey="o">&nbsp;'+
    '<input type="button" id="edit_cancel_[id]" value="Cancel" accesskey="c">&nbsp;'+
    '<input id="edit_tags_[id]" type="text" size="50"/>'+
    '</div>'+
    '<div class="itemcontents">'+
    '<textarea id="editor_[id]" cols="80"></textarea>'+
    '</div>'+
    '<div class="datecontrols">'+
    '<div class="whencontrols">'+
    '<label for="edit_date_[id]">Date:</label>'+
    '<input type="text" id="edit_date_[id]" size="15"/>'+
    '<label for="edit_end_[id]">End:</label>'+
    '<input type="text" id="edit_end_[id]" size="15"/>'+
    '<input type="checkbox" id="chk_all_day_[id]"/>'+
    '<label for="chk_all_day_[id]">All day</label>'+
    '</div>'+
    '<div class="remindcontrols">'+
    '<label for="edit_hide_until_[id]">Hide Until:</label>'+
    '<input type="text" id="edit_hide_until_[id]" size="15"/>'+
    '<label for="edit_highlight_at_[id]">Highlight at:</label>'+
    '<input type="text" id="edit_highlight_at_[id]" size="15"/>'+
    '</div>'+
    '<div class="bumpcontrols">'+
    '<label for="sel_bump_interval_[id]">Bump interval:</label>'+
    '<select id="sel_bump_interval_[id]" />'+
    '<input type="checkbox" id="chk_bump_and_copy_[id]" />'+
    '<label for="chk_bump_and_copy_[id]">Save, then bump new</label> '+
    '<input type="button" id="btn_bump_bwd_[id]" value="&lt; Bump"/>'+
    '<input type="button" id="btn_bump_fwd_[id]" value="Bump &gt;"accesskey="b"/>'+
    '</div>'+
    '</div>'
    ).allreplace("[id]",  self.id)
    );
  self.div.addClass("editing");

  // {{{ initial content setup

  // default to current search tags if new item
  if (self.id == null)
  {
    var default_tags = self.manager.query_tags.join(",");
    if (default_tags == "")
      $("#edit_tags_"+self.id).val("home");
    else
    {
      $("#edit_tags_"+self.id).val(default_tags);
    }
  }
  else
    $("#edit_tags_"+self.id).val(self.tags);

  $("#editor_"+self.id).val(self.contents);

  $("#editor_"+self.id).get(0).focus();
  $("#editor_"+self.id).height(text_height);

  function split( val ) { return val.split( /,\s*/ ); }
  function extractLast( term ) { return split(term).pop(); }

  $("#edit_tags_"+self.id)
    // don't navigate away from the field on tab when selecting an item
    .bind("keydown", function(event) {
      if ( event.keyCode === $.ui.keyCode.TAB &&
          $( this ).data( "autocomplete" ).menu.active ) {
        event.preventDefault();
      }
    })
    .autocomplete({
      minLength: 1,
      delay: 100,
      source: function(request, response) {
        $.getJSON("tags/get_filter", { q: extractLast(request.term) }, response);
      },
      focus: function() {
        // prevent value inserted on focus
        return false;
      },
      select: function(event, ui) {
        var terms = split(this.value);
        terms.pop();
        terms.push( ui.item.value );
        terms.push( "" );
        this.value = terms.join( "," );
        return false;
      }
    });

  // {{{ date - related

  $("#edit_date_"+self.id).datepicker({ constrainInput: false, showOn: 'button' });
  $("#edit_end_"+self.id).datepicker({ constrainInput: false, showOn: 'button' });
  $("#edit_hide_until_"+self.id).datepicker({ constrainInput: false, showOn: 'button' });
  $("#edit_highlight_at_"+self.id).datepicker({ constrainInput: false, showOn: 'button' });
  $(".ui-datepicker-trigger", self.div).attr("tabindex", -1);

  function set_date_val(name, value, all_day_affected)
  {
    if (value) $(name).val(format_editable_timestamp(
          value, all_day_affected && self.all_day));
  }

  $("#chk_all_day_"+self.id).get(0).checked = self.all_day;
  set_date_val("#edit_date_"+self.id, self.start_date, true);
  set_date_val("#edit_end_"+self.id, self.end_date, true);
  set_date_val("#edit_hide_until_"+self.id, self.hide_until, false);
  set_date_val("#edit_highlight_at_"+self.id, self.highlight_at, false);

  var bump_intv_html;

  for (var i in BUMP_INTERVALS)
  {
    bump_intv_html +=
      '<option value="'+BUMP_INTERVALS[i][0]+'">'+BUMP_INTERVALS[i][1]+"</option>";
  }

  $("#sel_bump_interval_"+self.id).html(bump_intv_html);
  if (self.bump_interval)
    $("#sel_bump_interval_"+self.id).val(self.bump_interval);

  // }}}

  // }}}

  self.div.get(0).scrollIntoView(false);

  // {{{ button responses

  // {{{ basic save functionality

  function save_item(options)
  {
    var tags = parse_tags($("#edit_tags_"+self.id).val());

    var new_id = self.id;
    if (typeof(new_id) != 'number')
      new_id = null;

    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: 'item/store',
      data: {json: JSON.stringify({
        id: new_id,
        tags: tags,

        contents: $("#editor_"+self.id).val(),
        current_query: $("#search").val(),

        all_day: $("#chk_all_day_"+self.id).get(0).checked,
        start_date: $("#edit_date_"+self.id).val(),
        end_date: $("#edit_end_"+self.id).val(),
        hide_until: $("#edit_hide_until_"+self.id).val(),
        highlight_at: $("#edit_highlight_at_"+self.id).val(),
        bump_interval: $("#sel_bump_interval_"+self.id).val()
      })},

      success: options["success"],
      error: options["error"],
    });
  }

  // }}}

  $("#edit_ok_"+self.id).click(function(){
    $("input", self.div).attr("disabled", true);

    self.manager.check_if_results_are_current();
    ++self.manager.up_to_date_check_inhibitions;

    var new_contents = $("#editor_"+self.id).val();

    save_item({
      error: function(req, stat, err)
      {
        self.div.removeClass("editing");

        --edit_count;
        alert("Saving failed.\n"+req.responseText);
        --self.manager.up_to_date_check_inhibitions;
        self.begin_edit();

        // preserve contents in case saving fails
        $("#editor_"+self.id).val(new_contents);
      },

      success: function(data, msg)
      {
        self.div.removeClass("editing");

        --edit_count;
        var prev_id = self.id;
        self.set_from_obj(data);
        self.id = data.id;
        self.call_with_item_div(function(html){ self.div.replaceWith(html); });
        self.manager.set_cursor_to(self.div);

        // Don't trigger change notification.
        //
        // There's a race condition here. Someone else might be changing items
        // while we are doing the same. Not very likely, though--ok for our
        // purposes.
        self.manager.update_result_hash_and_uninhibit_check();

        update_tag_clouds();
        if (prev_id == null)
        {
          self.manager.empty_was_filled();
        }
      }
    });
  });

  $("#edit_cancel_"+self.id).click(function(){
    --edit_count;
    self.div.removeClass("editing");
    self.fill_item_div();
    self.manager.redraw_cursor();
  });

  function bump(dir)
  {
    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: 'item/datebump',
      data: {json: JSON.stringify({
        id: self.id,
        bump_direction: dir,
        start_date: $("#edit_date_"+self.id).val(),
        end_date: $("#edit_end_"+self.id).val(),
        hide_until: $("#edit_hide_until_"+self.id).val(),
        highlight_at: $("#edit_highlight_at_"+self.id).val(),
        bump_interval: $("#sel_bump_interval_"+self.id).val()
      })},

      error: function(req, stat, err)
      {
        set_message("Bump server request failed.");
      },

      success: function(data, msg)
      {
        set_date_val("#edit_date_"+self.id, data.start_date);
        set_date_val("#edit_end_"+self.id, data.end_date);
        set_date_val("#edit_hide_until_"+self.id, data.hide_until);
        set_date_val("#edit_highlight_at_"+self.id, data.highlight_at);
      }
    });
  }

  function bump_button_action(dir)
  {
    if (!$("#chk_bump_and_copy_"+self.id).get(0).checked)
      bump(dir)
    else
    {
      $("input", self.div).attr("disabled", true);
      // save current, then bump, then edit again
      var new_contents = $("#editor_"+self.id).val();

      save_item({
        error: function(req, stat, err)
        {
          set_message("Saving failed.");
          self.begin_edit();

          // preserve contents in case saving fails
          $("#editor_"+self.id).val(new_contents);
        },

        success: function(data, msg)
        {
          self.set_from_obj(data);
          self.id = "post_bump_"+self.id;
          if (self.tags.indexOf("repeat") == "-1")
            self.tags.push("repeat");
          self.begin_edit();

          bump(dir);

          $("#chk_bump_and_copy_"+self.id).get(0).checked = true;
          if (dir > 0)
            $("#btn_bump_fwd_"+self.id).focus();
          else
            $("#btn_bump_bwd_"+self.id).focus();
        }
      });
    }
  }

  $("#btn_bump_fwd_"+self.id).click(function () { bump_button_action(1); } );
  $("#btn_bump_bwd_"+self.id).click(function () { bump_button_action(-1); } );

  // }}}
});




ItemManager.method("do_delete", function()
{
  var self = this;

  self.manager.set_cursor_to(self.div.next());
  self.div.remove();
  self.manager.check_if_results_are_current();
  ++self.manager.up_to_date_check_inhibitions;

  $.ajax({
    type: 'POST',
    dataType: 'json',
    url: 'item/store',
    data: {json: JSON.stringify({
      id: self.id,
      tags: [],
      contents: null
    })},
    error: function(req, stat, err) {
             report_error("Delete failed.");
             --self.manager.up_to_date_check_inhibitions;
           },
    success: function(data, msg) {
      // Don't trigger change notification.
      //
      // There's a race condition here. Someone else might be changing items
      // while we are doing the same. Not very likely, though--ok for our
      // purposes.
      self.manager.update_result_hash_and_uninhibit_check();
      update_tag_clouds();
    }
  });
});

ItemManager.method("load_from_server", function(when_done)
{
  var self = this;
  $.ajax({
    url: "item/get_by_id",
    data: {id: self.id},
    dataType:"json",
    success: function(obj, status)
    {
      self.set_from_obj(obj);
      if (when_done != undefined)
        when_done();
    },
    error: function(req, stat, err)
    {
      self.div.html('<div class="error">An error occurred.</div>');
    }
    });
});

// }}}

// {{{ ItemCollectionManager
function ItemCollectionManager()
{
  var self = this;
  self.div = $("#items");
  self.empty_item = new ItemManager(self);
  self.fill_sequence_number = 0;

  self.setup_history_handling();
  self.setup_search();
  self.setup_keyboard_nav();
  self.setup_toolbar();

  self.query_tags = [];

  self.item_timeouts = [];

  // catch out-of-date results
  window.setTimeout(function() { self.check_if_results_are_current() },
      UP_TO_DATE_TIMEOUT);
  $("#ood_reload_btn").click(function() {
    $("#out_of_date_notifier").addClass("ood_hidden");
    self.reload();
  })
  self.up_to_date_check_inhibitions = 0;

}




ItemCollectionManager.method("set_history_slider", function(time)
{
  var new_percentage;
  if (time == null || this.tsrange == undefined)
    new_percentage = 100.;
  else
    new_percentage = (time-this.tsrange.min)
      / (this.tsrange.max-this.tsrange.min)* 100.;

  ++this.slider_update_inhibitions;
  $("#history_slider").slider("value", new_percentage);
  --this.slider_update_inhibitions;
});




ItemCollectionManager.method("setup_history_handling", function()
{
  var self = this;

  self.tsrange = null;
  $.getJSON("timestamp/get_range", function (json)
    {
      self.tsrange = json;
      self.set_history_slider(self.view_time);
    });

  self.view_time = null;

  // setup history slider
  self.slider_update_inhibitions = 0;

  $("#history_slider").slider({
      slide: function(e, ui)
        {
          if (self.tsrange == null || self.slider_update_inhibitions)
            return;

          if (ui.value == 100)
            self.show_time(null);
          else
            var new_time = self.tsrange.min
              + ui.value/100.*(self.tsrange.max-self.tsrange.min);
            self.show_time(new_time);
        },
      change: function(e, ui)
        {
          if (self.tsrange == null || self.slider_update_inhibitions)
            return;

          if (ui.value == 100)
            self.set_time(null, "slider");
          else
          {
            var new_time = self.tsrange.min
              + ui.value/100.*(self.tsrange.max-self.tsrange.min);
            self.set_time(new_time, "slider");
          }
        },
      value: 100
      });

  // setup history datepicker
  $("#edit_date").datepicker();
  $("#edit_date").change(function()
      {
        var val = $("#edit_date").val();

        if (val == "")
          self.set_time(null);
        else
          self.set_time(Date.parse(val)/1000, "picker");
      });

  $("#btn_go_present").click(function()
    { self.set_time(null, "button"); });

  $("#edit_date").val('');
  $("#history_time").html('present');
});




ItemCollectionManager.method("get_current_fragment", function()
{
  // Need to double-escape because something is preventing unicode characters
  // in URLs.

  return escape(escape(JSON.stringify({
      query:$("#search").val(),
      timestamp:this.view_time
    })));
});




var nav_warning_inhibitor = 0;
ItemCollectionManager.method("add_history_item", function()
{
  ++nav_warning_inhibitor;
  var frag = this.get_current_fragment();
  dhtmlHistory.add(frag);
  --nav_warning_inhibitor;
});




ItemCollectionManager.method("handle_history_event", function(new_loc, dummy)
{
  if (new_loc != "")
  {
    new_loc = unescape(unescape(new_loc));
    if (new_loc[0] == "{")
    {
      var loc_descriptor = JSON.parse(new_loc);
      $("#search").val(loc_descriptor.query);
      this.set_time(loc_descriptor.timestamp, "history");
    }
    else
      set_search(new_loc, true);
  }
  else
  {
    $("#search").val("");
    this.set_time(null, "history");
  }
});




ItemCollectionManager.method("setup_search", function()
{
  var self = this;

  $("#search").change(function()
    {
      self.update();
    });
  $("#search").focus(function()
    {
      var last_search = $("#search").val();
      var unchanged_count = 0;
      var is_updated = true;

      self.div.everyTime("100ms", "search_changewatch",
        function()
        {
          var search = $("#search").val();
          if (search != last_search)
          {
            is_updated = false;
            last_search = search;
            unchanged_count = 0;
            return
          }

          if (!is_updated)
          {
            ++unchanged_count;

            if (unchanged_count > 3)
            {
              self.update();
              is_updated = true;
            }
          }
        });
      ++self.search_focused;
    });
  $("#search").blur(function()
    {
      self.div.stopTime("search_changewatch");
      self.add_history_item();
      self.update();
      --self.search_focused;
    });
  $("#btn_search_clear").click(function()
    {
      set_search("");
      $("#search").get(0).focus();
    });
});




ItemCollectionManager.method("setup_keyboard_nav", function()
{
  var self = this;
  self.cursor_at = null;
  self.search_focused = 0;

  $(document).keypress(function(ev)
    {
      var key = String.fromCharCode(ev.charCode);
      var handled = false;

      if (self.search_focused && ev.keyCode == 13)
      {
        $("#search").get(0).blur();
        return;
      }

      // don't take the kbd shortcut if an input is focused
      if ($("input:focus").length || $("textarea:focus").length)
        return true;

      if (key == "s" || key =="/")
      {
        $("#search").get(0).focus();
        handled = true;
      }

      if (key == "u")
      {
        self.reload();
        handled = true;
      }

      if (key == "c")
      {
        self.cursor_at.find(".editcontrols .collapser").click();
        handled = true;
      }

      if (self.cursor_at != null)
      {
        if (key == "j")
        {
          var successor = self.cursor_at.next();
          if (successor.length)
            self.set_cursor_to(successor, false);
          handled = true;
        }
        else if (key == "k")
        {
          var pred = self.cursor_at.prev();
          if (pred.length)
            self.set_cursor_to(pred, true);
          handled = true;
        }
        else if (key == "e")
        {
          self.cursor_at.find(".editcontrols .editcontrols_top .editbutton").click();
          handled = true;
        }
        else if (key == "h")
        {
          self.cursor_at.find(".editcontrols .editcontrols_top .item_history_button").click();
          handled = true;
        }
        else if (key == "D")
        {
          self.cursor_at.find(".editcontrols .editcontrols_top .deletebutton").click();
          handled = true;
        }
        else if (key == "n")
        {
          var new_item_div = $("#item_null");
          if (new_item_div.length)
          {
            self.set_cursor_to(new_item_div);
            self.cursor_at.find(".editcontrols .editcontrols_top .editbutton").click();
          }
          handled = true;
        }
      }

      return !handled;
    });
});




ItemCollectionManager.method("setup_toolbar", function()
{
  $("#btn_print").click(function()
    {
      var printurl = "items/print?query="+escape($("#search").val());
      if (self.view_time != null)
        printurl += "&max_timestamp="+escape(self.view_time.toString());

      window.open(printurl);
    });
  $("#btn_calendar").click(function()
    {
      window.open("calendar");
    });
  $("#btn_export").click(function()
    {
      var exporturl = "items/export?query="+escape($("#search").val());
      if (self.view_time != null)
        exporturl += "&max_timestamp="+escape(self.view_time.toString());

      window.open(exporturl);
    });
  $("#btn_expand").click(function()
    {
      $(".item").removeClass("collapsed");
    });
  $("#btn_collapse").click(function()
    {
      $(".item").addClass("collapsed");
    });
  $("#btn_quit").click(function()
    {
      location.href = "app/quit";
    });
  $("#btn_copy").click(function()
    {
      var linkurl = $("#linkurl");
      if (linkurl.hasClass("shown"))
      {
        linkurl.removeClass("shown");
      }
      else
      {
        linkurl.addClass("shown");
        var linkurl_edit = $("#linkurl_edit").get(0);
        linkurl_edit.select();
        linkurl_edit.focus();
      }
    });
});




ItemCollectionManager.method("redraw_cursor", function()
{
  if (this.cursor_at != null)
    this.set_cursor_to(this.cursor_at);
});




ItemCollectionManager.method("set_cursor_to", function(div, is_up, noscroll)
{
  if (this.cursor_at != null)
  {
    this.cursor_at.removeClass("focused");
  }

  div.addClass("focused");
  if (!noscroll)
    div.get(0).scrollIntoView(is_up);
  this.cursor_at = div;
});




ItemCollectionManager.method("note_list_emptied", function(item)
{
  this.cursor_at = null;
});




ItemCollectionManager.method("note_new_first_item", function(item)
{
  this.set_cursor_to(item.div, /* is_up */ true, /*noscroll*/ true);
});




ItemCollectionManager.method("show_time", function(new_time, origin)
{
  var dt = null;
  if (new_time != null)
  {
    dt = new Date(new_time*1000);
    $("#history_time").html(
      dt.getHours()
      +":"+zero_pad(dt.getMinutes().toFixed(0), 2)
      +":"+zero_pad(dt.getSeconds().toFixed(0), 2));
  }
  else
    $("#history_time").html('present');

  if (origin != "picker")
  {
    if (dt != null)
      $("#edit_date").val((dt.getMonth()+1)+"/"+dt.getDate()+"/"+dt.getFullYear());
    else
      $("#edit_date").val('');
  }
});




ItemCollectionManager.method("set_time", function(new_time, origin)
{
  this.view_time = new_time;
  this.update();
  this.show_time(new_time, origin);

  if (origin != "history")
    this.add_history_item();

  if (origin != "slider")
    this.set_history_slider(new_time);
});




ItemCollectionManager.method("realize_items", function(items)
{
  var self = this;
  self.div.html('')
  for (var i = 0; i<items.length; ++i)
    items[i].call_with_item_div(function(html) { self.div.append(html) });

  // only allow adding if we're in the present
  var have_empty_item = self.view_time == null;

  if (have_empty_item)
    self.empty_item.call_with_item_div(function(html) { self.div.append(html) });

  if (items.length)
    self.note_new_first_item(items[0]);
  else
  {
    if (have_empty_item)
      self.note_new_first_item(self.empty_item);
  }
});




ItemCollectionManager.method("empty_was_filled", function()
{
  var self = this;
  self.empty_item = new ItemManager(self);
  self.empty_item.call_with_item_div(function(html) { self.div.append(html) });
});




ItemCollectionManager.method("update", function(force)
{
  $("#linkurl_edit").val("#"+this.get_current_fragment());

  this.fill($("#search").val(), this.view_time, force);
})



ItemCollectionManager.method("reload", function()
{
  this.update(true);
})




ItemCollectionManager.method("fill", function(query, timestamp, force)
{
  if ($(".item .editing").length != 0)
  {
    if (confirm("You seem to be editing one or more entries. Continue loading?") == false)
      return;
  }

  var self = this;

  while (self.item_timeouts.length)
  {
    timeout = self.item_timeouts.pop();
    window.clearTimeout(timeout);
  }

  if (!force && query == self.last_query && timestamp == self.last_timestamp)
    return;

  self.div.html(busy('Loading...'));
  self.note_list_emptied();

  self.last_query = query;
  self.last_timestamp = timestamp;

  data = { query: query };

  if (!(timestamp == null || timestamp == undefined))
    data.max_timestamp = timestamp;

  ++self.fill_sequence_number;
  var seq_no = self.fill_sequence_number;

  $.ajax({
    data: data,
    url: 'items/get',
    dataType:"json",
    success: function(json, status)
    {
      if (seq_no != self.fill_sequence_number)
        return; // another fill was initiated before we completed, bail out.

      var jsonlist = json.list;

      var items = [];
      for (var i = 0; i < json.items.length; ++i)
      {
        items.push(new ItemManager(self, json.items[i], self.view_time != null));
      }
      self.realize_items(items);

      fill_subtag_cloud(json);
      self.query_tags = json.query_tags;
      self.last_query_data = data;
      self.result_hash = json.result_hash;

      $("#out_of_date_notifier").addClass("ood_hidden");
    },
    error: function(req, stat, err)
    {
      var msg = "Sorry, we encountered an error.";
      var longmsg = ''
      if (err != undefined)
        msg = msg + ' (' + err + ')';
      if (req.responseText != undefined)
        longmsg = req.responseText;

      self.div.html(('<div class="error"><div class="message">[msg]</div></div>'
          +'<div class="errordetail">[longmsg]</div>')
          .allreplace('[msg]', msg)
          .allreplace('[longmsg]', longmsg)
          );
    }
    });
})




ItemCollectionManager.method("check_if_results_are_current", function()
{
  var self = this;

  if (self.last_query_data && self.result_hash
    && self.up_to_date_check_inhibitions == 0)
  {
    $.ajax({
      data: self.last_query_data,
      url: 'items/get_result_hash',
      dataType:"json",
      success: function(json, status)
      {
        if (self.result_hash != json
          && self.up_to_date_check_inhibitions == 0)
        {
          $("#out_of_date_notifier").removeClass("ood_hidden");
        }
      }
    });
  }

  window.setTimeout(function() { self.check_if_results_are_current() },
      UP_TO_DATE_TIMEOUT);
});




ItemCollectionManager.method("update_result_hash_and_uninhibit_check", function()
{
  var self = this;

  if (!$("#out_of_date_notifier").hasClass("ood_hidden"))
  {
    // we are out of date, do nothing
    return
  }

  if (self.last_query_data && self.result_hash)
  {
    $.ajax({
      data: self.last_query_data,
      url: 'items/get_result_hash',
      dataType:"json",
      success: function(json, status)
      {
        self.result_hash = json;
        --self.up_to_date_check_inhibitions;
      },
      error: function()
      {
        --self.up_to_date_check_inhibitions;
      }
    });
  }
});

// }}}

// {{{ tag cloud

function is_valid_tag(tag)
{
  return tag.match(/^[.a-zA-Z0-9]+$/) != null;
}




function format_tag_links(tags, joiner)
{
  if (joiner == undefined)
    joiner = ", ";

  var result = '';
  for (var i = 0; i < tags.length; ++i)
  {
    result += '<a class="taglink tag-'+tags[i]+' ui-corner-all">'+tags[i]+'</a>';
    if (i < tags.length-1)
      result += joiner;
  }
  return result;
}




function make_tag_cloud(data, show_hidden, exclude)
{
  var max_usecount = 0;
  for (var i = 0; i < data.length; ++i)
  {
    var tag = data[i][0];
    var usecount = data[i][1];

    if (exclude != undefined && find_in_array(exclude, tag) != -1)
      continue;

    if (tag[0] == "." && !show_hidden)
      continue;

    if (usecount > max_usecount)
      max_usecount = usecount;
  }

  var html = '';
  for (var i = 0; i < data.length; ++i)
  {
    var tag = data[i][0];

    if (exclude != undefined && find_in_array(exclude, tag) != -1)
      continue;

    if (tag[0] == "." && !show_hidden)
      continue;

    var usecount = data[i][1];
    var usefraction = data[i][1]/max_usecount;
    var sizefraction = 1-Math.pow(1-usefraction, 0.8);
    var fontsize = Math.round(7.+usefraction*15);

    html += ('<a class="taglink tag-[tag]" style="font-size:[fs]pt">[tag]</a> '
      .allreplace("[fs]", fontsize)
      .allreplace("[tag]", tag));
  }

  return html;
}




function update_tag_clouds()
{
  update_main_tag_cloud();
  update_subtag_cloud();
}




function update_main_tag_cloud()
{
  $.getJSON("tags/get_for_query", function (json)
    {
      $("#tagcloud").html(make_tag_cloud(
          json.tags, $("#chk_tagcloud_show_hidden").get(0).checked));
      add_tag_behavior($("#tagcloud a"));
    });
}




function fill_subtag_cloud(data)
{
  $("#subtagcloud").html(
    make_tag_cloud(data.tags,
      $("#chk_subtagcloud_show_hidden").get(0).checked,
      data.query_tags));
  add_tag_behavior($("#subtagcloud a"));

  $("#subtagcloud_search_tags").html(
      format_tag_links(data.query_tags, " &middot; ")
      );
  add_tag_behavior($("#subtagcloud_search_tags a"));
}




function update_subtag_cloud()
{
  $.ajax({
    dataType: 'json',
    url: 'tags/get_for_query',
    data: { query: $("#search").val() },
    success: function(data, msg) { fill_subtag_cloud(data); }
  });
}




function parse_tags(taglist_str)
{
  var tags = taglist_str.split(",");
  var trimmed_tags = [];

  for (var i = 0; i < tags.length; ++i)
  {
    var trimmed = tags[i].trim();
    if (trimmed.length != 0)
      trimmed_tags.push(trimmed);
  }
  return trimmed_tags;
}




function set_search(search, no_hist_update)
{
  $("#search").val(search);
  $("#search").change();
  if (!no_hist_update)
    document.collection_manager.add_history_item();
}




function click_tag(tag)
{
  var search = $("#search").val();

  var idx = search.indexOf(tag);
  if (idx == -1)
  {
    if (search.length == 0)
      search = tag;
    else
      search = search + " " + tag;
  }
  else
  {
    search = search.replace(RegExp(re_escape("-"+tag+" "), "g"), "");
    search = search.replace(RegExp(re_escape(" -"+tag), "g"), "");
    search = search.replace(RegExp(re_escape(tag+" "), "g"), "");
    search = search.replace(RegExp(re_escape(" "+tag), "g"), "");
    search = search.replace(RegExp(re_escape(tag), "g"), "");
  }

  set_search(search);
}




function add_tag_behavior(jq_result)
{
  jq_result.click(function()
    {
      click_tag($(this).html());
    });
  jq_result.dblclick(function()
    { set_search($(this).html()); });
  jq_result.contextMenu("tag_context_menu", {
      bindings: {
        'tag-menu-rename': function(tag_html)
        {
          var old_name = $(tag_html).html();
          var new_name = prompt(
            "Rename tag '[old_name]' to:"
            .allreplace("[old_name]", old_name),
            old_name);
          if (new_name != undefined && new_name != old_name)
          {
            $.ajax({
              type: 'POST',
              dataType: 'text',
              url: 'tags/rename',
              data: {json: JSON.stringify({
                old_name: old_name,
                new_name: new_name
              })},
              error: function(req, stat, err) {
                alert("Rename failed.\n"+req.responseText);
              },
              success: function(data, msg) {
                set_message("Rename successful.");
                update_tag_clouds();
                document.collection_manager.update(true);
              }
            });
          }
        },
        'tag-menu-restrict': function(tag_html) {
          click_tag($(tag_html).html());
        },
        'tag-menu-search': function(tag_html) {
          set_search($(tag_html).html());
        }
      }
      });
}




function update_tag_cloud_height()
{
  var tc_height = (
      $(window).height()
      - $("#logo").height()
      - $("#history_nav").height()
      - $("#tagtab_header").height()
      - $("#tagcloud_hidden_control_1").height()
      - 95
      );

  if (tc_height < 100)
    tc_height = 100;

  $(".tagcloud").css("max-height", tc_height+"px");
}



// }}}




$(document).ready(function()
{
  var collection_manager = new ItemCollectionManager()
  document.collection_manager = collection_manager;

  tag_tabs = $("#navtabs").tabs();

  $("#items").sortable({
    handle: ".item-drag-handle",
    start: function(event, ui)
      { $("#item_null").appendTo("#hiddenitems"); },
    stop: function(event, ui)
      { $("#item_null").appendTo("#items"); },
    update: function(event, ui)
      {
        var items = $("#items").children()
        var item_ids = [];
        for (var i = 0; i < items.length; ++i)
          item_ids.push(items[i].id.replace("item_", ""));

        $.ajax({
          type: 'POST',
          dataType: 'text',
          url: 'item/reorder',
          data: {
            json: JSON.stringify({
              new_order: item_ids.join(","),
              current_search: $("#search").val()
            })},
          error: function(req, stat, err)
          { report_error("Reordering failed on server."); }
        });
      }
    });

  update_main_tag_cloud();
  $("#chk_tagcloud_show_hidden").change(update_main_tag_cloud);
  $("#chk_subtagcloud_show_hidden").change(update_subtag_cloud);

  dhtmlHistory.initialize();
  dhtmlHistory.addListener(
    function (new_loc, data)
    {
      collection_manager.handle_history_event(new_loc, data);
    });
  if (dhtmlHistory.isFirstLoad())
    collection_manager.handle_history_event(dhtmlHistory.getCurrentLocation(), null);

  $(window).resize(update_tag_cloud_height);
  update_tag_cloud_height();

  window.onbeforeunload = function(evt) {
    var e = e || window.event;

    if (nav_warning_inhibitor == 0 && edit_count)
    {
      var warning = "You seem to be editing one or more entries."
      evt.returnValue = warning;
      return warning
    }
  }
});


window.dhtmlHistory.create({
  toJSON: function(o)
  {
    return JSON.stringify(o);
  },
  fromJSON: function(s)
  {
    return JSON.parse(s);
  }
});

// vim: foldmethod=marker
