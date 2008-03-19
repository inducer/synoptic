class DataModel(object):
    def __init__(self):
        from sqlalchemy import Table, Column, \
                Integer, Float, Text, UnicodeText, Unicode, ForeignKey, \
                MetaData

        self.metadata = MetaData()

        self.items = Table('items', self.metadata,
                Column('id', Integer, primary_key=True)
                )

        self.tags = Table('tags', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('name', Unicode(100)),
                ) 

        self.itemversions = Table('itemversions', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('item_id', Integer, ForeignKey('items.id')),
                Column('timestamp', Float, index=True),
                Column('contents', UnicodeText())
                )

        self.itemversions_tags = Table('itemversions_tags', self.metadata,
                Column('itemversion_id', Integer, ForeignKey('itemversions.id'), index=True),
                Column('tag_id', Integer, ForeignKey('tags.id'), index=True),
                ) 

        self.vieworderings = Table('vieworderings', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('tagset', Text()), # ascending, comma-separated list of tag ids
                Column('timestamp', Float, index=True),
                ) 

        self.viewordering_entries = Table('viewordering_entries', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('viewordering_id', Integer, ForeignKey('vieworderings.id')),
                Column('item_id', Integer, ForeignKey('items.id')),
                Column('weight', Integer),
                ) 

        from sqlalchemy.orm import mapper, relation

        mapper(Item, self.items, properties={
            'versions': relation(ItemVersion, backref='item'),
            })
        mapper(Tag, self.tags)
        mapper(ItemVersion, self.itemversions, properties={
            'tags':relation(Tag, secondary=self.itemversions_tags)
            })

        mapper(ViewOrdering, self.vieworderings, properties={
            'entries': relation(ViewOrderingEntry, backref='viewordering'),
            })
        mapper(ViewOrderingEntry, self.viewordering_entries, properties={
            'item': relation(Item),
            })



# mapped instances ------------------------------------------------------------
class Tag(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Tag '%s'>" % self.name

    def __hash__(self):
        return 0xaffe ^ hash(self.name)

    def __eq__(self, other):
        return self.name == other.name




class Item(object):
    def __repr__(self):
        return "<Item %s>" % self.id




_html_cache = {}
class ItemVersion(object):
    def __init__(self, item, timestamp, tags, contents):
        self.item = item
        self.timestamp = timestamp
        self.tags = tags
        self.contents = contents

    def as_json(self):
        return {"id": self.item.id, 
                "tags": [tag.name for tag in self.tags],
                "contents": self.contents,
                }

    def copy(self, item=None, timestamp=None, tags=None, contents=None):
        return Item(
                item=item or self.item,
                timestamp=timestamp or self.timestamp,
                tags=tags or self.tags,
                contents=contents or self.contents,
                )

    @staticmethod
    def htmlize(text):
        if text is not None:
            try:
                return _html_cache[text]
            except KeyError:
                import re
                text = re.sub(r"\~\~([^~]+)\~\~", r"<strike>\1</strike>", text)
                from synoptic.markdown import markdown
                result = markdown(text)

                _html_cache[text] = result
                return result
        else:
            return None

    def contents_html(self):
        return self.htmlize(self.contents)



class ViewOrdering(object):
    def __init__(self, tagset, timestamp):
        self.tagset = tagset
        self.timestamp = timestamp

    @staticmethod
    def make_tagset(tags):
        tags = list(tags)
        tags.sort(key=lambda tag: tag.id)
        ts = ",".join(str(tag.id) for tag in tags)
        return ts




class ViewOrderingEntry(object):
    def __init__(self, viewordering, item, weight):
        self.viewordering = viewordering
        self.item = item
        self.weight = weight

    def __repr__(self):
        return "<VOEntry item=%s, weight=%s>" % (self.item, self.weight)



# tools -----------------------------------------------------------------------
def find_tags(session, tags, create_them):
    result = []
    for tag_str in tags:
        if len(tag_str) == 0:
            continue

        tags = session.query(Tag).filter_by(name=tag_str)
        if tags.count():
            result.append(tags.one())
        else: 
            if create_them:
                new_tag = Tag(tag_str)
                session.save(new_tag)
                result.append(new_tag)
            else:
                result.append(Tag(tag_str))

    return result




def parse_tags(session, tags_str, create_them):
    return find_tags(session, 
            (s.strip() for s in tags_str.split(",")),
            create_them=create_them)
