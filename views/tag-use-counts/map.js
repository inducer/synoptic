function(doc)
{
  if (doc.type == "item_version")
    for (var tag_idx in doc.tags)
      emit(doc.tags[tag_idx], 1);
}
