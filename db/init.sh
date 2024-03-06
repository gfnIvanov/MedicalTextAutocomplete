psql -d $1 <<EOF
create table if not exists FED_NSI_RAW (
  ID           INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  TEXT_CONTENT INTEGER,
  DICT_NAME    CHAR(400),
  DICT_ID      INTEGER
);

create table if not exists FED_NSI_CLEAN (
  ID           INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  PID          INTEGER,
  TEXT_CONTENT TEXT,
  CLEAN_VER    INTEGER,
  constraint FK_PID
     foreign key(PID) references FED_NSI_RAW(ID) on delete cascade
);

create table if not exists CLIN_RECS_RAW (
  ID            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  TEXT_CONTENT  TEXT,
  CLIN_REC_NAME CHAR(400),
  CLIN_REC_CODE INT
);

create table if not exists CLIN_RECS_CLEAN (
  ID           INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  PID          INTEGER,
  TEXT_CONTENT TEXT,
  CLEAN_VER    INTEGER,
  constraint FK_PID
     foreign key(PID) references CLIN_RECS_RAW(ID) on delete cascade
);
EOF