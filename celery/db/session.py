import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from celery import conf

ResultModelBase = declarative_base()

_SETUP = {"results": False}
_ENGINES = {}


def get_engine(dburi, **kwargs):
    if dburi not in _ENGINES:
        _ENGINES[dburi] = create_engine(dburi, **kwargs)
    return _ENGINES[dburi]


def create_session(dburi, **kwargs):
    engine = get_engine(dburi, **kwargs)
    return engine, sessionmaker(bind=engine)


def setup_results(engine):
    if not _SETUP["results"]:
        ResultModelBase.metadata.create_all(engine)
        _SETUP["results"] = True


def ResultSession(dburi=conf.RESULT_DBURI, **kwargs):
    engine, session = create_session(dburi, **kwargs)
    if os.environ.get("CELERYINIT"):
        setup_results(engine)
    return session()
