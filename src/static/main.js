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
    timeout = "10s";

  $("#messagearea").oneTime(timeout, function()
      { my_msg.remove(); })
}

function report_error(what)
{
  set_message(what);
}




// String extension  -----------------------------------------------------------
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




// misc tools -----------------------------------------------------------------
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




// ItemManager  --------------------------------------------------------------------
function ItemManager(mgr, arg)
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
    this.set_from_obj(arg);
}




ItemManager.method("set_from_obj", function(arg)
{
  this.id = arg.id;
  this.tags = arg.tags;
  this.title = arg.title;
  this.contents = arg.contents;
  this.contents_html = arg.contents_html;
});




ItemManager.method("call_with_item_div", function(inserter, when_created)
{
  inserter('<div id="item_[id]" class="item"></div>'.replace('[id]', this.id));
  this.div = $("#item_"+this.id);

  if (when_created != undefined)
    when_created(this.div);
  this.fill_item_div();
});




ItemManager.method("fill_item_div", function() 
{
  var self = this;

  var have_dropzone = false;
  if (self.id == null)
  {
    have_dropzone = true;
    self.div.html(
      (
      '<div id="item_dropzone_[id]" class="dropzone">Drop here</div>'+
      '<div class="editcontrols">'+
      '<span id="item_cursor_[id]" class="cursorfield">&nbsp;</span> '+
      '<input type="button" id="new_[id]" value="New" class="editbutton"/>'+
      '</div>'
      ).allreplace('[id]', self.id)
      );
    $('#new_'+self.id).click(function(){ self.begin_edit() });
  }
  else 
  {
    if (self.manager.view_time == null)
    {
      have_dropzone = true;
      self.div.html(
        (
        '<div id="item_dropzone_[id]" class="dropzone">Drop here</div>'+
        '<div class="editcontrols">'+
        '<span id="item_cursor_[id]" class="cursorfield">&nbsp;</span> '+
        '<span id="item_collapser_[id]" class="collapser">&nbsp;</span> '+
        '<input type="button" id="edit_[id]" value="Edit" class="editbutton"/> '+
        '<input type="button" id="delete_[id]" value="Delete" class="deletebutton"/> '+
        '<div id="item_draghandle_[id]" class="draghandle">'+
          '<img src="/static/dragger.png" alt="drag handle" '+
          'title="Drag this handle to change display order"/>'+
        '</div> '+
        'Tags: [tags]'+
        '</div>'+
        '<div id="item_contents_[id]" class="itemcontents">[contents]</div>'
        ).allreplace('[id]', self.id)
        .allreplace('[tags]', format_tag_links(self.tags))
        .allreplace('[contents]', self.contents_html)
        );
      $('#edit_'+self.id).click(function(){ self.begin_edit() });
      $('#delete_'+self.id).click(function(){ self.do_delete() });
      $('#item_draghandle_'+self.id).draggable({
          helper: "clone",
          start: function() 
          { 
            self.manager.dragging_item = self; 
            self.div.addClass("dragging");
          },
          stop: function() 
          { 
            self.div.removeClass("dragging");
          }
          });
    }
    else
    {
      self.div.html(
        (
        '<div class="editcontrols">'+
        '<span id="item_cursor_[id]" class="cursorfield">&nbsp;</span> '+
        '<span id="item_collapser_[id]" class="collapser">&nbsp;</span> '+
        '<input type="button" id="btn_revert_[id]" value="Revert"/> '+
        '<input type="button" id="btn_copy_to_present_[id]" value="Copy to Present"/> '+
        'Tags: [tags]'+
        '</div>'+
        '<div id="item_contents_[id]" class="itemcontents">[contents]</div>'
        ).allreplace('[id]', self.id)
        .allreplace('[tags]', format_tag_links(self.tags))
        .allreplace('[contents]', self.contents_html)
        );
      $('#btn_revert_'+self.id).click(function()
        { 
          $.ajax({
            type: 'POST',
            dataType: 'json',
            url: 'item/store',
            data: {json: JSON.stringify({
              id: self.id,
              tags: self.tags,
              contents: self.contents,
              current_query: $("#search").val()
            })},
            error: function(req, stat, err) { report_error("Revert failed."); },
            success: function(data, msg) { 
              set_message("Revert successful."); 
              update_tag_clouds();
            }
          });
        });
      $('#btn_copy_to_present_'+self.id).click(function()
        { 
          $.ajax({
            type: 'POST',
            dataType: 'json',
            url: 'item/store',
            data: {json: JSON.stringify({
              id: null,
              tags: self.tags,
              contents: self.contents,
              current_query: $("#search").val()
            })},
            error: function(req, stat, err) { report_error("Copy failed."); },
            success: function(data, msg) { 
              set_message("Copy successful."); 
              update_tag_clouds();
            }
          });
        });
    }

    var query = "#item_[id] div.editcontrols a.taglink".replace("[id]", self.id);
    add_tag_behavior($(query));

    $("#item_collapser_"+self.id).click(
        function() { item_toggle_collapsed(self.div); }
        );
  }

  if (have_dropzone)
  {
    $("#item_dropzone_"+self.id).droppable({
      accept: ".draghandle",
      activeClass: 'dropzone-active',
      hoverClass:  'dropzone-hover',
      tolerance: 'pointer',
      drop: function(ev, ui) {
        var dragged_item = self.manager.dragging_item;
        if (self == dragged_item)
          return;

        // move dragged item's div in front of ours
        dragged_item.div.hide("slow",
          function()
          {
            dragged_item.div.remove();
            dragged_item.call_with_item_div(
              function(html) { self.div.before(html); } /* creator */
              );
            self.manager.set_cursor_to(dragged_item.div);
          });

        // report drag to server
        $.ajax({
          type: 'POST',
          dataType: 'text',
          url: 'item/reorder',
          data: {
            json: JSON.stringify({
              dragged_item: dragged_item.id,
              before_item: self.id,
              current_search: $("#search").val()
            })},
          error: function(req, stat, err) 
          { report_error("Reordering failed on server."); }
        });
      }
      });
  }
});


