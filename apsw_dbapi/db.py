# pylint: disable=invalid-name, c-extension-no-member, no-self-use, unused-import
"""
A DB API 2.0 wrapper for APSW.

https://rogerbinns.github.io/apsw/dbapi.html
"""
import datetime
import itertools
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)

import apsw
import dateutil.parser

from . import functions
from .exceptions import Warning  # pylint: disable=redefined-builtin
from .exceptions import (
    DatabaseError,
    DataError,
    Error,
    IntegrityError,
    InterfaceError,
    InternalError,
    NotSupportedError,
    OperationalError,
    ProgrammingError,
)
from .types import (
    BINARY,
    DATETIME,
    NUMBER,
    ROWID,
    STRING,
    Binary,
    Date,
    DateFromTicks,
    Time,
    TimeFromTicks,
    Timestamp,
    TimestampFromTicks,
)
from .typing import Description, SQLiteValidType

apilevel = "2.0"
threadsafety = 2
paramstyle = "qmark"
sqlite_version_info = tuple(
    int(number) for number in apsw.sqlitelibversion().split(".")
)

CURSOR_METHOD = TypeVar("CURSOR_METHOD", bound=Callable[..., Any])


def check_closed(method: CURSOR_METHOD) -> CURSOR_METHOD:
    """Decorator that checks if a connection or cursor is closed."""

    @wraps(method)
    def wrapper(self: "Cursor", *args: Any, **kwargs: Any) -> Any:
        if self.closed:
            raise ProgrammingError(f"{self.__class__.__name__} already closed")
        return method(self, *args, **kwargs)

    return cast(CURSOR_METHOD, wrapper)


def check_result(method: CURSOR_METHOD) -> CURSOR_METHOD:
    """Decorator that checks if the cursor has results from ``execute``."""

    @wraps(method)
    def wrapper(self: "Cursor", *args: Any, **kwargs: Any) -> Any:
        if self._results is None:  # pylint: disable=protected-access
            raise ProgrammingError("Called before ``execute``")
        return method(self, *args, **kwargs)

    return cast(CURSOR_METHOD, wrapper)


def get_type_code(type_name: Optional[str]) -> Optional[str]: # DBAPIType
    """
    Return a ``DBAPIType`` that corresponds to a type name.
    """
    if type_name is None:
        return None
    return type_name.split("(", 1)[0]
    # return cast(DBAPIType, type_map.get(type_name, Blob))


type_map = {
    None: lambda x: x,
    "INTEGER": lambda x: x,
    "VARCHAR": lambda x: x,
    "TEXT": lambda x: x,
    "DATE": lambda x: None if x is None else dateutil.parser.isoparse(x).date(),
    "DATETIME": lambda x: None if x is None else dateutil.parser.isoparse(x),
    "BOOLEAN": lambda x: x,
    "FLOAT": lambda x: x,
    "BLOB": lambda x: x,
    "TIME": lambda x: None if x is None else datetime.time.fromisoformat(x),
}


def convert_binding(binding: Any) -> SQLiteValidType:
    """
    Convert a binding to a SQLite type.

    Eg, if the user is filtering a timestamp column we need to convert the
    ``datetime.datetime`` object in the binding to a string.
    """
    if isinstance(binding, bool):
        return int(binding)
    if isinstance(binding, (int, float, str, bytes, type(None))):
        return binding
    if isinstance(binding, (datetime.datetime, datetime.date, datetime.time)):
        return binding.isoformat()
    return str(binding)


