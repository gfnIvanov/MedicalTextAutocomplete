from enum import Enum

class FedNsiRaw(str, Enum):
    INSERT = """
        insert into FED_NSI_RAW (TEXT_CONTENT, DICT_NAME, DICT_ID)
        values (%s, %s, %s);
        """,
    CHECK_FOR_REC = """
        select count(*)
          from FED_NSI_RAW
        """,
    EXIST_BY_DICT_ID = """
        select count(*)
          from FED_NSI_RAW
         where DICT_ID = %s;
        """,
    DEL_BY_DICT_ID = """
        delete from FED_NSI_RAW
         where DICT_ID = %s;
        """,
    DROP_ALL = """
        truncate FED_NSI_RAW cascade;
        """

class ClinRecRaw(str, Enum):
    INSERT = """
        insert into CLIN_RECS_RAW (TEXT_CONTENT, CLIN_REC_NAME, CLIN_REC_CODE)
        values (%s, %s, %s);
        """,
    CHECK_FOR_REC = """
        select count(*)
          from CLIN_RECS_RAW
        """,
    EXIST_BY_CR_CODE = """
        select count(*)
          from CLIN_RECS_RAW
         where CLIN_REC_CODE = %s;
        """,
    DEL_BY_CR_CODE = """
        delete from CLIN_RECS_RAW
         where CLIN_REC_CODE = %s;
        """,
    DROP_ALL = """
        truncate CLIN_RECS_RAW cascade;
        """