function item_toggle_collapsed(div)
{
  if ($(div).hasClass("collapsed"))
    $(div).removeClass("collapsed");
  else
    $(div).addClass("collapsed");
}


ItemManager.method("begin_edit", function() 
{
  var self = this;

  var text_height = self.div.find(".itemcontents").height();
  if (text_height < 150)
    text_height = 150;

  self.div.html(
    (
    '<div id="edit_div_[id]" class="edit_div">'+
    '<table>'+
    '<tr><td>'+
    '<input type="button"  id="edit_ok_[id]"  value="OK"  accesskey="o">&nbsp;'+
    '<input type="button" id="edit_cancel_[id]" value="Cancel" accesskey="c">&nbsp;'+
    '<label for="edit_tags_[id]" accesskey="t">Tags: </label><input id="edit_tags_[id]" type="text" size="50"/>'+
    '</td></tr>'+
    '<tr><td>'+
    '<textarea id="editor_[id]" cols="80"></textarea>'+
    '</td></tr>'+
    '</tr></table>'+
    '</div>'
    ).allreplace("[id]",  self.id)
    );

  // default to current search tags
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

  self.manager.install_focus_handlers($("#editor_"+self.id));
  $("#editor_"+self.id).get(0).focus();
  $("#editor_"+self.id).height(text_height);

  self.manager.install_focus_handlers($("#edit_tags_"+self.id));
  /*
  $("#edit_tags_"+self.id).autocomplete("tags/get",
      { delay: 100, multiple:true, autoFill: true, cacheLength:1 });
      */

  $("#edit_ok_"+self.id).click(function(){
    $("edit_div_"+self.id).html(busy('Saving...'));
    var tags = parse_tags($("#edit_tags_"+self.id).val());

    for (var i = 0; i<tags.length; ++i)
      if (!is_valid_tag(tags[i]))
      {
        alert("Invalid tag: '[tag]'".allreplace("[tag]", tags[i]));
        return;
      }

    self.contents = $("#editor_"+self.id).val();

    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: 'item/store',
      data: {json: JSON.stringify({
        id: self.id,
        tags: tags,
        contents: self.contents,
        current_query: $("#search").val()
      })},

      error: function(req, stat, err) 
      {
        set_message("Saving failed.");
        self.begin_edit();
      },

      success: function(data, msg) 
      {
        var prev_id = self.id;
        self.set_from_obj(data);
        self.id = data.id;
        self.call_with_item_div(function(html){ self.div.replaceWith(html); });
        self.manager.set_cursor_to(self.div);
        update_tag_clouds();
        if (prev_id == null)
        {
          self.manager.empty_was_filled();
        }
      }
    });
  });

  $("#edit_cancel_"+self.id).click(function(){
    self.fill_item_div();
    self.manager.redraw_cursor();
  });
});




