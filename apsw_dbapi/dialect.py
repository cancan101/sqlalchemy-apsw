# pylint: disable=protected-access, abstract-method
"""A SQLALchemy dialect."""
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.engine.url import URL
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.visitors import VisitableType
from typing_extensions import TypedDict

from . import db


class SQLAlchemyColumn(TypedDict):
    """
    A custom type for a SQLAlchemy column.
    """

    name: str
    type: VisitableType
    nullable: bool
    default: Optional[str]
    autoincrement: str
    primary_key: int


class APSWDialect(SQLiteDialect):

    """
    A SQLAlchemy dialect for for sqlite that uses APSW.

    The dialect is based on the ``SQLiteDialect``, since we're using APSW.
    """

    driver = "apsw"

    # This is supported in ``SQLiteDialect``, and equally supported here. See
    # https://docs.sqlalchemy.org/en/14/core/connections.html#caching-for-third-party-dialects
    # for more context.
    supports_statement_cache = True

    # The base class:
    # https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/dialects/sqlite/base.py

    # TODO(cancan101): figure out if this is true
    # ``SQLiteDialect.colspecs`` has custom representations for objects that SQLite stores
    # as string (eg, timestamps). Since the our DB API driver returns them as
    # proper objects the custom representations are not needed.
    colspecs: Dict[TypeEngine, TypeEngine] = {}

    @classmethod
    def dbapi(cls):  # pylint: disable=method-hidden
        """
        Return the DB API module.
        """
        return db

    def create_connect_args(
        self,
        url: URL,
    ) -> Tuple[Tuple[()], Dict[str, Any]]:
        path = str(url.database) if url.database else ":memory:"
        return (), {
            "path": path,
            "isolation_level": self.isolation_level,
        }

    def _get_server_version_info(self, connection):
        return self.dbapi.sqlite_version_info
