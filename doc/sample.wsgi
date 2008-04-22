#! /usr/bin/env python




DATABASE_FILE = '/home/andreas/synoptic.db'
DATABASE_URL = 'sqlite:///%s' % DATABASE_FILE
URL_PREFIX = '/'
ADD_STARTUP_CONTENT = False




def application(environ, start_response):
    import os
    import sys

    from synoptic import Application
    real_app = app = Application(URL_PREFIX)

    from synoptic import DBSessionInjector
    app = dbinj = DBSessionInjector(app, DATABASE_URL)

    from synoptic import ErrorMiddleware
    app = ErrorMiddleware(app)

    if ADD_STARTUP_CONTENT:
        from synoptic import import_file, get_static_file
        import_file(dbinj.sessionmaker(), 
                get_static_file("initial-content.txt")[0])

    return app(environ, start_response)




if __name__ == "__main__":
    from paste.httpserver import WSGIServer, WSGIHandler
    server = WSGIServer(application, ("127.0.0.1", 7331), WSGIHandler)
    server.serve_forever()