ItemManager.method("do_delete", function()
{
  var self = this;

  self.manager.set_cursor_to(self.div.next());
  self.div.remove();

  $.ajax({
    type: 'POST',
    dataType: 'json',
    url: 'item/store',
    data: {json: JSON.stringify({
      id: self.id,
      tags: [],
      contents: null
    })},
    error: function(req, stat, err) { report_error("Delete failed."); },
    success: function(data, msg) { 
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




// ItemCollectionManager ----------------------------------------------------------------
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
  $("#history_slider").slider("moveTo", new_percentage);
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
      startValue: 100
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

  self.install_focus_handlers($("#edit_date"));
});




ItemCollectionManager.method("get_current_fragment", function()
{
  return escape(JSON.stringify({
      query:$("#search").val(),
      timestamp:this.view_time
    }));
});




ItemCollectionManager.method("add_history_item", function()
{
  dhtmlHistory.add(this.get_current_fragment());
});




ItemCollectionManager.method("handle_history_event", function(new_loc, dummy)
{
  if (new_loc != "")
  {
    new_loc = unescape(new_loc);
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
  /*
  $("#search").autocomplete("tags/get",
      { delay: 100, multiple:true, autoFill: true, cacheLength:1 });
      */
  $("#btn_search_clear").click(function()
    {
      set_search("");
      $("#search").get(0).focus();
    });

  self.install_focus_handlers($("#search"));
});




ItemCollectionManager.method("setup_keyboard_nav", function()
{
  var self = this;
  self.cursor_at = null;
  self.kb_shortcut_inhibitions = 0;
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

      if (self.kb_shortcut_inhibitions != 0)
        return true;

      if (key == "s" || key =="/")
        $("#search").get(0).focus();

      if (key == "c")
        self.cursor_at.find(".editcontrols .collapser").click();

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
          self.cursor_at.find(".editcontrols .editbutton").click();
        else if (key == "d")
          self.cursor_at.find(".editcontrols .deletebutton").click();
        else if (key == "n")
        {
          var new_item_div = $("#item_null");
          if (new_item_div.length)
          {
            self.set_cursor_to(new_item_div);
            self.cursor_at.find(".editcontrols .editbutton").click();
          }
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
  this.install_focus_handlers($("#linkurl_edit"));
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
    this.cursor_at.find(".editcontrols").removeClass("hascursor");
  }

  div.find(".editcontrols").addClass("hascursor");
  if (!noscroll)
    div.get(0).scrollIntoView(is_up);
  this.cursor_at = div;
});




ItemCollectionManager.method("install_focus_handlers", function(input_el)
{
  var self = this;
  input_el.focus(function(ev) 
    { 
      ++self.kb_shortcut_inhibitions; 
    });
  input_el.blur(function(ev) 
    { 
      --self.kb_shortcut_inhibitions; 
    });
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
    $("#history_time").html(dt.getHours()+":"+dt.getMinutes()+":"+dt.getSeconds());
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




ItemCollectionManager.method("fill", function(query, timestamp, force)
{
  if ($(".item .edit_div").length != 0)
  {
    if (confirm("You seem to be editing one or more entries. Continue loading?") == false)
      return;
  }

  var self = this;
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
        items.push(new ItemManager(self, json.items[i]));
      }
      self.realize_items(items);

      fill_subtag_cloud(json);
      self.query_tags = json.query_tags;
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




// tag cloud -------------------------------------------------------------------
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
    result += '<a class="taglink">'+tags[i]+'</a>';
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

    html += ('<a class="taglink" style="font-size:[fs]pt">[tag]</a> '
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
  $.getJSON("tags/get", function (json)
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
    url: 'tags/get',
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
        'rename': function(tag_html) 
        {
          var old_name = $(tag_html).html();
          var new_name = prompt(
            "Rename tag '[old_name]' to:"
            .allreplace("[old_name]", old_name),
            old_name);
          if (new_name != undefined && new_name != old_name)
          {
            if (!is_valid_tag(new_name))
              alert("Cannot rename--not a valid tag.");
            else
            {
              $.ajax({
                type: 'POST',
                dataType: 'text',
                url: 'tags/rename',
                data: {json: JSON.stringify({
                  old_name: old_name,
                  new_name: new_name
                })},
                error: function(req, stat, err) { report_error("Rename failed."); },
                success: function(data, msg) { 
                  set_message("Rename successful."); 
                  update_tag_clouds();
                  document.collection_manager.update(true);
                }
              });
            }
          }
        },
        'restrict': function(tag_html) {
          click_tag($(tag_html).html());
        },
        'search': function(tag_html) {
          set_search($(tag_html).html());
        }
      }
      });
}




// functions  ------------------------------------------------------------------
$(document).ready(function()
{
  var collection_manager = new ItemCollectionManager()
  document.collection_manager = collection_manager;

  $("#navtabs > ul").tabs();

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
