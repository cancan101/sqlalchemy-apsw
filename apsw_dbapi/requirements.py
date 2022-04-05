from sqlalchemy.testing.requirements import SuiteRequirements
from sqlalchemy.testing import exclusions

class Requirements(SuiteRequirements):
    @property
    def schemas(self):
        """Target database must support external schemas, and have one
        named 'test_schema'."""
        return exclusions.closed()
