from sqlalchemy import *
from migrate import *

meta = MetaData()

BUMP_INTERVALS = [
    ("hour", "hour"),
    ("day", "day"), 
    ("week", "week"),
    ("2week", "2 weeks"),
    ("month", "month"),
    ("year", "year")
    ]

itemversions = Table('itemversions', meta,
        Column('id', Integer, primary_key=True),
        Column('item_id', Integer, ForeignKey('items.id')),
        Column('timestamp', Float, index=True),
        Column('contents', UnicodeText()),

        Column('start_date', Float()),
        Column('end_date', Float()),
        Column('bump_interval', 
            Enum(*[key for key, val in BUMP_INTERVALS])),
        Column('hide_until', Float()),
        Column('highlight_at', Float()),
        )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    Column('all_day', Boolean()).create(itemversions)

def downgrade(migrate_engine):
    raise NotImplementedError
