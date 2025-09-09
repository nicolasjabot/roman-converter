import os
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, Connection, URL

_engine: Engine | None = None

def connect_unix_socket() -> Engine:
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASSWORD"]
    db_name = os.environ["DB_NAME"]
    socket_dir = os.environ["INSTANCE_UNIX_SOCKET"]  # "/cloudsql/PROJECT:REGION:INSTANCE"

    # psycopg v3 driver
    url = URL.create(
        drivername="postgresql+psycopg",
        username=db_user,
        password=db_pass,
        database=db_name,
        query={"host": socket_dir},
    )

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=2,
        connect_args={"connect_timeout": 5},
    )

def _ensure_engine() -> Engine:
    global _engine
    if _engine is None:
        # optional assert so failures are obvious
        if not os.path.isdir(os.environ["INSTANCE_UNIX_SOCKET"]):
            raise RuntimeError(f"Cloud SQL socket dir missing: {os.environ.get('INSTANCE_UNIX_SOCKET')}")
        _engine = connect_unix_socket()
    return _engine

@contextmanager
def get_connection() -> Iterator[Connection]:
    with _ensure_engine().connect() as conn:
        yield conn