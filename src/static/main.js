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
  inserter('<div id="item_[id]"></div>'.replace('[id]', this.id));
  this.div = $("#item_"+this.id);
  if (when_created != undefined)
    when_created(this.div);
  this.fill_item_div();
});


ItemManager.method("format_tag_links", function() 
{
  var result = '';
  for (var i = 0; i < this.tags.length; ++i)
  {
    result += '<a class="taglink">'+this.tags[i]+'</a>';
    if (i < this.tags.length-1)
      result += ', ';
  }
  return result;
});

ItemManager.method("fill_item_div", function() 
{
  var self = this;

  var have_dropzone = false;
  if (this.id == null)
  {
    have_dropzone = true;
    this.div.html(
      (
      '<div id="item_dropzone_[id]" class="dropzone">Drop here</div>'+
      '<div class="editcontrols">'+
      '<input type="button" id="new_[id]" value="New"/>'+
      '</div>'
      ).allreplace('[id]', this.id)
      );
    $('#new_'+this.id).click(function(){ self.begin_edit() });
  }
  else 
  {
    if (this.manager.view_time == null)
    {
      have_dropzone = true;
      this.div.html(
        (
        '<div id="item_dropzone_[id]" class="dropzone">Drop here</div>'+
        '<div class="editcontrols">'+
        '<div id="item_draghandle_[id]" class="draghandle">&uarr;&darr;</div> '+
        '<input type="button" id="edit_[id]" value="Edit"/> '+
        '<input type="button" id="delete_[id]" value="Delete"/> '+
        'Tags: [tags]'+
        '</div>'+
        '<div>[contents]</div>'
        ).allreplace('[id]', this.id)
        .allreplace('[tags]', this.format_tag_links())
        .allreplace('[contents]', this.contents_html)
        );
      $('#edit_'+this.id).click(function(){ self.begin_edit() });
      $('#delete_'+this.id).click(function(){ self.do_delete() });
      $('#item_draghandle_'+this.id).draggable({
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
      this.div.html(
        (
        '<div class="editcontrols">'+
        '<input type="button" id="btn_revert_[id]" value="Revert"/> '+
        '<input type="button" id="btn_copy_to_present_[id]" value="Copy to Present"/> '+
        'Tags: [tags]'+
        '</div>'+
        '<div>[contents]</div>'
        ).allreplace('[id]', this.id)
        .allreplace('[tags]', this.format_tag_links())
        .allreplace('[contents]', this.contents_html)
        );
      $('#btn_revert_'+this.id).click(function()
        { 
          $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '/item/store',
            data: {json: JSON.stringify({
              id: self.id,
              tags: self.tags,
              contents: self.contents
            })},
            error: function(req, stat, err) { report_error("Revert failed."); },
            success: function(data, msg) { 
              set_message("Revert successful."); 
              update_tag_cloud();
            }
          });
        });
      $('#btn_copy_to_present_'+this.id).click(function()
        { 
          $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '/item/store',
            data: {json: JSON.stringify({
              id: null,
              tags: self.tags,
              contents: self.contents
            })},
            error: function(req, stat, err) { report_error("Copy failed."); },
            success: function(data, msg) { 
              set_message("Copy successful."); 
              update_tag_cloud();
            }
          });
        });
    }

    var query = "#item_[id] div.editcontrols a.taglink".replace("[id]", this.id);
    make_tag_links($(query));
  }

  if (have_dropzone)
  {
    $("#item_dropzone_"+this.id).droppable({
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
          });

        // report drag to server
        $.ajax({
          type: 'POST',
          dataType: 'text',
          url: '/item/reorder',
          data: {json: JSON.stringify({
            dragged_item: dragged_item.id,
            before_item: self.id,
            current_search: parse_tags($("#search").val()),
          })},
          error: function(req, stat, err) 
          { report_error("Reordering failed on server."); },
          success: function(data, msg) { 
            set_message("Reordering OK."); 
          }
        });
      }
      });
  }
});

