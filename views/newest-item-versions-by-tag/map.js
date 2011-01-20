function(doc)
{
  if (doc.type == "item_version")
  {
    for (var tag_idx in doc.tags)
      emit([doc.tags[tag_idx], doc.item_id], [doc.timestamp, doc._id]);
  }
}
