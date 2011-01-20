function(doc)
{
  if (doc.type == "item_version")
  {
    emit([doc.item_id], [doc.timestamp, doc._id]);
  }
}
