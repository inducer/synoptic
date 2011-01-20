from sqlalchemy import *
from migrate import *

meta = MetaData()

itemversions = Table('itemversions', meta,
        Column('id', Integer, primary_key=True),
        Column('item_id', Integer, ForeignKey('items.id')),
        Column('timestamp', Float, index=True),
        Column('contents', UnicodeText())
        )

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    new_cols = [
        Column('start_date', Float()),
        Column('end_date', Float()),
        Column('bump_interval', 
            Enum("hour", "day", "week", "2week", "month", "year")),
        Column('hide_until', Float()),
        Column('highlight_at', Float()),
        ]

    for col in new_cols:
        col.create(itemversions)

def downgrade(migrate_engine):
    raise NotImplementedError
