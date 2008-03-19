from __future__ import with_statement
from synoptic.datamodel import Item, ItemVersion, Tag, parse_tags, find_tags




class DBSessionInjector(object):
    def __init__(self, sub_app, dburl):
        from sqlalchemy import create_engine
        self.engine = create_engine(dburl, echo=True)
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
        return Response(self.environ, self.start_response, *args, **kwargs)()




        
class ApplicationBase:
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





def int_or_null(val):
    try:
        return int(val)
    except ValueError:
        if val == "null":
            return None
        else:
            from paste.httpexceptions import HTTPBadRequest
            raise BadRequest("invalid integer_or_null parameter")




class Application(ApplicationBase):
    def __init__(self):
        ApplicationBase.__init__(self,
                [
                    (r'^/$', self.index),
                    (r'^/timestamp/get_range$', self.get_tsrange),
                    (r'^/item/get_by_id$', self.get_item_by_id),
                    (r'^/item/get_multi_by_tags$', self.get_multiple_items_by_tags),
                    (r'^/item/store$', self.store_item),
                    (r'^/tags/get$', self.get_tags),
                    (r'^/static/([-_/a-zA-Z0-9.]+)$', self.serve_static),
                    ])

        WSGIRequest.defaults["charset"] = "utf-8"

    # tools -------------------------------------------------------------------
    def item_to_json(self, item):
        result = item.as_json()

        if item.contents is not None:
            overrides = {
                    #'input_encoding': input_encoding,
                    'doctitle_xform': False,
                    'initial_header_level': 2,
                    }
            from docutils.core import publish_parts
            from wikisyntax import MyHTMLWriter
            parts = publish_parts(source=item.contents, 
                    writer=MyHTMLWriter(), settings_overrides=overrides)

            result['contents_html'] = parts['html_body']
        else:
            result['contents_html'] = None

        result['title'] = None
        return result

    def get_current_versions_query(self, model, max_timestamp=None):
        """Find the current version of all items."""

        from sqlalchemy.sql import select, and_, or_, not_, func

        result = select(
                [model.itemversions.c.id, 
                    func.max(model.itemversions.c.timestamp)])
                
        if max_timestamp is not None:
            result = result.where(model.itemversions.c.timestamp <= max_timestamp)

        result = result.group_by(model.itemversions.c.item_id)
        return result.alias("current_versions")

    # page handlers -----------------------------------------------------------
    def index(self, request):
        from synoptic.html import mainpage, Context
        ctx = Context()
        return request.respond(mainpage(ctx))

    def get_tsrange(self, request):
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

    def get_tags(self, request):
        from sqlalchemy.sql import select, and_, or_, not_, func

        model = request.datamodel

        if "max_timestamp" in request.GET:
            max_timestamp = float(request.GET["max_timestamp"])
        else:
            max_timestamp = None

        current_query = self.get_current_versions_query(model, max_timestamp)

        # twuc_q = tags_with_usecount_query
        twuc_q = (
                select([
                    model.tags.c.name, 
                    func.count(current_query.c.id).label("use_count"),
                        ],
                    from_obj=[model.itemversions_tags
                        .join(current_query, 
                            current_query.c.id==model.itemversions_tags.c.itemversion_id)
                        .join(model.tags)
                        ])
                )
        if "q" in request.GET:
            twuc_q = twuc_q.where(model.tags.c.name.like('%s%%' % request.GET["q"]))

        twuc_q = (twuc_q
                .group_by(model.tags.c.id)
                .having(func.count(current_query.c.id)>0)
                )
        if "limit" in request.GET:
            twuc_q = twuc_q.limit(int(request.GET["limit"]))

        result = request.dbsession.execute(twuc_q)

        if "withusecount" in request.GET:
            from simplejson import dumps

            data = [list(row) for row in result]

            return request.respond(
                    dumps({ 
                    "data": data,
                    "max_usecount": max(row[1] for row in data),
                    }),
                    mimetype="text/plain")
        else:
            return request.respond(u"\n".join(row[0] for row in result), 
                    mimetype="text/plain")

    def get_item_by_id(self, request):
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
        return request.respond(dumps(self.item_to_json(query.first())))

    def get_multiple_items_by_tags(self, request):
        tags = parse_tags(request.dbsession, request.GET["query"])

        model = request.datamodel

        from sqlalchemy.sql import select, and_, or_, not_, func

        tag_where = model.itemversions.c.contents != None
        for tag in tags:
            tag_where = and_(tag_where, ItemVersion.tags.any(id=tag.id))

        # find appropriate versions of items
        if "max_timestamp" in request.GET:
            max_timestamp = float(request.GET["max_timestamp"])
        else:
            max_timestamp = None

        current_query = self.get_current_versions_query(model, max_timestamp)

        # out of that, find all that have matching tags and are not deleted
        tag_query = (
                select([model.itemversions.c.id],
                    from_obj=[model.itemversions.join(
                        current_query,
                        current_query.c.id==model.itemversions.c.id)
                        ])
                .where(tag_where)
                .group_by(model.itemversions.c.item_id)
                )

        # now grab the ORMed instances
        versions = [request.dbsession.query(ItemVersion).get(row['id']) 
                for row in request.dbsession.execute(tag_query)]

        # and ship them out by JSON
        from simplejson import dumps
        return request.respond(dumps([self.item_to_json(v) for v in versions]))

    def store_item(self, request):
        from simplejson import loads, dumps
        data = loads(request.POST["json"])
        item_id = data["id"]

        if item_id is None:
            item = Item()
            request.dbsession.save(item)
        else:
            assert isinstance(item_id, int)
            item = request.dbsession.query(Item).get(item_id)

        from time import time
        itemversion = ItemVersion(
                item,
                time(),
                find_tags(request.dbsession, data["tags"]),
                data["contents"],
                )
        request.dbsession.save(itemversion)
        request.dbsession.commit()

        from simplejson import dumps
        return request.respond(dumps(self.item_to_json(itemversion)))

    def serve_static(self, request, filename):
        from os.path import splitext, join, normpath

        import synoptic
        root_path = join(synoptic.__path__[0], "static")

        try:
            full_path = normpath(join(root_path, filename))
            if not full_path.startswith(root_path):
                from paste.httpexceptions import HTTPForbidden
                raise HTTPForbidden()

            with open(full_path, "rb") as inf:
                data = inf.read()
        except IOError:
            print "NOT FOUND:", filename
            from paste.httpexceptions import HTTPNotFound
            raise HTTPNotFound()

        name, ext = splitext(filename)
        mimetypes = {
                ".jpg": "image/jpeg",
                ".png": "image/png",
                ".css": "text/css",
                ".js": "text/javascript",
                ".js": "text/javascript",
                }

        return request.respond(data, 
                mimetype=mimetypes.get(ext, "application/octet-stream"))

