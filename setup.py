from pathlib import Path

from setuptools import find_packages, setup

# -----------------------------------------------------------------------------

DESCRIPTION = "An APSW driver for the sqlite Dialect in SQLAlchemy."
VERSION = "0.0.1.dev0"

# -----------------------------------------------------------------------------

# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
long_description_content_type = "text/markdown; charset=UTF-8; variant=GFM"

# -----------------------------------------------------------------------------

setup(
    name="sqlalchemy-apsw",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    author="Alex Rothberg",
    author_email="agrothberg@gmail.com",
    url="https://github.com/cancan101/sqlalchemy-apsw",
    packages=find_packages(exclude=("tests",)),
    entry_points={
        "sqlalchemy.dialects": [
            "sqlite.apsw = apsw_dbapi.dialect:APSWDialect",
        ],
    },
    install_requires=("sqlalchemy >= 1.3.0",),
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    # $ setup.py publish support.
    cmdclass={
        # "buildit": BuildCommand,
        # "uploadtest": UploadTestCommand,
        # "upload": UploadCommand,
    },
)