ItemManager.method("begin_edit", function() 
{
  this.div.html(
    (
    '<div id="edit_div_[id]" class="edit_div">'+
    '<table>'+
    '<tr><td>'+
    '<input type="button"  id="edit_ok_[id]"  value="OK"  accesskey="o">&nbsp;'+
    '<input type="button" id="edit_cancel_[id]" value="Cancel" accesskey="c">&nbsp;'+
    '<label for="edit_tags_[id]" accesskey="t">Tags: </label><input id="edit_tags_[id]" type="text" size="50"/>'+
    '</td></tr>'+
    '<tr><td>'+
    '<textarea id="editor_[id]" cols="80" rows="10"></textarea>'+
    '</td></tr>'+
    '</tr></table>'+
    '</div>'+
    '<div  id="edit_errors_[id]"  class="errors"></div>'
    ).allreplace("[id]",  this.id)
    );

  // default to current search tags
  if (this.id == null)
    $("#edit_tags_"+this.id).val($("#search").val());
  else
    $("#edit_tags_"+this.id).val(this.tags);

  $("#editor_"+this.id).val(this.contents);
  $("#editor_"+this.id).focus();
  $("#edit_tags_"+this.id).autocomplete("/tags/get",
      { delay: 100, multiple:true, autoFill: true, cacheLength:1 });

  var self = this;
  $("#edit_ok_"+this.id).click(function(){
    $("edit_div_"+self.id).html(busy('Saving...'));
    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: '/item/store',
      data: {json: JSON.stringify({
        id: self.id,
        tags: parse_tags($("#edit_tags_"+self.id).val()),
        contents: $("#editor_"+self.id).val()
      })},
      error: function(req, stat, err) {
        self.begin_edit();
        $("#edit_errors_"+self.id).html(req.responseText);
      },
      success: function(data, msg) 
      {
        var prev_id = self.id;
        $("#edit_errors_"+self.id).html('');
        self.set_from_obj(data);
        self.id = data.id;
        self.call_with_item_div(function(html){ self.div.replaceWith(html); });
        update_tag_cloud();
        if (prev_id == null)
        {
          self.manager.empty_was_filled();
        }
      }
    });
  });

  $("#edit_cancel_"+this.id).click(function(){
    self.fill_item_div();
  });
});

ItemManager.method("do_delete", function()
{
  var self = this;
  self.div.remove();

  $.ajax({
    type: 'POST',
    dataType: 'json',
    url: '/item/store',
    data: {json: JSON.stringify({
      id: self.id,
      tags: [],
      contents: null
    })},
    error: function(req, stat, err) { report_error("Delete failed."); },
    success: function(data, msg) { 
      set_message("Delete successful."); 
      update_tag_cloud();
    }
  });
});

