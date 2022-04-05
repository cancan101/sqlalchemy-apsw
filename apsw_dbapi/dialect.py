# pylint: disable=protected-access, abstract-method
"""A SQLALchemy dialect."""
from typing import Any, Dict, List, Optional, Tuple, cast

import sqlalchemy.types
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.engine.url import URL
from sqlalchemy.pool.base import _ConnectionFairy
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.visitors import VisitableType
from typing_extensions import TypedDict

from . import db
from .exceptions import ProgrammingError


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

    name = "sqlite-apsw"
    driver = "apsw"

    # This is supported in ``SQLiteDialect``, and equally supported here. See
    # https://docs.sqlalchemy.org/en/14/core/connections.html#caching-for-third-party-dialects
    # for more context.
    supports_statement_cache = True

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

    # TODO(cancan101): figure out if we need these:
    # def do_ping(self, dbapi_connection: _ConnectionFairy) -> bool:
    #     return True

    # def has_table(
    #     self,
    #     connection: _ConnectionFairy,
    #     table_name: str,
    #     schema: Optional[str] = None,
    # ) -> bool:
    #     """
    #     Return true if a given table exists.
    #     """
    #     try:
    #         pass
    #     except ProgrammingError:
    #         return False
    #     return True

    # needed for SQLAlchemy
    # def _get_table_sql(  # pylint: disable=unused-argument
    #     self,
    #     connection: _ConnectionFairy,
    #     table_name: str,
    #     schema: Optional[str] = None,
    #     **kwargs: Any,
    # ) -> str:
    #     return table.get_create_table(table_name)

    # def get_columns(  # pylint: disable=unused-argument
    #     self,
    #     connection: _ConnectionFairy,
    #     table_name: str,
    #     schema: Optional[str] = None,
    #     **kwargs: Any,
    # ) -> List[SQLAlchemyColumn]:
    #     return [
    #         {
    #             "name": column_name,
    #             "type": getattr(sqlalchemy.types, field.type),
    #             "nullable": True,
    #             "default": None,
    #             "autoincrement": "auto",
    #             "primary_key": 0,
    #         }
    #         for column_name, field in columns.items()
    #     ]
