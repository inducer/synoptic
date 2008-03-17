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
                Column('timestamp', Float),
                Column('title', UnicodeText()),
                Column('contents', UnicodeText())
                )

        self.itemversions_tags = Table('items_tags', self.metadata,
                Column('itemversion_id', Integer, ForeignKey('itemversions.id')),
                Column('tag_id', Integer, ForeignKey('tags.id')),
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




class Item(object):
    pass




class ItemVersion(object):
    def __init__(self, item, timestamp, tags, title, contents):
        self.item = item
        self.timestamp = timestamp
        self.tags = tags
        self.title = title
        self.contents = contents

    def copy(self, id=None, title=None, contents=None, timestamp=None):
        return Item(
                id=id or self.id,
                title=title or self.title,
                contents=contents or self.contents,
                timestamp=timestamp or self.timestamp,
                )




def parse_tags(session, tags_str):
    result = []
    for tag_str in [s.strip() for s in tags_str.split(",")]:
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
