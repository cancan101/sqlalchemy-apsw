from sqlalchemy.dialects import registry
import pytest

registry.register("sqlite.apsw", "apsw_dbapi.dialect", "APSWDialect")

pytest.register_assert_rewrite("sqlalchemy.testing.assertions")

from sqlalchemy.testing.plugin.pytestplugin import *
