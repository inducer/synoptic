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
            ".gif": "image/gif",
            ".css": "text/css",
            ".txt": "text/plain",
            ".js": "text/javascript",
            }

    if ext == ".txt":
        data = data.decode("utf-8")

    return (data, mimetypes.get(ext, "application/octet-stream"))




# {{{ import backup/initial content

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

        store_itemversion(dbsession, 
                contents="\n".join(body), tags=tags, timestamp=timestamp)

    dbsession.commit()

# }}}




def kill_hms_in_time_struct(t_struct):
    t_struct = list(t_struct)
    t_struct[3:6] = (0,0,0)
    t_struct[8] = -1
    return t_struct



def get_google_calendar_tag(entry_dict):
    from hashlib import md5
    md5_obj = md5()
    md5_obj.update(str(entry_dict.get("url")))
    return "gcal-"+md5_obj.hexdigest()[:10]




# {{{ HTTP middleware

class DBSessionInjector(object):
    def __init__(self, sub_app, dburl, exists, echo=False):
        # {{{ schema upgrade

        import migrate.versioning.api as mig_api
        import synoptic.schema_ver_repo as svr
        from os.path import dirname
        versioning_repo = dirname(svr.__file__)

        latest_ver = mig_api.version(versioning_repo)

        if exists:
            from migrate.exceptions import DatabaseNotControlledError
            try:
                db_ver = mig_api.db_version(dburl, versioning_repo)
            except DatabaseNotControlledError:
                print "adding version control to db"
                mig_api.version_control(dburl, versioning_repo)
                db_ver = mig_api.db_version(dburl, versioning_repo)


            print "found database version %d, code uses version %d" % (db_ver, latest_ver)

            if db_ver < latest_ver:
                print "upgrading..."
                mig_api.upgrade(dburl, versioning_repo)
        else:
            # we're only just creating the db, thus using the latest available version
            mig_api.version_control(dburl, versioning_repo, version=latest_ver)

        # }}}

        from sqlalchemy.pool import NullPool
        from sqlalchemy import create_engine
        self.engine = create_engine(dburl, poolclass=NullPool)

        from synoptic.datamodel import DataModel
        self.datamodel = DataModel()
        if not exists:
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

# }}}

# {{{ URL dispatch

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

# }}}




