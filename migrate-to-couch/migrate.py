#! /usr/bin/env python2.5

def main():
    from optparse import OptionParser

    import os
    import sys

    description = ("Migration to CouchDB"
            "To start a new database file, simply pick a file name and start synoptic "
            "with it. That file will be created and will contain your set of notes.")

    parser = OptionParser(description=description,
            usage="%prog [options] dbfile tgt_db_url couch_user couch_pwd")
    parser.add_option("--couch-db-name", default="synoptic")
    options, args = parser.parse_args()

    if len(args) != 4:
        parser.print_help()
        sys.exit(1)

    dbname = args[0]

    if not os.access(dbname, os.F_OK):
        raise

    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///%s" % dbname)
    from synoptic.datamodel import DataModel, Item, ViewOrdering
    datamodel = DataModel()
    datamodel.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    sessionmaker = sessionmaker(bind=engine, autoflush=True,
            autocommit=False)

    dbsession = sessionmaker()

    from couchdb.client import Server as CouchServer
    csrv = CouchServer(args[1])
    csrv.resource.http.add_credentials(args[2], args[3])

    cdb = csrv[options.couch_db_name]

    from uuid import uuid4

    for item in dbsession.query(Item):
        for itemversion in item.versions:
            doc = {
                    "_id": uuid4().hex,
                    "type": "item_version",
                    "item_id": item.id,
                    "timestamp": itemversion.timestamp,
                    "contents": itemversion.contents,
                    "tags": [tag.name for tag in itemversion.tags]
                    }

            cdb[doc["_id"]] = doc

    for vieword in dbsession.query(ViewOrdering):
        doc = {
                "_id": uuid4().hex,
                "type": "view_ordering",
                "timestamp": vieword.timestamp,
                "norm_query": vieword.tagset,
                "entries": [item_id for weight, item_id in sorted(
                    (ent.weight, ent.item_id)
                    for ent in vieword.entries)]
                }

        cdb[doc["_id"]] = doc










if __name__ == "__main__":
    main()

