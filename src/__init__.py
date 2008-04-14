from synoptic.datamodel import \
        Item, ItemVersion, Tag, ViewOrdering, ViewOrderingEntry, \
        store_itemversion




def get_static_file(filename):
    from os.path import splitext, join, normpath

    import synoptic
    root_path = join(synoptic.__path__[0], "static")

    full_path = normpath(join(root_path, filename))
    if not full_path.startswith(root_path):
        from paste.httpexceptions import HTTPForbidden
        raise HTTPForbidden()

    inf = open(full_path, "rb")
    data = inf.read()
    inf.close()

    name, ext = splitext(filename)
    mimetypes = {
            ".jpg": "image/jpeg",
            ".png": "image/png",
            ".css": "text/css",
            ".txt": "text/plain",
            ".js": "text/javascript",
            ".js": "text/javascript",
            }

    if ext == ".txt":
        data = data.decode("utf-8")

    return (data, mimetypes.get(ext, "application/octet-stream"))




def import_file(dbsession, text):
    lines = text.split("\n")

    tags_label = "TAGS: "
    separator = 60*"-"

    from time import time
    timestamp = time()

    idx = 0
    while idx < len(lines):
        assert lines[idx].startswith(tags_label)
        tags = lines[idx][len(tags_label):]
        idx += 1

        body = []

        while idx < len(lines) and not lines[idx].startswith(separator):
            body.append(lines[idx])
            idx += 1

        idx += 1  # skip separator

        store_itemversion(dbsession, "\n".join(body), tags, timestamp=timestamp)

    dbsession.commit()




class DBSessionInjector(object):
    def __init__(self, sub_app, dburl, echo=False):
        from sqlalchemy import create_engine
        self.engine = create_engine(dburl)
        from synoptic.datamodel import DataModel
        self.datamodel = DataModel()
        self.datamodel.metadata.create_all(self.engine) 

        from sqlalchemy.orm import sessionmaker
        self.sessionmaker = sessionmaker(bind=self.engine, autoflush=True, 
                transactional=True)

        self.sub_app = sub_app

    def __call__(self, environ, start_response):
        session = environ["datamodel"] = self.datamodel
        session = environ["dbsession"] = self.sessionmaker()
        try:
            for item in self.sub_app(environ, start_response):
                yield item
            session.commit()
        except:
            session.rollback()
            raise




class ErrorMiddleware(object):
    def __init__(self, sub_app):
        self.sub_app = sub_app

    def __call__(self, environ, start_response):
        import sys

        try:
            return list(self.sub_app(environ, start_response))
        except:
            status = "500 Server Error"
            response_headers = [("content-type","text/plain")]
            exc_info = sys.exc_info()
            ex_type, ex_val, ex_tb = exc_info

            from traceback import print_exc
            print_exc()

            start_response(status, response_headers, exc_info)
            return ["%s: %s" % (ex_type.__name__,str(ex_val))]
        
from paste.wsgiwrappers import WSGIRequest, WSGIResponse




class Response(WSGIResponse):
    def __init__(self, environ, start_response, *args, **kwargs):
        self.environ = environ
        self.start_response = start_response

        WSGIResponse.__init__(self, *args, **kwargs)

    def __call__(self):
        return WSGIResponse.__call__(self, self.environ, self.start_response)





class Request(WSGIRequest):
    def __init__(self, environ, start_response):
        WSGIRequest.__init__(self, environ)
        self.start_response = start_response
        self.dbsession = environ["dbsession"]
        self.datamodel = environ["datamodel"]

    def respond(self, *args, **kwargs):
        resp = Response(self.environ, self.start_response, *args, **kwargs)
        return resp()




        