ItemManager.method("load_from_server", function(when_done) 
{
  var self = this;
  $.ajax({
    url: "/item/get_by_id", 
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

  // set up search field
  $("#search").change(function()
    {
      self.update();
    });
  $("#search").focus(function()
    {
      self.div.everyTime("250ms", "search_changewatch",
        function() { self.update(); });
    });
  $("#search").blur(function()
    {
      self.div.stopTime("search_changewatch");
    });
  $("#search").autocomplete("/tags/get",
      { delay: 100, multiple:true, autoFill: true, cacheLength:1 });
  $("#btn_search_clear").click(function()
    {
      $("#search").val('');
      $("#search").change();
      $("#search").focus();
    });
  $("#btn_print").click(function()
    {
      var printurl = "/item/print_multi_by_tags?query="+escape($("#search").val());
      if (self.view_time != null)
        printurl += "&max_timestamp="+escape(self.view_time.toString());

      window.open(printurl);
    });

  // setup history management
  self.tsrange = null;
  $.getJSON("/timestamp/get_range", function (json)
    { self.tsrange = json; });
  self.view_time = null;

  // setup history slider
  $("#history_slider").slider({
      slide: function(e, ui)
        {
          if (self.tsrange == null)
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
          if (self.tsrange == null)
            return;

          if (ui.value == 100)
            self.set_time(null, "slider");
          else
            var new_time = self.tsrange.min 
              + ui.value/100.*(self.tsrange.max-self.tsrange.min);
            self.set_time(new_time, "slider");
        },
      startValue: 100,
      });

  // setup history datepicker
  $("#edit_date").datepicker();

  $("#btn_go_present").click(function()
    { self.set_time(null, "button"); });

  $("#edit_date").val('');
  $("#history_time").html('present');
}

ItemCollectionManager.method("show_time", function(new_time)
{
  if (this.tsrange == undefined)
  {
    report_error("Cannot set date until timestamp range has been received.");
    return;
  }

  var dt = null;
  if (new_time != null)
  {
    dt = new Date(new_time*1000);
    $("#history_time").html(dt.getHours()+":"+dt.getMinutes()+":"+dt.getSeconds());
  }
  else
    $("#history_time").html('present');

  if (dt != null)
    $("#edit_date").val((dt.getMonth()+1)+"/"+dt.getDate()+"/"+dt.getFullYear());
  else
    $("#edit_date").val('');
});

ItemCollectionManager.method("set_time", function(new_time, origin)
{
  if (this.tsrange == undefined)
  {
    report_error("Cannot set date until timestamp range has been received.");
    return;
  }

  this.view_time = new_time;
  this.update();
  this.show_time(new_time);

  if (origin != "slider")
  {
    var new_percentage = (new_time-this.tsrange.min)
      / (this.tsrange.max-this.tsrange.min)* 100.
    this.set_time(new_time, "slider");
    $("#history_slider").slider("moveTo", new_percentage.toInt());
  }
});

ItemCollectionManager.method("realize_items", function(items)
{
  var self = this;
  self.div.html('')
  for (var i = 0; i<items.length; ++i)
    items[i].call_with_item_div(function(html) { self.div.append(html) });

  // only allow adding if we're in the present
  if (self.view_time == null)
    self.empty_item.call_with_item_div(function(html) { self.div.append(html) });
});

ItemCollectionManager.method("empty_was_filled", function()
{
  var self = this;
  self.empty_item = new ItemManager(self);
  self.empty_item.call_with_item_div(function(html) { self.div.append(html) });
});

ItemCollectionManager.method("update", function()
{
  this.fill($("#search").val(), this.view_time);
})

ItemCollectionManager.method("fill", function(query, timestamp)
{
  if (query == this.last_query && timestamp == this.last_timestamp)
    return;

  this.div.html(busy('Loading...'));

  this.last_query = query;
  this.last_timestamp = timestamp;

  data = { query: query };

  if (!(timestamp == null || timestamp == undefined))
    data.max_timestamp = timestamp;

  var self = this;

  $.ajax({
    data: data,
    url: '/item/get_multi_by_tags',
    dataType:"json",
    success: function(list, status)
    {
      var items = [];
      for (var i = 0; i < list.length; ++i)
      {
        items.push(new ItemManager(self, list[i]));
      }
      self.realize_items(items);
    },
    error: function(req, stat, err)
    {
      self.div.html('<div class="error">An error occurred.</div>');
    }
    });
})




// tag cloud -------------------------------------------------------------------
function update_tag_cloud()
{
  $.getJSON("/tags/get?withusecount", function (json)
    {  
      var html = '';
      for (var i = 0; i < json.data.length; ++i)
      {
        var tag = json.data[i][0];
        var usecount = json.data[i][1];
        var usefraction = json.data[i][1]/json.max_usecount;
        var sizefraction = 1-Math.pow(1-usefraction, 2);
        var fontsize = Math.round(8.+usefraction*15);

        html += ('<a class="taglink" style="font-size:[fs]pt">[tag]</a> '
          .allreplace("[fs]", fontsize)
          .allreplace("[tag]", tag));
      }

      $("#tagcloud").html(html);
      make_tag_links($("#tagcloud a"));
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

function click_tag(tag)
{
  var tags = parse_tags($("#search").val());

  var idx = tags.indexOf(tag);
  if (idx == -1)
    tags.push(tag);
  else
    tags.pop(idx);

  $("#search").val(tags.join(", "));
  $("#search").change();
}

function make_tag_links(jq_result)
{
  jq_result.click(function()
    {
      click_tag($(this).html());
    });
}




// functions  ------------------------------------------------------------------
$(document).ready(function()
{
  document.item_manager = new ItemCollectionManager();
  document.item_manager.update();

  $("#navtabs > ul").tabs();

  update_tag_cloud();
});
