import os
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import create_engine, engine
from sqlalchemy.engine import Engine, Connection, URL

_engine: Engine | None = None


def connect_unix_socket() -> engine.base.Engine:
    """Initializes a Unix socket connection pool for a Cloud SQL instance of Postgres."""
    print("connect_unix_socket(): starting")

    try:
        db_user = os.environ["DB_USER"]
        db_pass = os.environ["DB_PASSWORD"]
        db_name = os.environ["DB_NAME"]
        unix_socket_path = os.environ["INSTANCE_UNIX_SOCKET"]

        print(f"connect_unix_socket(): got envs DB_USER={db_user}, DB_NAME={db_name}, INSTANCE_UNIX_SOCKET={unix_socket_path}")
    except KeyError as e:
        print(f"connect_unix_socket(): missing env var {e}")
        raise

    url = URL.create(
        drivername="postgresql+pg8000",
        username=db_user,
        password=db_pass,
        database=db_name,
        # pg8000 wants the *socket file* path via unix_sock
        query={"unix_sock": f"{unix_socket_path}/.s.PGSQL.5432"},
    )

    print(f"connect_unix_socket(): created SQLAlchemy URL {url}")

    try:
        engine_obj = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )
        print("connect_unix_socket(): engine created successfully")
        return engine_obj
    except Exception as e:
        print(f"connect_unix_socket(): failed creating engine -> {e}")
        raise


def _ensure_engine() -> Engine:
    global _engine
    if _engine is None:
        print("_ensure_engine(): no cached engine, creating")
        socket_dir = os.environ.get("INSTANCE_UNIX_SOCKET")
        print(f"_ensure_engine(): INSTANCE_UNIX_SOCKET={socket_dir}")
        if not socket_dir or not os.path.isdir(socket_dir):
            print(f"_ensure_engine(): socket dir missing or not mounted: {socket_dir}")
            raise RuntimeError(f"Cloud SQL socket dir missing or not mounted: {socket_dir}")
        _engine = connect_unix_socket()
    else:
        print("_ensure_engine(): reusing cached engine")
    return _engine


@contextmanager
def get_connection() -> Iterator[Connection]:
    print("get_connection(): opening DB connection...")
    try:
        with _ensure_engine().connect() as conn:
            print("get_connection(): connection opened")
            yield conn
    except Exception as e:
        print(f"get_connection(): failed to open connection -> {e}")
        raise
    finally:
        print("get_connection(): context closed")
