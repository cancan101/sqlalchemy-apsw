from sqlalchemy.dialects import registry # type: ignore
import pytest

# In case we haven't installed the package, we can still use the dialect
registry.register("sqlite.apsw", "apsw_dbapi.dialect", "APSWDialect")

# suppress a spurious warning from pytest
pytest.register_assert_rewrite("sqlalchemy.testing.assertions")

# bootstraps SQLAlchemy's pytest plugin into the pytest runner.
from sqlalchemy.testing.plugin.pytestplugin import *
