from __future__ import with_statement
from zapp.datamodel import Item, ItemVersion, Tag, parse_tags




class DBSessionInjector(object):
    def __init__(self, sub_app, dburl):
        from sqlalchemy import create_engine
        self.engine = create_engine(dburl, echo=True)
        from zapp.datamodel import DataModel
        self.datamodel = DataModel()
        self.datamodel.metadata.create_all(self.engine) 

        from sqlalchemy.orm import sessionmaker
        self.sessionmaker = sessionmaker(bind=self.engine, autoflush=True, 
                transactional=True)

        self.sub_app = sub_app

    def __call__(self, environ, start_response):
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
                    (r'^/item/get_multi_by_tags$', self.get_multiple_items_by_tags),
                    (r'^/item/store$', self.store_item),
                    (r'^/static/([-_a-zA-Z0-9.]+)$', self.serve_static)
                    ])

        WSGIRequest.defaults["charset"] = "utf-8"

    def index(self, request):
        from zapp.html import mainpage, Context
        ctx = Context()
        return request.respond(mainpage(ctx))

    def get_multiple_items_by_tags(self, request):
        tags = parse_tags(request.dbsession, request.GET["query"])
        print tags
        query = request.dbsession.query(ItemVersion)
        for tag in tags:
            query = query.filter(ItemVersion.tags.any(id=tag.id))
        query = query.group_by('item_id')

        json = [
                {"id": itv.item.id, 
                    "tags": u",".join(tag.name for tag in itv.tags),
                    "title": itv.title,
                    "contents": itv.contents,
                    "contents_html": itv.contents,
                    }
                for itv in query
                ]

        from simplejson import dumps
        return request.respond(dumps(json))

    def store_item(self, request):
        item_id = int_or_null(request.POST["id"])

        if item_id is None:
            item = Item()
            request.dbsession.save(item)
        else:
            item = session.query(Item).get(item_id)

        from time import time
        itemversion = ItemVersion(
                item,
                time(),
                parse_tags(request.dbsession, request.POST["tags"]),
                request.POST["title"], 
                request.POST["contents"],
                )
        request.dbsession.save(itemversion)

        from simplejson import dumps
        return request.respond(dumps({"id": item.id}))

    def serve_static(self, request, filename):
        from os.path import splitext, join

        import zapp
        try:
            full_path = join(zapp.__path__[0], "static", filename)
            with open(full_path, "rb") as inf:
                data = inf.read()
        except IOError:
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

