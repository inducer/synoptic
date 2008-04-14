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
                try:
                    result = markdown(text)
                except:
                    result = "*** MARKDOWN ERROR *** "+text;

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




class ViewOrderingEntry(object):
    def __init__(self, viewordering, item, weight):
        self.viewordering = viewordering
        self.item = item
        self.weight = weight

    def __repr__(self):
        return "<VOEntry item=%s, weight=%s>" % (self.item, self.weight)




# tools -----------------------------------------------------------------------
def find_tags(session, tags, create_them):
    if isinstance(tags, basestring):
        tags = [s.strip() for s in tags.split(",")]

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




def store_itemversion(dbsession, contents, tags, item_id=None, timestamp=None):
    import re
    from htmlentitydefs import name2codepoint

    if contents is not None:
        def replace_special_char(match):
            try:
                return unichr(name2codepoint[match.group(1)])
            except KeyError:
                return match.group(0)

        contents = re.sub(r"(?<!\\)\\([a-z0-9]+)", replace_special_char, contents)

    if item_id is None:
        item = Item()
        dbsession.save(item)
    else:
        assert isinstance(item_id, int)
        item = dbsession.query(Item).get(item_id)

    if timestamp is None:
        from time import time
        timestamp = time()

    itemversion = ItemVersion(
            item,
            timestamp,
            find_tags(dbsession, tags, create_them=True),
            contents,
            )
    dbsession.save(itemversion)

    return itemversion




# query rewrite visitor -------------------------------------------------------
class SQLifyQueryVisitor(object):
    def __init__(self, session):
        self.session = session

    def visit_tag_query(self, q):
        tags = self.session.query(Tag).filter_by(name=q.name)
        if tags.count() == 1:
            return ItemVersion.tags.any(id=tags[0].id)
        else:
            from sqlalchemy.sql import literal
            return literal(False)

    def visit_tag_wildcard_query(self, q):
        tags = self.session.query(Tag).filter(
                Tag.name.like(q.name.replace("?", "_").replace("*", "%")))

        cnt = tags.count()
        if cnt == 0:
            return literal(True)
        elif tags.count() == 1:
            return ItemVersion.tags.any(id=tags[0].id)
        else:
            from sqlalchemy.sql import or_
            return reduce(or_, 
                    (ItemVersion.tags.any(id=tag.id) for tag in tags))

    def visit_fulltext_query(self, q):
        return ItemVersion.contents.contains(q.substr)

    def visit_not_query(self, q):
        from sqlalchemy.sql import not_
        return not_(q.child.visit(self))

    def visit_and_query(self, q):
        from sqlalchemy.sql import and_
        return reduce(and_, (ch.visit(self) for ch in q.children))

    def visit_or_query(self, q):
        from sqlalchemy.sql import or_
        return reduce(or_, (ch.visit(self) for ch in q.children))

    def visit_date_query(self, q):
        if q.is_before:
            return ItemVersion.timestamp < q.timestamp
        else:
            return ItemVersion.timestamp > q.timestamp
