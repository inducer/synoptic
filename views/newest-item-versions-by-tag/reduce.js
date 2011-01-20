function(keys, values, rereduce)
{
  var max_time = 0;
  var max_item = null;
  for (var i in values)
  {
    var item_time = values[i][0];
    if (item_time > max_time)
    {
      max_item = values[i][1];
      max_time = item_time;
    }
  }
  return [max_time, max_item];
}