class Application(ApplicationBase):
    def __init__(self, urlprefix="/", allowed_networks=[]):
        import re
        re_prefix = "^"+re.escape(urlprefix)

        ApplicationBase.__init__(self,
                [(re_prefix+pattern, handler) for pattern, handler in [
                    (r'$', self.http_index),
                    (r'mobile$', self.http_mobile_index),
                    (r'timestamp/get_range$', self.http_get_tsrange),
                    (r'item/get_by_id$', self.http_get_item_by_id),
                    (r'item/get_version_by_id$', self.http_get_item_version_by_id),
                    (r'items/get$', self.http_get_items),
                    (r'items/get_result_hash$', self.http_get_result_hash),
                    (r'items/print$', self.http_print_items),
                    (r'items/export$', self.http_export_items),
                    (r'item/history/get$', self.http_get_item_history),
                    (r'item/store$', self.http_store_item),
                    (r'item/datebump$', self.http_item_datebump),
                    (r'item/reorder$', self.http_reorder_item),
                    (r'tags/get_filter$', self.http_get_tags),
                    (r'tags/get_for_query$', self.http_get_tags_for_query),
                    (r'tags/rename$', self.http_rename_tag),
                    (r'calendar$', self.http_calendar),
                    (r'mobile-calendar$', self.http_mobile_calendar),
                    (r'calendar/event_sources$', self.http_calendar_event_sources),
                    (r'calendar/data$', self.http_calendar_data),
                    (r'app/get_all_js$', self.http_get_all_js),
                    (r'tag-color-css$', self.http_get_tag_color_css),
                    (r'app/quit$', self.http_quit),
                    (r'static/([-_/a-zA-Z0-9.]+)$', self.serve_static),
                    ]],
                allowed_networks=allowed_networks)

        WSGIRequest.defaults["charset"] = "utf-8"
        self.quit_func = None

    def set_quit_func(self, quit_func):
        self.quit_func = quit_func

    # {{{ tools

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
                            "all_day": row[itemversions_query.c.all_day],
                            "start_date": row[itemversions_query.c.start_date],
                            "end_date": row[itemversions_query.c.end_date],
                            "bump_interval": row[itemversions_query.c.bump_interval],
                            "hide_until": row[itemversions_query.c.hide_until],
                            "highlight_at": row[itemversions_query.c.highlight_at],
                            })
            if row[model.tags.c.name] is not None:
                result[-1]["tags"].append(row[model.tags.c.name])

        return result

    def get_config_info_by_tag(self, datamodel, dbsession, tag):
        """Return a list of dictionaries containing configuration information
        from notes with *tag* which are formatted like this::

            * url: https://bladiblah
            * color: #4433cc
        """

        tags = dbsession.query(Tag).filter_by(name=tag)

        entries = []

        if tags.count():
            google_calendar_tag = tags.one()

            from sqlalchemy.sql import select
            qry = select([datamodel.itemversions],
                    from_obj=get_current_itemversions_join(datamodel)) \
                    .where(ItemVersion.tags.any(id=google_calendar_tag.id))

            import re
            config_entry_re = re.compile(r"^\s*(?:\*\s+)?([a-zA-Z0-9]+)\s*:\s*(.*)\s*$",
                    re.MULTILINE)
            for item_ver in dbsession.query(ItemVersion).from_statement(qry):
                entry = {}
                entries.append(entry)
                for match in config_entry_re.finditer(item_ver.contents):
                    entry[match.group(1)] = match.group(2)

        return entries

    # }}}

    # {{{ page handlers

    def http_index(self, request):
        from synoptic.html import main_page, Context
        ctx = Context()
        return request.respond(main_page(ctx))

    def http_mobile_index(self, request):
        from synoptic.html import mobile_main_page, Context
        ctx = Context()
        return request.respond(mobile_main_page(ctx))

    def http_get_tsrange(self, request):
        from time import time

        now = time()

        from simplejson import dumps
        from sqlalchemy import asc, desc
        base_query = request.dbsession.query(ItemVersion)
        if list(base_query.limit(1)):
            return request.respond(
                    dumps({
                        "min": base_query.order_by(asc(ItemVersion.timestamp))[0].timestamp,
                        "max": max(now,
                               base_query.order_by(desc(ItemVersion.timestamp))[0].timestamp),
                        "now": now,
                        }),
                    mimetype="text/plain")
        else:
            return request.respond(
                    dumps({ "min": now, "max": now+1, "now": now, }),
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

        from simplejson import dumps
        return request.respond(
                dumps([row.name for row in q]),
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

        from synoptic.datamodel import is_valid_tag
        if not is_valid_tag(new_name):
            raise RuntimeError("invalid tag")

        tag = request.dbsession.query(Tag).filter_by(name=old_name).one()
        new_tag_query = request.dbsession.query(Tag).filter_by(name=new_name)

        if new_tag_query.count():
            raise ValueError, "tag already exsits"

        tag.name = new_name

        import re

        old_re = re.compile(r"(?:\b|^)%s(?:\b|$)" % re.escape(old_name))

        for v_ord in request.dbsession.query(ViewOrdering).filter(
                ViewOrdering.norm_query.contains(old_name)):
            v_ord.norm_query = old_re.sub(new_name, v_ord.norm_query)

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

        from simplejson import dumps

        # kind of silly to do two JSON encodes, but what the heck
        result_hash = hash(dumps(json_items))

        # and ship them out by JSON
        return request.respond(dumps({
            "items": json_items,
            "result_hash": result_hash,
            "tags": tags,
            "query_tags": query_tags,
            }),
                mimetype="text/plain")

    def http_get_result_hash(self, request):
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

        from simplejson import dumps
        result_hash = hash(dumps(json_items))

        # and ship them out by JSON
        return request.respond(dumps(result_hash),
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

    @staticmethod
    def parse_datetime(data, name, rel_to_name=None, use_utc=False):
        import parsedatetime.parsedatetime as pdt
        cal = pdt.Calendar()
        import datetime
        import time

        if data[name]:
            if rel_to_name is not None and data[rel_to_name] is not None:
                rel_to = datetime.datetime.fromtimestamp(
                        data[rel_to_name]).timetuple()
            else:
                rel_to = None

            t_struct, parsed_as = cal.parse(data[name], rel_to)
            if parsed_as:
                t_struct = list(t_struct)
                if parsed_as == 1:
                    # only parsed as date, eliminate time part
                    t_struct[3:6] = (0,0,0)

                t_struct[8] = -1 # isdst -- we don't know if that is DST

                if use_utc:
                    from calendar import timegm
                    data[name] = timegm(t_struct)
                else:
                    data[name] = time.mktime(t_struct)
            else:
                data[name] = None
        else:
            data[name] = None

    def http_store_item(self, request):
        from simplejson import loads, dumps
        data = loads(request.POST["json"])

        current_query = data.pop("current_query", None)
        deleting = data["contents"] is None

        # if view ordering is present for current query,
        # make sure this entry shows up last
        if not deleting:
            # if we're not deleting
            from synoptic.datamodel import ViewOrderingHandler
            from synoptic.query import parse_query
            voh = ViewOrderingHandler(
                    request.dbsession, request.datamodel,
                    parse_query(current_query))
            if voh.has_ordering():
                voh.load()
                if data["id"] in voh:
                    # we already have a spot in the ordering, don't bother
                    voh = None
            else:
                voh = None
        else:
            voh = None

        if not deleting:
            self.parse_datetime(data, "start_date", 
                    use_utc=data["all_day"])
            self.parse_datetime(data, "end_date", "start_date", 
                    use_utc=data["all_day"])
            self.parse_datetime(data, "hide_until", "start_date")
            self.parse_datetime(data, "highlight_at", "start_date")

        if not deleting:
            from synoptic.datamodel import is_valid_tag
            for tag in data["tags"]:
                if not is_valid_tag(tag):
                    raise RuntimeError("invalid tag")

        itemversion = store_itemversion(request.dbsession,
                **data)

        request.dbsession.commit() # fills in the item_id

        if voh is not None:
            voh.insert(len(voh), itemversion.item_id)
            voh.save()

        # send response
        from simplejson import dumps
        return request.respond(
                dumps(self.item_to_json(itemversion)),
                mimetype="text/plain")

    def http_item_datebump(self, request):
        from simplejson import loads, dumps
        data = loads(request.POST["json"])

        bump_interval = data["bump_interval"]
        bump_direction = data["bump_direction"]

        self.parse_datetime(data, "start_date")
        self.parse_datetime(data, "end_date", "start_date")
        self.parse_datetime(data, "hide_until", "start_date")
        self.parse_datetime(data, "highlight_at", "start_date")

        tdelta = None
        increment_func = None

        import datetime
        import time

        if bump_interval == "hour":
            tdelta = datetime.timedelta(hours=bump_direction)
        elif bump_interval == "day":
            tdelta = datetime.timedelta(days=bump_direction)
        elif bump_interval == "week":
            tdelta = datetime.timedelta(days=7*bump_direction)
        elif bump_interval == "2week":
            tdelta = datetime.timedelta(days=14*bump_direction)
        elif bump_interval == "month":
            def increment_func(timestamp):
                dt = datetime.datetime.fromtimestamp(timestamp)
                year = dt.year
                month = dt.month + bump_direction
                day = dt.day

                if month > 12:
                    month = 1
                    year += 1
                if month < 1:
                    month = 12
                    year -= 1

                attempt_count = 10
                while True:
                    try:
                        dt = dt.replace(year=year, month=month, day=day)
                    except ValueError:
                        day -= 1
                        attempt_count -= 1
                        if attempt_count == 0:
                            raise
                    else:
                        break

                return time.mktime(dt.timetuple())
        elif bump_interval == "year":
            def increment_func(timestamp):
                dt = datetime.datetime.fromtimestamp(timestamp)
                year = dt.year + bump_direction
                month = dt.month
                day = dt.day

                attempt_count = 10
                while True:
                    try:
                        dt = dt.replace(year=year, month=month, day=day)
                    except ValueError:
                        day -= 1
                        attempt_count -= 1
                        if attempt_count == 0:
                            raise
                    else:
                        break

                return time.mktime(dt.timetuple())
        else:
            raise RuntimeError("unknown bump_interval")

        if increment_func is None:
            def increment_func(timestamp):
                dt = datetime.datetime.fromtimestamp(timestamp)
                dt = dt + tdelta
                return time.mktime(dt.timetuple())

        for key in ["start_date", "end_date", "hide_until", "highlight_at"]:
            if data[key] is not None:
                data[key] = increment_func(data[key])

        from simplejson import dumps
        return request.respond(
                dumps(data),
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

    # {{{ calendar

    def http_calendar(self, request):
        from html import calendar_page
        return request.respond(calendar_page({}))

    def http_mobile_calendar(self, request):
        from html import mobile_calendar_page
        return request.respond(mobile_calendar_page({}))

    def http_calendar_event_sources(self, request):
        event_sources = ["/calendar/data"]

        for entry_dict in self.get_config_info_by_tag(
                request.datamodel, request.dbsession, u"googlecalendar"):
            if "url" not in entry_dict:
                continue
            event_sources.append(dict(
                url=entry_dict["url"],
                className=get_google_calendar_tag(entry_dict),
                requireOnline=True))

        from simplejson import dumps
        return request.respond(
                dumps(event_sources),
                mimetype="text/plain")

    def http_calendar_data(self, request):
        start = float(request.GET.get("start", 0))
        end = float(request.GET.get("end", 0))
        max_timestamp = None # FIXME

        from_obj = get_current_itemversions_join(
                request.datamodel, max_timestamp)

        from sqlalchemy.sql import select, or_, and_
        where = or_(
            # start_date in range
            and_(
                start <= ItemVersion.start_date,
                ItemVersion.start_date <= end),
            # end_date in range
            and_(
                start <= ItemVersion.end_date,
                ItemVersion.end_date <= end),
            # span entire range
            and_(
                ItemVersion.start_date <= start,
                ItemVersion.end_date <= end)
            )

        qry = select([request.datamodel.itemversions], from_obj=from_obj) \
                .where(where)

        data = []
        for item_ver in (request.dbsession.query(ItemVersion).from_statement(qry)):
            if item_ver.all_day:
                from time import gmtime, mktime
                if item_ver.start_date is not None:
                    start = mktime(
                            kill_hms_in_time_struct(
                                gmtime(item_ver.start_date)))
                else:
                    start = None
                if item_ver.end_date is not None:
                    end = mktime(
                            kill_hms_in_time_struct(
                                gmtime(item_ver.end_date)))
                else:
                    end = None
            else:
                start = item_ver.start_date
                end = item_ver.end_date

            contents = item_ver.contents

            if len(contents) > 40:
                contents = contents[:40] + "..."

            from urllib import quote
            data.append(dict(
                id=item_ver.id,
                title=contents,
                start=start,
                end=end,
                allDay=item_ver.all_day,
                className=["tag-%s" % tag.name for tag in item_ver.tags],
                url="/#"+quote('{"query": "id(%d) nohide"}' % item_ver.item_id),
                ))

        from time import time
        now = time()
        data.append(dict(
            id="-1",
            title="NOW",
            start=now,
            end=now + 7.5 * 60,
            allDay=False,
            className=["calendar-now" ],
            ))

        from simplejson import dumps
        return request.respond(
                dumps(data),
                mimetype="text/plain")

    # }}}

    def http_get_all_js(self, request):
        all_js_filenames = [
          "jquery.js",
          "jquery-migrate.js",
          "jquery.timers.js",
          "jquery.bgiframe.js",
          "jquery.dimensions.js",
          "jquery.contextmenu.r2.js",
          "jquery-ui.js",

          # override because of z-index bug
          # http://bugs.jqueryui.com/ticket/5479
          "jquery.ui.datepicker.js", 

          "inheritance.js",
          "json2.js",
          "rsh.js",
          "sprintf.js",
          ]
        sep = "/* %s */\n" % (75*"-")
        all_js = "".join(
            "%s/* %s */\n%s%s" % (sep, fn, sep, get_static_file(fn)[0])
            for fn in all_js_filenames)

        from synoptic.datamodel import BUMP_INTERVALS
        from simplejson import dumps
        all_js = "var BUMP_INTERVALS = %s;\n%s" % (dumps(BUMP_INTERVALS), all_js)

        return request.respond(all_js,
            mimetype="text/javascript")

    def http_get_tag_color_css(self, request):
        is_calendar = request.GET.get("calendar", "") == "true"
        if is_calendar:
            pattern = """.tag-%(tag)s, .fc-agenda .tag-%(tag)s .fc-event-time, .tag-%(tag)s .fc-event-inner
                { background-color: %(color)s; border-color: %(color)s; }"""
        else:
            pattern = ".tag-%(tag)s { background-color: %(color)s; color:white; }" 

        color_decls = []
        for entry_dict in self.get_config_info_by_tag(
                request.datamodel, request.dbsession, u"colorconfig"):
            for tag, color in entry_dict.iteritems():
                color_decls.append(pattern % dict(tag=tag, color=color))

        if is_calendar:
            for entry_dict in self.get_config_info_by_tag(
                    request.datamodel, request.dbsession, u"googlecalendar"):
                if "color" in entry_dict:
                    color_decls.append(
                        """.%(tag)s, .fc-agenda .%(tag)s .fc-event-time, .%(tag)s .fc-event-inner
                            { background-color: %(color)s; border-color: %(color)s; }"""
                        % dict(
                            tag=get_google_calendar_tag(entry_dict),
                            color=entry_dict["color"]))

        css = "\n".join(color_decls)

        return request.respond(css, mimetype="text/css")

    def http_quit(self, request):
        if self.quit_func is not None:
            self.quit_func()
            return request.respond(
                    "Thanks for using synoptic.",
                    mimetype="text/plain")
        else:
            from paste.httpexceptions import HTTPForbidden
            raise HTTPForbidden()

    def serve_static(self, request, filename):
        try:
            data, mimetype = get_static_file(filename)
        except IOError:
            print "NOT FOUND:", filename
            from paste.httpexceptions import HTTPNotFound
            raise HTTPNotFound()

        return request.respond(data, mimetype=mimetype)

    # }}}

# vim: foldmethod=marker