class Cursor:  # pylint: disable=too-many-instance-attributes

    """
    Connection cursor.
    """

    description: Optional[Description]

    def __init__(
        self,
        cursor: "apsw.Cursor",
        isolation_level: Optional[str] = None,
    ):
        self._cursor = cursor

        self.in_transaction = False
        self.isolation_level = isolation_level

        # This read/write attribute specifies the number of rows to fetch at a
        # time with .fetchmany(). It defaults to 1 meaning to fetch a single
        # row at a time.
        self.arraysize = 1

        # Per https://peps.python.org/pep-0249/#lastrowid, we can safely set this to None
        # https://rogerbinns.github.io/apsw/dbapi.html#optional-db-api-extensions
        self.lastrowid = None

        self.closed = False

        # this is updated only after a query
        self.description: Description = None

        # this is set to an iterator of rows after a successful query
        self._results: Optional[Iterator[Tuple[Any, ...]]] = None
        self._rowcount = -1

        def exectrace(cursor, sql, bindings):
            # In the case of an empty sequence, fall back to None,
            # meaning now rows returned.
            self.description = self._cursor.getdescription() or None
            return True

        self._cursor.setexectrace(exectrace)

    @property  # type: ignore
    @check_closed
    def rowcount(self) -> int:
        """
        Return the number of rows after a query.
        """
        try:
            results = list(self._results)  # type: ignore
        except TypeError:
            return -1

        n = len(results)
        self._results = iter(results)
        return max(0, self._rowcount) + n

    @check_closed
    def close(self) -> None:
        """
        Close the cursor.
        """
        self._cursor.close()
        self.closed = True

    @check_closed
    def execute(
        self,
        operation: str,
        parameters: Optional[Tuple[Any, ...]] = None,
    ) -> "Cursor":
        """
        Execute a query using the cursor.
        """
        if not self.in_transaction and self.isolation_level:
            self._cursor.execute(f"BEGIN {self.isolation_level}")
            self.in_transaction = True

        self.description = None
        self._rowcount = -1

        # convert parameters (bindings) to types accepted by SQLite
        if parameters:
            parameters = tuple(convert_binding(parameter) for parameter in parameters)

        try:
            self._cursor.execute(operation, parameters)
            self.description = self._get_description()
            self._results = self._convert(self._cursor)
        except apsw.SQLError as ex:
            message = ex.args[0]
            raise ProgrammingError(message) from ex

        return self

    def _convert(self, cursor: "apsw.Cursor") -> Iterator[Tuple[Any, ...]]:
        """
        Convert row from SQLite types to native Python types.

        Original notes; not sure if they still apply
        SQLite only supports 5 types. For booleans and time-related types
        we need to do the conversion here.
        """
        if not self.description:
            return

        for row in cursor:
            yield tuple(
                # convert from SQLite types to native Python types
                type_map[desc[1]](col)
                for col, desc in zip(row, self.description)
            )

    def _get_description(self) -> Description:
        """
        Return the cursor description.

        We only return name and type, since that's what we get from APSW.
        """
        try:
            description = self._cursor.getdescription()
        except apsw.ExecutionCompleteError:
            return self.description

        return [
            (
                name,
                get_type_code(type_name),
                None,
                None,
                None,
                None,
                True,
            )
            for name, type_name in description
        ]

    @check_closed
    def executemany(
        self,
        operation: str,
        seq_of_parameters: Optional[List[Tuple[Any, ...]]] = None,
    ) -> "Cursor":
        if seq_of_parameters is None:
            return

        for parameters in seq_of_parameters:
            self.execute(operation, parameters=parameters)

        return self

    @check_result
    @check_closed
    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """
        Fetch the next row of a query result set, returning a single sequence,
        or ``None`` when no more data is available.
        """
        try:
            row = self.next()
        except StopIteration:
            return None

        self._rowcount = max(0, self._rowcount) + 1

        return row

    @check_result
    @check_closed
    def fetchmany(self, size=None) -> List[Tuple[Any, ...]]:
        """
        Fetch the next set of rows of a query result, returning a sequence of
        sequences (e.g. a list of tuples). An empty sequence is returned when
        no more rows are available.
        """
        size = size or self.arraysize
        results = list(itertools.islice(self, size))

        return results

    @check_result
    @check_closed
    def fetchall(self) -> List[Tuple[Any, ...]]:
        """
        Fetch all (remaining) rows of a query result, returning them as a
        sequence of sequences (e.g. a list of tuples). Note that the cursor's
        arraysize attribute can affect the performance of this operation.
        """
        results = list(self)

        return results

    @check_closed
    def setinputsizes(self, sizes: int) -> None:
        """
        Used before ``execute`` to predefine memory areas for parameters.

        Currently not supported.
        """

    @check_closed
    def setoutputsizes(self, sizes: int) -> None:
        """
        Set a column buffer size for fetches of large columns.

        Currently not supported.
        """

    @check_result
    @check_closed
    def __iter__(self) -> Iterator[Tuple[Any, ...]]:
        for row in self._results:  # type: ignore
            self._rowcount = max(0, self._rowcount) + 1
            yield row

    @check_result
    @check_closed
    def __next__(self) -> Tuple[Any, ...]:
        return next(self._results)  # type: ignore

    next = __next__


def apsw_version() -> str:
    """
    Custom implementation of the ``VERSION`` function.

    This function shows the backend version::

        sql> SELECT VERSION();
        VERSION()
        ----------------------
        1.0.5 (apsw 3.36.0-r1)

    """
    return f"{functions.version()} (apsw {apsw.apswversion()})"


class Connection:

    """Connection."""

    def __init__(
        self,
        path: str,
        isolation_level: Optional[str] = None,
    ):
        # create underlying APSW connection
        self._connection = apsw.Connection(path)
        self.isolation_level = isolation_level

        # register functions
        available_functions = {
            "sleep": functions.sleep,
            "version": apsw_version,
        }
        for name, function in available_functions.items():
            self._connection.createscalarfunction(name, function)

        self.closed = False
        self.cursors: List[Cursor] = []

    @check_closed
    def close(self) -> None:
        """Close the connection now."""
        self.closed = True
        for cursor in self.cursors:
            if not cursor.closed:
                cursor.close()

    @check_closed
    def commit(self) -> None:
        """Commit any pending transaction to the database."""
        for cursor in self.cursors:
            if cursor.in_transaction:
                cursor._cursor.execute("COMMIT")  # pylint: disable=protected-access
                cursor.in_transaction = False

    @check_closed
    def rollback(self) -> None:
        """Rollback any transactions."""
        for cursor in self.cursors:
            if cursor.in_transaction:
                cursor._cursor.execute("ROLLBACK")  # pylint: disable=protected-access
                cursor.in_transaction = False

    @check_closed
    def cursor(self) -> Cursor:
        """Return a new Cursor Object using the connection."""
        cursor = Cursor(
            self._connection.cursor(),
            self.isolation_level,
        )
        self.cursors.append(cursor)

        return cursor

    @check_closed
    def execute(
        self,
        operation: str,
        parameters: Optional[Tuple[Any, ...]] = None,
    ) -> Cursor:
        """
        Execute a query on a cursor.
        """
        cursor = self.cursor()
        return cursor.execute(operation, parameters)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.commit()
        self.close()


def connect(
    path: str,
    isolation_level: Optional[str] = None,
) -> Connection:

    return Connection(
        path,
        isolation_level,
    )
