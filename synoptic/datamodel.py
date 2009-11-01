MAPPERS_DEFINED = [False]




class DataModel(object):
    def __init__(self):
        if MAPPERS_DEFINED[0]:
            return

        MAPPERS_DEFINED[0] = True

        from sqlalchemy import Table, Column, \
                Integer, Float, Text, UnicodeText, Unicode, ForeignKey, \
                MetaData

        cls = DataModel

        cls.metadata = MetaData()

        cls.items = Table('items', self.metadata,
                Column('id', Integer, primary_key=True)
                )

        cls.tags = Table('tags', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('name', Unicode(100)),
                )

        cls.itemversions = Table('itemversions', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('item_id', Integer, ForeignKey('items.id')),
                Column('timestamp', Float, index=True),
                Column('contents', UnicodeText())
                )

        cls.itemversions_tags = Table('itemversions_tags', self.metadata,
                Column('itemversion_id', Integer, ForeignKey('itemversions.id'), index=True),
                Column('tag_id', Integer, ForeignKey('tags.id'), index=True),
                )

        cls.vieworderings = Table('vieworderings', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('tagset', Text()), # misnomer, by now: normalized query string
                Column('timestamp', Float, index=True),
                )

        cls.viewordering_entries = Table('viewordering_entries', self.metadata,
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
                "version_id": self.id,
                "timestamp": self.timestamp,
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
                session.add(new_tag)
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

        contents = re.sub(r"(?<!\\)\\([A-Za-z0-9]+)", replace_special_char, contents)

    if item_id is None:
        item = Item()
        dbsession.add(item)
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
    dbsession.add(itemversion)

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





# query helpers ---------------------------------------------------------------
def get_current_itemversions_join(model, max_timestamp=None):
    """Find the current version of all items."""

    from sqlalchemy.sql import select, and_, or_, not_, func

    max_timestamps_per_item = select(
            [model.itemversions.c.item_id,
                func.max(model.itemversions.c.timestamp).label("max_timestamp")])

    if max_timestamp is not None:
        max_timestamps_per_item = max_timestamps_per_item.where(
                model.itemversions.c.timestamp <= max_timestamp+1)

    max_timestamps_per_item = max_timestamps_per_item.group_by(
            model.itemversions.c.item_id)
    max_timestamps_per_item = max_timestamps_per_item.alias("max_ts")

    return model.itemversions.join(max_timestamps_per_item,
                and_(
                    max_timestamps_per_item.c.item_id
                      ==model.itemversions.c.item_id,
                    max_timestamps_per_item.c.max_timestamp
                      ==model.itemversions.c.timestamp,
                    ))




def query_itemversions(session, model, parsed_query, max_timestamp=None):
    """Given parsed_query and max_timestamp, find the resulting ItemVersion ids,
    in the right order."""

    from sqlalchemy.sql import select, and_, or_, not_, func

    # find view ordering
    view_orderings = (session.query(ViewOrdering)
            .filter_by(tagset=str(parsed_query))
            .order_by(ViewOrdering.timestamp.desc())
            .limit(1)).all()

    if view_orderings:
        have_view_ordering = len(view_orderings[0].entries) != 0
    else:
        have_view_ordering = False

    # compose base set: the current versions of all items
    from_obj = get_current_itemversions_join(model, max_timestamp)

    if have_view_ordering:
        # if we have an ordering, we must also join the viewordering_entries table
        # so we can order by weight

        vo_entries = (
                select([model.viewordering_entries])
                .where(model.viewordering_entries.c.viewordering_id
                    ==view_orderings[0].id)).alias("vo_entries")

        from_obj = from_obj.outerjoin(vo_entries,
                model.itemversions.c.item_id==vo_entries.c.item_id)

    from synoptic.datamodel import SQLifyQueryVisitor
    where = and_(
            model.itemversions.c.contents != None,
            parsed_query.visit(SQLifyQueryVisitor(session))
            )

    result = select([model.itemversions], from_obj=[from_obj]).where(where)

    if have_view_ordering:
        # add the ordering clause
        result = result.order_by(vo_entries.c.weight)
    else:
        result = result.order_by(model.itemversions.c.timestamp.desc())

    return result.group_by(model.itemversions.c.item_id)




# view ordering handler -------------------------------------------------------
class ViewOrderingHandler:
    def __init__(self, session, model, parsed_query):
        self.session = session
        self.model = model
        self.parsed_query = parsed_query

    def __len__(self):
        return len(self.item_ids)

    def has_ordering(self):
        view_orderings = (self.session.query(ViewOrdering)
                .filter_by(tagset=str(self.parsed_query))
                .order_by(ViewOrdering.timestamp.desc())
                .limit(1)).all()

        if view_orderings:
            return len(view_orderings[0].entries) != 0
        else:
            return False

    def load(self):
        self.item_ids = [row[self.model.itemversions.c.item_id]
                for row in self.session.execute(
                query_itemversions(self.session,
                    self.model, self.parsed_query)
                .alias("currentversions"))]

    def __contains__(self, sought_item_id):
        return sought_item_id in self.item_ids

    def index_from_id(self, sought_item_id):
        if sought_item_id == None:
            return len(self.item_ids)
        for idx, item_id in enumerate(self.item_ids):
            if item_id == sought_item_id:
                return idx
        raise ValueError, "invalid item id supplied"

    def reorder(self, moved_idx, before_idx):
        assert moved_idx != before_idx

        if before_idx < moved_idx:
            dragged_item = self.item_ids.pop(moved_idx)
            self.item_ids.insert(before_idx, dragged_item)
        else:
            self.item_ids.insert(before_idx, self.item_ids[moved_idx])
            self.item_ids.pop(moved_idx)

    def set_order(self, item_ids):
        self.item_ids = item_ids

    def insert(self, before_idx, new_id):
        self.item_ids.insert(before_idx, new_id)

    def delete(self):
        from time import time

        viewordering = ViewOrdering(str(self.parsed_query), time())
        session.add(viewordering)
        session.commit()

    def save(self):
        from time import time

        viewordering = ViewOrdering(str(self.parsed_query), time())

        for idx, item_id in enumerate(self.item_ids):
            viewordering.entries.append(ViewOrderingEntry(viewordering,
                self.session.query(Item).get(item_id), idx))
        self.session.add(viewordering)
