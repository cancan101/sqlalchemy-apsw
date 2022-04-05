# sqlalchemy-apsw
An APSW driver for the sqlite Dialect in SQLAlchemy

Code originally copied from https://github.com/rogerbinns/apsw and then Virtual Table logic stripped out.

## Example
```python
from sqlalchemy import create_engine

engine = create_engine('sqlite+apsw:///')
```
