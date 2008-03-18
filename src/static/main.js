function busy(what)
{
  return '<img src="/static/busy.gif" alt="Busy" /> '+what;
}




function report_error(what)
{
  $("#errorlog").html(what);
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

ItemManager.method("append_item_div", function(where)
{
  where.append('<div id="item_[id]"></div>'.replace('[id]', this.id));
  this.div = $("#item_"+this.id);
  this.fill_item_div();
});


ItemManager.method("fill_item_div", function() 
{
  var self = this;

  if (this.id == null)
  {
    this.div.html(
      (
      '<div class="editcontrols">'+
      '<input type="button" id="new_[id]" value="New" accesskey="N">'+
      '</div>'
      ).allreplace('[id]', this.id)
      );
    $('#new_'+this.id).click(function(){ self.begin_edit() });
  }
  else 
  {
    if (this.manager.view_time == null)
    {
      this.div.html(
        (
        '<div class="editcontrols">'+
        '<input type="button" id="edit_[id]" value="Edit"> '+
        '<input type="button" id="delete_[id]" value="Delete"> '+
        'Tags: [tags]'+
        '</div>'+
        '<div>[contents]</div>'
        ).allreplace('[id]', this.id)
        .allreplace('[tags]', this.tags)
        .allreplace('[contents]', this.contents_html)
        );
      $('#edit_'+this.id).click(function(){ self.begin_edit() });
      $('#delete_'+this.id).click(function(){ self.do_delete() });
    }
    else
    {
      this.div.html(
        (
        '<div class="editcontrols">'+
        '<input type="button" id="btn_make_current_[id]" value="Revert"> '+
        '<input type="button" id="copy_to_present_[id]" value="Copy to Present"> '+
        'Tags: [tags]'+
        '</div>'+
        '<div>[contents]</div>'
        ).allreplace('[id]', this.id)
        .allreplace('[tags]', this.tags)
        .allreplace('[contents]', this.contents_html)
        );
    }
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
        tags: $("#edit_tags_"+self.id).val(),
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
        self.id = data.id;
        self.load_from_server(function(){self.fill_item_div(); });
        if (prev_id == null)
          self.manager.empty_was_filled();
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
  self.manager.note_delete(self);
  self.div.remove();

  $.ajax({
    type: 'POST',
    dataType: 'json',
    url: '/item/store',
    data: {json: JSON.stringify({
      id: self.id,
      tags: "",
      contents: null
    })},
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
  self.items = [];
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

  // setup history management
  self.tsrange = null;
  $.getJSON("/timestamp/get_range", function (json)
    { self.tsrange = json; });
  self.view_time = null;

  // setup history slider
  $("#history_slider").slider({
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
}

ItemCollectionManager.method("set_time", function(new_time, origin)
{
  if (this.tsrange == undefined)
  {
    report_error("Cannot set date until timestamp range has been received.");
    return;
  }

  this.view_time = new_time;
  this.update();

  var dt = null;
  if (new_time != null)
  {
    dt = new Date(new_time*1000);
    $("#history_time").html(dt.getHours()+":"+dt.getMinutes()+":"+dt.getSeconds());
  }
  else
    $("#history_time").html('');

  if (origin != "picker")
  {
    if (dt != null)
      $("#edit_date").setDatepickerDate(dt);
    else
      $("#edit_date").val("");
  }
  if (origin != "slider")
  {
    var new_percentage = (new_time-this.tsrange.min)
      / (this.tsrange.max-this.tsrange.min)* 100.
    this.set_time(new_time, "slider");
    $("#history_slider").slider("moveTo", new_percentage.toInt());
  }
});

ItemCollectionManager.method("realize_items", function(query)
{
  this.div.html('')
  for (var i = 0; i<this.items.length; ++i)
    this.items[i].append_item_div(this.div);

  // only allow adding if we're in the present
  if (this.view_time == null)
    this.empty_item.append_item_div(this.div);
});

ItemCollectionManager.method("empty_was_filled", function()
{
  this.items.push(this.empty_item);
  this.empty_item = new ItemManager(this);
  this.empty_item.append_item_div(this.div);
});

ItemCollectionManager.method("note_delete", function(item)
{
  this.items.splice(this.items.indexOf(item), 1);
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
  this.items = [];

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
      for (var i = 0; i < list.length; ++i)
      {
        self.items.push(new ItemManager(self, list[i]));
      }
      self.realize_items();
    },
    error: function(req, stat, err)
    {
      self.div.html('<div class="error">An error occurred.</div>');
    }
    });
})




// functions  ------------------------------------------------------------------
$(document).ready(function()
{
  document.item_manager = new ItemCollectionManager();
  document.item_manager.update();
});
