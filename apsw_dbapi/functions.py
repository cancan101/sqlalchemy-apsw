"""
Custom functions available to the SQL backend.
"""
import time

import pkg_resources

__all__ = ["sleep", "version"]


def sleep(seconds: int) -> None:
    """
    Sleep for ``n`` seconds.

    This is useful for troubleshooting timeouts::

        sql> SELECT sleep(60);

    """
    time.sleep(seconds)


def version() -> str:
    """
    Return the current version of sqlalchemy-apsw.

    As an example::

        sql> SELECT VERSION();
        VERSION()
        -----------
        0.7.4

    """
    return pkg_resources.get_distribution("sqlalchemy-apsw").version
