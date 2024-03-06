include .env

RUN = poetry run
BASH = /bin/bash

# переменная для переопределения при вызове make
FLAGS =

# создание таблиц БД
init_db:
	$(BASH) db/init.sh $(DB_NAME)

# получение данных для дообучения модели
get_data:
	@if [[ ! -z "$(dict_oid)" ]] && [[ ! -z "$(cr_code)" ]]; then \
		$(RUN) get_data --dict_oid="$(dict_oid)" --cr_code="$(cr_code)" $(FLAGS); \
	elif [[ ! -z "$(dict_oid)" ]] && [[ -z "$(cr_code)" ]]; then \
		$(RUN) get_data --dict_oid="$(dict_oid)" $(FLAGS); \
	elif [[ -z "$(dict_oid)" ]] && [[ ! -z "$(cr_code)" ]]; then \
		$(RUN) get_data --cr_code="$(cr_code)" $(FLAGS); \
	else $(RUN) get_data $(FLAGS); \
	fi
