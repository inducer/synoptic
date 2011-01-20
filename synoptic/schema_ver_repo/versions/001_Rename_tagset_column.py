from sqlalchemy import *
from migrate import *

meta = MetaData()

vieworderings = Table('vieworderings', meta,
        Column('id', Integer, primary_key=True),
        Column('tagset', Text()),
        Column('timestamp', Float, index=True),
        )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    vieworderings.c.tagset.alter(name="norm_query")

def downgrade(migrate_engine):
    raise NotImplementedError
