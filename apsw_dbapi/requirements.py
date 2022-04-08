from sqlalchemy.testing.requirements import SuiteRequirements
from sqlalchemy.testing import exclusions

class Requirements(SuiteRequirements):
    @property
    def schemas(self):
        """Target database must support external schemas, and have one
        named 'test_schema'."""
        # Testing with schemas is broken due to provision.py not called
        return exclusions.closed()

    @property
    def datetime_implicit_bound(self):
        """target dialect when given a datetime object will bind it such
        that the database server knows the object is a datetime, and not
        a plain string."""
        # The type of datetimes are lost when formatted and passed to execute
        return exclusions.closed()
