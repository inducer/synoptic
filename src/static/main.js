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
function ItemManager()
{
  this.id = null;
}

function ItemManager(arg)
{
  if (typeof(arg) == "number")
  {
    this.id = id;
    self.load_from_server();
  }
  else
  {
    this.id = arg.id;
    this.tags = arg.tags;
    this.title = arg.title;
    this.contents = arg.contents;
    this.contents_html = arg.contents_html;
  }
}

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
      '<input type="button" id="new_[id]" value="New" accesskey="N">'
      ).allreplace('[id]', this.id)
      );
    $('#new_'+this.id).click(function(){ self.begin_edit() });
  }
  else
  {
    this.div.html(
      (
      '<div class="editcontrols">'+
      '<input type="button" id="edit_[id]" value="Edit">'+
      '<input type="button" id="delete_[id]" value="Delete">'+
      'Tags: [tags]'+
      '</div>'+
      '<div>[title]</div>'+
      '<div>[contents]</div>'
      ).allreplace('[id]', this.id)
      .allreplace('[tags]', this.tags)
      .allreplace('[title]', this.title)
      .allreplace('[contents]', this.contents_html)
      );
    $('#edit_'+this.id).click(function(){ self.begin_edit() });
    $('#delete_'+this.id).click(function(){ self.do_delete() });
  }
});

ItemManager.method("begin_edit", function() 
{
  this.div.html(
    (
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
    '<div  id="edit_errors_[id]"  class="errors"></div>'
    ).allreplace("[id]",  this.id)
    );
  $("#edit_tags_"+this.id).val(this.tags);
  $("#editor_"+this.id).val(this.contents);
  $("#editor_"+this.id).focus();

  var self = this;
  $("#edit_ok_"+this.id).click(function(){
    $.ajax({
      type: "POST",
      url: "/item/store?_=1", // the _=1 switches on simple error reporting in paste
      data: {
        id: self.id,
        tags: $("#edit_tags_"+self.id).val(),
        title: "",
        dataType: "json",
        contents: $("#editor_"+self.id).val()
      },
      error: function(req, stat, err) {
        $("#edit_errors_"+self.id).html(req.responseText);
      },
      success: function(data, msg) {
        $("#edit_errors_"+self.id).html('');
        this.id = data.msg;
        self.load_from_server();
      }
    });
  });

  $("#edit_cancel_"+this.id).click(function(){
    self.fill_item_div();
  });
});

ItemManager.method("load_from_server", function(when_done) 
{
  var self = this;
  $.getJSON("/item/get_multi_by_tags", 
    {query: query, _:1}, 
    function(list, status)
    {
      for (var i = 0; i < list.length; ++i)
      {
        var newobj = new ItemManager(list[i]);
        self.items.push(newobj);
      }
      self.update();
      if (when_done != undefined)
        when_done();
    });
});




// ItemCollectionManager ----------------------------------------------------------------
function ItemCollectionManager()
{
  this.div = $("#items");
  this.items = [];
  this.empty_item = new ItemManager(null);
}

ItemCollectionManager.method("update", function(query)
{
  this.div.html('')
  for (var i = 0; i<this.items.length; ++i)
    this.items[i].append_item_div(this.div);
  this.empty_item.append_item_div(this.div);
});

ItemCollectionManager.method("fill_from_query", function(query)
{
  this.div.html('<img src="/static/busy.gif" alt="Busy" /> Loading...');

  this.items = [];

  var self = this;
  $.getJSON("/item/get_multi_by_tags", 
    {query: query, _:1}, 
    function(list, status)
    {
      for (var i = 0; i < list.length; ++i)
      {
        var newobj = new ItemManager(list[i]);
        self.items.push(newobj);
      }
      self.update();
    });
})




// functions  ------------------------------------------------------------------
$(document).ready(function()
{
  document.item_manager = new ItemCollectionManager();
  document.item_manager.fill_from_query("");
});
