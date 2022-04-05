from typing import List, Optional, Tuple, Type, Union

SQLiteValidType = Union[None, int, float, str, bytes]


# Cursor description
# https://peps.python.org/pep-0249/#description
Description = Optional[
    List[
        Tuple[
            str,
            str,  # type_code. Perhaps this should be of type DBAPIType
            Optional[str],
            Optional[str],
            Optional[str],
            Optional[str],
            Optional[bool],
        ]
    ]
]
