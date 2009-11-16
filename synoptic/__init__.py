from synoptic.datamodel import \
        Item, ItemVersion, Tag, ViewOrdering, ViewOrderingEntry, \
        store_itemversion,  \
        get_current_itemversions_join, \
        query_itemversions




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
                autocommit=False)

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

        from paste.httpexceptions import HTTPException

        try:
            return list(self.sub_app(environ, start_response))
        except HTTPException, e:
            return e(environ, start_response)
        except:
            status = "500 Server Error"
            response_headers = [("content-type","text/plain")]
            exc_info = sys.exc_info()
            ex_type, ex_val, ex_tb = exc_info

            from traceback import print_exc
            try:
                print_exc()
            except:
                pass

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
    def __init__(self, table, allowed_networks=[]):
        import re
        self.table = [
                (re.compile(match), dest)
                for match, dest in table
                ]

        self.allowed_networks = allowed_networks

    def __call__(self, environ, start_response):
        if self.allowed_networks:
            from paste.httpexceptions import HTTPForbidden
            try:
                remote_addr_str = environ["REMOTE_ADDR"]
            except KeyError:
                raise HTTPForbidden("REMOTE_ADDR not found, "
                        "but allowed_networks was specified")

            from ipaddr import IPAddress
            remote_addr = IPAddress(remote_addr_str)

            allowed = False

            for an in self.allowed_networks:
                if remote_addr in an:
                    allowed = True
                    break

            if not allowed:
                raise HTTPForbidden("Requests from your address aren't allowed")

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
    def __init__(self, urlprefix="/", allowed_networks=[]):
        import re
        re_prefix = "^"+re.escape(urlprefix)

        ApplicationBase.__init__(self,
                [(re_prefix+pattern, handler) for pattern, handler in [
                    (r'$', self.index),
                    (r'timestamp/get_range$', self.http_get_tsrange),
                    (r'item/get_by_id$', self.http_get_item_by_id),
                    (r'item/get_version_by_id$', self.http_get_item_version_by_id),
                    (r'items/get$', self.http_get_items),
                    (r'items/print$', self.http_print_items),
                    (r'items/export$', self.http_export_items),
                    (r'item/history/get$', self.http_get_item_history),
                    (r'item/store$', self.http_store_item),
                    (r'item/reorder$', self.http_reorder_item),
                    (r'tags/get_filter$', self.http_get_tags),
                    (r'tags/get_for_query$', self.http_get_tags_for_query),
                    (r'tags/rename$', self.http_rename_tag),
                    (r'app/get_all_js$', self.http_get_all_js),
                    (r'app/quit$', self.http_quit),
                    (r'static/([-_/a-zA-Z0-9.]+)$', self.serve_static),
                    ]],
                allowed_networks=allowed_networks)

        WSGIRequest.defaults["charset"] = "utf-8"
        self.quit_func = None

    def set_quit_func(self, quit_func):
        self.quit_func = quit_func

    # tools -------------------------------------------------------------------
    def item_to_json(self, item):
        result = item.as_json()
        result['contents_html'] = item.contents_html()
        return result

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
                .from_statement(query_itemversions(
                    session, model, parsed_query, max_timestamp)))

    def get_json_items(self, session, model, parsed_query, max_timestamp):
        itemversions_query = query_itemversions(
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
                            "version_id": row[itemversions_query.c.id],
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
        from sqlalchemy import asc, desc
        return request.respond(
                dumps({
                    "min": request.dbsession.query(ItemVersion).
                           order_by(asc(ItemVersion.timestamp))[0].timestamp,
                    "max": max(now,
                           request.dbsession.query(ItemVersion).
                           order_by(desc(ItemVersion.timestamp))[0].timestamp),
                    "now": now,
                    }),
                mimetype="text/plain")

    def get_tags_with_usecounts(self, session, model, parsed_query=None,
            max_timestamp=None, startswith=None, limit=None):
        from sqlalchemy.sql import select, and_, or_, not_, func

        if parsed_query is not None:
            itemversions_q = query_itemversions(session, model,
                    parsed_query, max_timestamp)
        else:
            itemversions_q = select([model.itemversions],
                    from_obj=[get_current_itemversions_join(
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

        if startswith is None or not startswith.startswith("."):
            twuc_q = twuc_q.where(~model.tags.c.name.startswith("."))

        if startswith:
            twuc_q = twuc_q.where(model.tags.c.name.startswith(startswith))

        twuc_q = (twuc_q
                .group_by(model.tags.c.id)
                .having(func.count(itemversions_q.c.id)>0)
                .order_by(model.tags.c.name)
                )

        if limit is not None:
            twuc_q = twuc_q.limit(limit)

        return session.execute(twuc_q)

    def http_get_tags(self, request):
        query = request.GET.get("q", "")
        limit = request.GET.get("limit", None)

        q = self.get_tags_with_usecounts(
                request.dbsession, request.datamodel,
                startswith=query, limit=limit)

        return request.respond(
                "\n".join(row.name for row in q)+"\n",
                mimetype="text/plain")

    def http_get_tags_for_query(self, request):
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

        import re

        old_re = re.compile(r"(?:\b|^)%s(?:\b|$)" % re.escape(old_name))

        for v_ord in request.dbsession.query(ViewOrdering).filter(
                ViewOrdering.tagset.contains(old_name)):
            v_ord.tagset = old_re.sub(new_name, v_ord.tagset)

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

    def http_get_item_version_by_id(self, request):
        query = (
                request.dbsession.query(ItemVersion)
                .filter_by(id=int(request.GET["version_id"]))
                .limit(1))

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
            }),
                mimetype="text/plain")

    def http_print_items(self, request):
        versions = self.get_itemversions_for_request(request)

        from html import printpage
        return request.respond(
                printpage({
                    "title": "Synoptic Printout",
                    "body": "<hr/>".join(
                        '<div class="itemcontents">%s</div>' % v.contents_html()
                        for v in versions),
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

    def http_get_item_history(self, request):
        item_id = int(request.GET["item_id"])

        json = [
                {
                    "version_id": iv.id, 
                    "timestamp":iv.timestamp,
                    "is_current":False,
                    "contents":iv.contents,
                    }
                for iv in request.dbsession.query(ItemVersion)
                .filter_by(item_id=item_id)
                .order_by(ItemVersion.timestamp.desc())]
        json[0]["is_current"] = True

        from simplejson import dumps
        return request.respond(dumps(json),
                mimetype="text/plain")

    def http_store_item(self, request):
        from simplejson import loads, dumps
        data = loads(request.POST["json"])

        # if view ordering is present for current query,
        # make sure this entry shows up last
        if data["contents"] is not None:
            # if we're not deleting
            from synoptic.datamodel import ViewOrderingHandler
            from synoptic.query import parse_query
            voh = ViewOrderingHandler(
                    request.dbsession, request.datamodel,
                    parse_query(data["current_query"]))
            if voh.has_ordering():
                voh.load()
                if data["id"] in voh:
                    # we already have a spot in the ordering, don't bother
                    voh = None
            else:
                voh = None
        else:
            voh = None

        itemversion = store_itemversion(request.dbsession,
                data["contents"], data["tags"], data["id"])

        request.dbsession.commit() # fills in the item_id

        if voh is not None:
            voh.insert(len(voh), itemversion.item_id)
            voh.save()

        # send response
        from simplejson import dumps
        return request.respond(
                dumps(self.item_to_json(itemversion)),
                mimetype="text/plain")

    def http_reorder_item(self, request):
        from simplejson import loads
        data = loads(request.POST["json"])

        from synoptic.query import parse_query
        from synoptic.datamodel import ViewOrderingHandler

        if data["new_order"]:
            voh = ViewOrderingHandler(
                    request.dbsession, request.datamodel,
                    parse_query(data["current_search"]))
            voh.load()
            voh.set_order([int(x) for x in data["new_order"].split(",")])
            voh.save()

        return request.respond("", mimetype="text/plain")

    def http_get_all_js(self, request):
        all_js_filenames = [
          "jquery.js",
          "jquery.timers.js",
          "jquery.bgiframe.js",
          "jquery.dimensions.js",
          "jquery.contextmenu.r2.js",
          "jquery.autocomplete.js",
          "jquery-ui/ui.core.js",
          "jquery-ui/ui.slider.js",
          "jquery-ui/ui.tabs.js",
          "jquery-ui/ui.sortable.js",
          "jquery-ui/ui.datepicker.js",
          "inheritance.js",
          "json2.js",
          "rsh.js",
          "main.js",
          ]
        sep = "/* %s */\n" % (75*"-")
        return request.respond("".join(
            "%s/* %s */\n%s%s" % (sep, fn, sep, get_static_file(fn)[0])
            for fn in all_js_filenames),
            mimetype="text/javascript")

    def http_quit(self, request):
        if self.quit_func is not None:
            self.quit_func()
            return request.respond(
                    "Thanks for using synoptic.",
                    mimetype="text/plain")
        else:
            raise HTTPForbidden()

    def serve_static(self, request, filename):
        try:
            data, mimetype = get_static_file(filename)
        except IOError:
            print "NOT FOUND:", filename
            from paste.httpexceptions import HTTPNotFound
            raise HTTPNotFound()

        return request.respond(data, mimetype=mimetype)
