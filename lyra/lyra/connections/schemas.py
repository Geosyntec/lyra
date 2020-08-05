from sqlalchemy import Column, DateTime, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from lyra.connections.database import database_engine


Base = declarative_base()


class TableChangeLog(Base):

    __tablename__ = "TableChangeLog"

    id = Column(Integer, primary_key=True)
    table_name = Column(String(32), index=True)
    status = Column(String(32), index=True)
    date_initiated = Column(DateTime, index=True)
    date_completed = Column(DateTime, nullable=True)
    message = Column(String, nullable=True)


class DTMetrics(Base):

    __tablename__ = "DTMetrics"

    id = Column(Integer, primary_key=True)
    catchidn = Column(Integer, index=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    variable = Column(Integer, index=True)
    value = Column(Float)

    # var_name_id = Column(Integer, ForeignKey('DTMetricsCategories.id'))


class DTMetricsCategories(Base):

    __tablename__ = "DTMetricsCategories"

    id = Column(Integer, primary_key=True)
    variable = Column(String)
    # metrics = relationship("DTMetrics", backref='DTMetricsCategories')


def init_all(engine):
    with engine.begin() as conn:
        Base.metadata.create_all(conn)


def drop_all(table_name, engine):
    with engine.begin() as conn:
        conn.execute(f"DROP TABLE {table_name}")