class ApplicationBase(object):
    def __init__(self, table):
        import re
        self.table = [
                (re.compile(match), dest)
                for match, dest in table
                ]

    def __call__(self, environ, start_response):
        for compiled_re, dest in self.table:
            match = compiled_re.search(environ["PATH_INFO"])
            if match is not None:
                result = dest(Request(environ, start_response), *match.groups())
                if isinstance(result, Response):
                    return result()
                else:
                    return result
        else:
            from paste.httpexceptions import HTTPNotFound
            raise HTTPNotFound()




class Application(ApplicationBase):
    def __init__(self):
        ApplicationBase.__init__(self,
                [
                    (r'^/$', self.index),
                    (r'^/timestamp/get_range$', self.http_get_tsrange),
                    (r'^/item/get_by_id$', self.http_get_item_by_id),
                    (r'^/items/get$', self.http_get_items),
                    (r'^/items/print$', self.http_print_items),
                    (r'^/items/export$', self.http_export_items),
                    (r'^/item/store$', self.http_store_item),
                    (r'^/item/reorder$', self.http_reorder_item),
                    (r'^/tags/get$', self.http_get_tags),
                    (r'^/tags/rename$', self.http_rename_tag),
                    (r'^/static/([-_/a-zA-Z0-9.]+)$', self.serve_static),
                    ])

        WSGIRequest.defaults["charset"] = "utf-8"

    # tools -------------------------------------------------------------------
    def item_to_json(self, item):
        result = item.as_json()

        result['contents_html'] = item.contents_html()
        result['title'] = None
        return result

    def get_current_itemversions_join(self, model, max_timestamp=None):
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

    def query_itemversions(self, session, model, parsed_query, max_timestamp=None):
        """Given parsed_query and max_timestamp, find the resulting ItemVersion ids,
        in the right order."""

        from sqlalchemy.sql import select, and_, or_, not_, func

        # find view ordering
        view_orderings = (session.query(ViewOrdering)
                .filter_by(tagset=str(parsed_query))
                .order_by(ViewOrdering.timestamp.desc())
                .limit(1)).all()

        # compose base set: the current versions of all items
        from_obj = self.get_current_itemversions_join(model, max_timestamp)

        if view_orderings:
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

        if view_orderings:
            # add the ordering clause
            result = result.order_by(vo_entries.c.weight)
        else:
            result = result.order_by(model.itemversions.c.timestamp.desc())

        return result.group_by(model.itemversions.c.item_id)

    def get_itemversions_for_request(self, request):
        from synoptic.query import parse_query
        parsed_query = parse_query(request.GET.get("query", ""))

        if "max_timestamp" in request.GET:
            max_timestamp = float(request.GET["max_timestamp"])
        else:
            max_timestamp = None

        session = request.dbsession
        model = request.datamodel

        # grab the ORMed instances
        return (session
                .query(ItemVersion)
                .from_statement(self.query_itemversions(
                    session, model, parsed_query, max_timestamp)))

    def get_json_items(self, session, model, parsed_query, max_timestamp):
        itemversions_query = self.query_itemversions(
                session, model, parsed_query, max_timestamp).alias("currentitemversions")

        # prepare eager loading of tags
        from sqlalchemy.sql import select
        iv_and_t_query = select([itemversions_query, model.tags],
                from_obj=[itemversions_query
                    .outerjoin(model.itemversions_tags, 
                        itemversions_query.c.id
                        ==model.itemversions_tags.c.itemversion_id)
                    .outerjoin(model.tags, 
                        model.itemversions_tags.c.tag_id
                        ==model.tags.c.id)
                    ],
                use_labels=True)

        last_id = None
        result = []
        for row in session.execute(iv_and_t_query):
            if last_id != row[itemversions_query.c.id]:
                last_id = row[itemversions_query.c.id]
                result.append(
                        {"id": row[itemversions_query.c.item_id],
                            "title": None,
                            "contents": row[itemversions_query.c.contents],
                            "contents_html": ItemVersion.htmlize(
                                row[itemversions_query.c.contents]),
                            "tags": [],
                            })
            if row[model.tags.c.name] is not None:
                result[-1]["tags"].append(row[model.tags.c.name])

        return result

    # page handlers -----------------------------------------------------------
    def index(self, request):
        from synoptic.html import mainpage, Context
        ctx = Context()
        return request.respond(mainpage(ctx))

    def http_get_tsrange(self, request):
        from time import time

        now = time()

        from simplejson import dumps
        return request.respond(
                dumps({
                    "min": request.dbsession.query(ItemVersion)
                    .min(ItemVersion.timestamp),
                    "max": max(now, request.dbsession.query(ItemVersion)
                    .max(ItemVersion.timestamp)),
                    "now": time(),
                    }),
                mimetype="text/plain")

    def get_tags_with_usecounts(self, session, model, parsed_query=None, 
            max_timestamp=None):
        from sqlalchemy.sql import select, and_, or_, not_, func

        if parsed_query is not None:
            itemversions_q = self.query_itemversions(session, model,
                    parsed_query, max_timestamp)
        else:
            itemversions_q = select([model.itemversions],
                    from_obj=[self.get_current_itemversions_join(
                        model, max_timestamp)
                        ])
                    
        itemversions_q = itemversions_q.alias("currentversions")

        # twuc_q stands for tags_with_usecount_query
        twuc_q = (
                select([
                    model.tags.c.name, 
                    func.count(itemversions_q.c.id).label("use_count"),
                        ],
                    from_obj=[model.itemversions_tags
                        .join(itemversions_q, 
                            itemversions_q.c.id==model.itemversions_tags.c.itemversion_id)
                        .join(model.tags)
                        ])
                )

        twuc_q = (twuc_q
                .group_by(model.tags.c.id)
                .having(func.count(itemversions_q.c.id)>0)
                .order_by(model.tags.c.name)
                )

        return session.execute(twuc_q)

    def http_get_tags(self, request):
        if "max_timestamp" in request.GET:
            max_timestamp = float(request.GET["max_timestamp"])
        else:
            max_timestamp = None

        query = request.GET.get("query", "")

        if query != "":
            from synoptic.query import parse_query
            parsed_query = parse_query(query)

            from synoptic.query import TagListVisitor
            query_tags = parsed_query.visit(TagListVisitor())
        else:
            parsed_query = None
            query_tags = []

        result = self.get_tags_with_usecounts(
                request.dbsession, request.datamodel, parsed_query,
                max_timestamp)

        from simplejson import dumps

        tags = [list(row) for row in result]

        return request.respond(
                dumps({ 
                "tags": tags,
                "query_tags": query_tags,
                "max_usecount": max([0] + [row[1] for row in tags]),
                }),
                mimetype="text/plain")

    def http_rename_tag(self, request):
        from simplejson import loads, dumps
        data = loads(request.POST["json"])

        old_name = data["old_name"]
        new_name = data["new_name"]

        tag = request.dbsession.query(Tag).filter_by(name=old_name).one()
        new_tag_query = request.dbsession.query(Tag).filter_by(name=new_name)
        
        if new_tag_query.count():
            raise ValueError, "tag already exsits"

        tag.name = new_name

        return request.respond("", mimetype="text/plain")

    def http_get_item_by_id(self, request):
        query = (
                request.dbsession.query(ItemVersion)
                .filter_by(item_id=int(request.GET["id"]))
                .order_by(ItemVersion.timestamp.desc())
                .filter(ItemVersion.contents != None)
                .limit(1)
                    )

        if query.count() == 0:
            from paste.httpexceptions import HTTPNotFound
            raise HTTPNotFound()

        from simplejson import dumps
        return request.respond(dumps(self.item_to_json(query.first())),
                mimetype="text/plain")

    def http_get_items(self, request):
        qry = request.GET.get("query", "")

        from synoptic.query import parse_query
        parsed_query = parse_query(qry)

        if "max_timestamp" in request.GET:
            max_timestamp = float(request.GET["max_timestamp"])
        else:
            max_timestamp = None

        json_items = self.get_json_items(
                request.dbsession, request.datamodel, 
                parsed_query, max_timestamp)

        if qry != "":
            tag_counter = {}
            for it in json_items:
                for tag in it["tags"]:
                    tag_counter[tag] = tag_counter.get(tag, 0) + 1

            tags = [list(it) for it in tag_counter.iteritems()]
            tags.sort()

            from synoptic.query import TagListVisitor
            query_tags = parsed_query.visit(TagListVisitor())
        else:
            # the empty query parses as "home", but we need to show
            # all tags, not just the ones relative to that,

            if "max_timestamp" in request.GET:
                max_timestamp = float(request.GET["max_timestamp"])
            else:
                max_timestamp = None

            tags = [list(row) 
                    for row in self.get_tags_with_usecounts(
                        request.dbsession, request.datamodel,
                        max_timestamp=max_timestamp)]

            query_tags = []

        # and ship them out by JSON
        from simplejson import dumps
        return request.respond(dumps({
            "items": json_items,
            "tags": tags,
            "query_tags": query_tags,
            "max_usecount": max([0] + [row[1] for row in tags]),
            }),
                mimetype="text/plain")

    def http_print_items(self, request):
        versions = self.get_itemversions_for_request(request)

        from html import printpage
        return request.respond(
                printpage({
                    "title": "Synoptic Printout",
                    "body": "<hr/>".join(v.contents_html() for v in versions),
                    }))

    def http_export_items(self, request):
        versions = self.get_itemversions_for_request(request)

        sep = (75*"-") + "\n"
        return request.respond(
                sep.join(
                    "TAGS: %s\n%s\n" % (
                        ",".join(tag.name for tag in v.tags),
                        v.contents)
                    for v in versions),
                mimetype="text/plain;charset=utf-8")

    def http_store_item(self, request):
        from simplejson import loads, dumps
        data = loads(request.POST["json"])

        itemversion = store_itemversion(request.dbsession, 
                data["contents"], data["tags"], data["id"])

        request.dbsession.commit() # fills in the item id

        from simplejson import dumps
        return request.respond(
                dumps(self.item_to_json(itemversion)),
                mimetype="text/plain")

    def http_reorder_item(self, request):
        from simplejson import loads
        data = loads(request.POST["json"])

        from synoptic.query import parse_query
        parsed_query = parse_query(data["current_search"])

        model = request.datamodel
        session = request.dbsession

        item_ids = [row[model.itemversions.c.item_id]
                for row in session.execute(
                self.query_itemversions(session, model, parsed_query)
                .alias("currentversions"))]

        def item_idx(sought_item_id):
            if sought_item_id == None:
                return len(item_ids)
            for idx, item_id in enumerate(item_ids):
                if item_id == sought_item_id:
                    return idx
            raise ValueError, "invalid item id supplied"

        dragged_item_idx = item_idx(data["dragged_item"])
        before_item_idx = item_idx(data["before_item"])

        assert dragged_item_idx != before_item_idx

        if before_item_idx < dragged_item_idx:
            dragged_item = item_ids.pop(dragged_item_idx)
            item_ids.insert(before_item_idx, dragged_item)
        else:
            item_ids.insert(before_item_idx, item_ids[dragged_item_idx])
            item_ids.pop(dragged_item_idx)

        from time import time

        viewordering = ViewOrdering(str(parsed_query), time())

        for idx, item_id in enumerate(item_ids):
            viewordering.entries.append(ViewOrderingEntry(viewordering, 
                session.query(Item).get(item_id), idx))
        session.save(viewordering)
        session.commit()

        return request.respond("", mimetype="text/plain")

    def serve_static(self, request, filename):
        try:
            data, mimetype = get_static_file(filename)
        except IOError:
            print "NOT FOUND:", filename
            from paste.httpexceptions import HTTPNotFound
            raise HTTPNotFound()

        return request.respond(data, mimetype=mimetype)
