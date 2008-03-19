class DataModel(object):
    def __init__(self):
        from sqlalchemy import Table, Column, \
                Integer, Float, UnicodeText, Unicode, ForeignKey, \
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

        self.itemversions_tags = Table('items_tags', self.metadata,
                Column('itemversion_id', Integer, ForeignKey('itemversions.id'), index=True),
                Column('tag_id', Integer, ForeignKey('tags.id'), index=True),
                ) 

        from sqlalchemy.orm import mapper, relation

        mapper(Item, self.items, properties={
            'versions': relation(ItemVersion, backref='item'),
            })
        mapper(Tag, self.tags)
        mapper(ItemVersion, self.itemversions, properties={
            'tags':relation(Tag, secondary=self.itemversions_tags)
            })



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
    pass




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




def find_tags(session, tags):
    result = []
    for tag_str in tags:
        if len(tag_str) == 0:
            continue

        tags = session.query(Tag).filter_by(name=tag_str)
        if tags.count():
            result.append(tags.one())
        else:
            new_tag = Tag(tag_str)
            session.save(new_tag)
            result.append(new_tag)

    return result




def parse_tags(session, tags_str):
    return find_tags(session, (s.strip() for s in tags_str.split(",")))
