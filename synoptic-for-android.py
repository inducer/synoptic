from __future__ import absolute_import
from __future__ import print_function
import sys
# -----------------------------------------------------------------------------
# requrires Python4Android and the Android scripting layer
#
# change settings here

root = "/sdcard/synoptic-install"
dbname = "/sdcard/synoptic-install/data.db"

host = "127.0.0.1"
port = 7331

# then copy this file into /sdcard/sl4a/scripts
# -----------------------------------------------------------------------------

paths = [
        "synoptic",
        "Paste-1.7.5.1",
        "SQLAlchemy-0.7.2/lib",
        "parsedatetime-0.8.7",
        "sqlalchemy-migrate-0.7.1",
        "ipaddr-2.1.9",
        "pkg_resources-2.6",
        "Tempita-0.5.1",
        "decorator-3.3.2/src",
        ]

from os.path import join
sys.path.extend(join(root, path) for path in paths)

from synoptic import Application
real_app = app = Application(allowed_networks=[])

import os
exists = os.access(dbname, os.F_OK)

from synoptic import DBSessionInjector
app = dbinj = DBSessionInjector(app, "sqlite:///%s" % dbname, exists)

from synoptic import ErrorMiddleware
app = ErrorMiddleware(app)

if not exists:
    from synoptic import import_file, get_static_file
    import_file(dbinj.sessionmaker(),
            get_static_file("initial-content.txt")[0])

from paste.httpserver import WSGIServer, WSGIHandler
server = WSGIServer(app, (host, port), WSGIHandler)

url = "http://%s:%d/" % (host, port)
print("serving at %s..." % url)

quit_flag = [False]

def quit_func():
    quit_flag[0] = True

real_app.set_quit_func(quit_func)

while not quit_flag[0]:
    server.handle_request()

print("quitting...", file=sys.stderr)
