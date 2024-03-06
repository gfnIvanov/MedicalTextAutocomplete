from dataclasses import dataclass


@dataclass
class NsiDictData:
    oid: str
    fields: list[str]


@dataclass
class NsiPassportData:
    rows_count: int
    dict_name: str
    dict_id: int
