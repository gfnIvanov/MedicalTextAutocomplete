import os
import re
import traceback
import yaml
import json
import html
import click
import logging
import requests
import psycopg2
import xml.etree.ElementTree as ET
from src import connect
from tqdm import tqdm
from typing import Iterator, Union
from pathlib import Path
from .types import NsiDictData, NsiPassportData
from .db_utils import FedNsiRaw, ClinRecRaw
from .cr_parser import cr_parser
from .exceptions import FedNsiExcept, ClinRecExcept

CURRENT_DIR = Path(__file__).resolve().parent
LOG = logging.getLogger(__name__)

@click.command()
@click.option("--dict_oid", type=click.STRING, required=False)
@click.option("--cr_code", type=click.STRING, required=False)
@click.option("--force", "-f", is_flag="True")
def process(dict_oid: Union[str, None] = None, cr_code: Union[str, None] = None, force: bool = False):
    """
    Функция для получения данных из источников, указанных в sources.yml

    dict_oid - при указании будут получены данные указанного справочника
    при условии, что он указан в fed_nsi sources.yml

    cr_code - при указании будут получены данные клинической рекомендации
    с соответствующим CODE

    force - при указании флага данные справочника (справочников),
    при наличии их в таблице FED_NSI_RAW, удаляются и запрашиваются заново
    при наличии связаннх данных в FED_NSI_CLEAN они удаляются каскадно

    запуск dvc repro по умолчанию выполняется с force
    """
    try:
        with open(CURRENT_DIR.joinpath("params/sources.yml"), "r") as f:
            sources = yaml.load(f, yaml.Loader)
        try:
            with connect:
                fed_nsi = sources["fed_nsi"]

                if dict_oid is not None:
                    dict_data = [x for x in fed_nsi["dicts"] if x["oid"] == dict_oid]
                    data_length = len(dict_data)
                    if data_length == 1:
                        passportData = get_nsi_passport(fed_nsi["url"], dict_data)

                        with connect.cursor() as cursor:
                            cursor.execute(FedNsiRaw.EXIST_BY_DICT_ID, (passportData["dict_id"], ))
                            if cursor.fetchone()[0] > 0:
                                if force:
                                    cursor.execute(FedNsiRaw.DEL_BY_DICT_ID, (passportData["dict_id"], ))
                                else:
                                    raise FedNsiExcept(f"Данные справочника \"{passportData["dict_name"]}\" уже содержатся в БД, для обновления используйте флаг force")

                        print(f"Получение справочника {dict_data[0]['oid']}")
                        for fields_data_list in get_nsi(fed_nsi["url"], dict_data=dict_data[0]):
                            with connect.cursor() as cursor:
                                text_content = " или ".join(fields_data_list["text_content"])
                                cursor.execute(FedNsiRaw.INSERT,
                                               (text_content, fields_data_list["dict_name"], fields_data_list["dict_id"]))
                                connect.commit()
                    elif data_length > 1:
                        raise FedNsiExcept(f"Дублирование справочника с oid {dict_oid} в src/data/params/sources.yml")
                    else:
                        raise FedNsiExcept(f"Справочник с oid {dict_oid} не найден в src/data/params/sources.yml")
                    return

                with connect.cursor() as cursor:
                    cursor.execute(FedNsiRaw.CHECK_FOR_REC)
                    if cursor.fetchone()[0] > 0:
                        if force:
                            cursor.execute(FedNsiRaw.DROP_ALL)
                        else:
                            raise FedNsiExcept(f"В таблице FED_NSI_RAW уже содержатся данные, для обновления используйте флаг force")

                for dict_data in tqdm(fed_nsi["dicts"], ascii=True, desc="Получение справочников nsi.rosminzdrav.ru"):
                    for fields_data_list in get_nsi(fed_nsi["url"], dict_data=dict_data):
                        with connect.cursor() as cursor:
                            text_content = " или ".join(fields_data_list["text_content"])
                            cursor.execute(FedNsiRaw.INSERT,
                                           (text_content, fields_data_list["dict_name"], fields_data_list["dict_id"]))
                            connect.commit()
        except psycopg2.Error as err:
            LOG.error(err)
            print("Ошибка при работе с разделом FED_NSI_RAW")
        except requests.RequestException as err:
            LOG.error(err)
            print("Ошибка при подключении к nsi.rosminzdrav.ru")
        except FedNsiExcept as err:
            print(err)

        try:
            with connect:
                clin_rec = sources["clin_rec"]

                if cr_code is not None:
                    with connect.cursor() as cursor:
                        cursor.execute(ClinRecRaw.EXIST_BY_CR_CODE, (cr_code, ))
                        if cursor.fetchone()[0] > 0:
                            if force:
                                cursor.execute(ClinRecRaw.DEL_BY_CR_CODE, (cr_code, ))
                            else:
                                raise ClinRecExcept(f"Данные клинической рекомендации с кодом {cr_code} уже содержатся в БД, для обновления используйте флаг force")

                    code, name = get_clin_rec_data(clin_rec["data_url"], cr_code)

                    print(f"Получение клинической рекомендации {name}")
                    for paragraph in cr_parser(clin_rec["schema_url"], cr_code):
                        with connect.cursor() as cursor:
                            cursor.execute(ClinRecRaw.INSERT, (paragraph, name, code))
                            connect.commit()
                    return

                with connect.cursor() as cursor:
                    cursor.execute(ClinRecRaw.CHECK_FOR_REC)
                    if cursor.fetchone()[0] > 0:
                        if force:
                            cursor.execute(ClinRecRaw.DROP_ALL)
                        else:
                            raise ClinRecExcept(f"В таблице CLIN_RECS_RAW уже содержатся данные, для обновления используйте флаг force")

                for cr_data in tqdm(get_clin_rec_data(clin_rec["data_url"]), ascii=True, desc="Получение клинических рекомендаций"):
                    code, name = cr_data

                    for paragraph in cr_parser(clin_rec["schema_url"], code):
                        with connect.cursor() as cursor:
                            cursor.execute(ClinRecRaw.INSERT, (paragraph, name, code))
                            connect.commit()
        except psycopg2.Error as err:
            LOG.error(err)
            print("Ошибка при работе с разделом CLIN_RECS_RAW")
        except requests.RequestException as err:
            LOG.error(err)
            print("Ошибка при подключении к cr.minzdrav.gov.ru")
        except ClinRecExcept as err:
            print(err)

    except Exception as err:
        LOG.error(err)
        if os.getenv("MODE") == "dev":
            traceback.print_tb(err.__traceback__)



def get_nsi(url: str, dict_data: NsiDictData) -> Iterator[list[str]]:
    """
    Функция для получения состава справочника fed_nsi
    """
    result = {}
    passportData = get_nsi_passport(url, dict_data)
    result.update(passportData)

    payload = {
        "identifier": dict_data["oid"],
        "userKey": os.getenv("FED_NSI_USER_KEY"),
        "columns": dict_data["fields"],
        "size": result["rows_count"]
    }

    resp = requests.get(url + "/data", params=payload, verify=False)

    if resp.status_code == 200:
        data = resp.json()

        for sublist in data["list"]:
            result["text_content"] = [x["value"] for x in sublist if x["value"] is not None and x["value"] != '']
            yield result
    else:
        raise requests.RequestException(f"Ошибка при подключении к сервису data: {resp.status_code}")



def get_nsi_passport(url: str, dict_data: NsiDictData) -> NsiPassportData:
    """
    Функция для получения паспортных данных справочника fed_nsi
    """
    result = {}
    payload = {"identifier": dict_data["oid"], "userKey": os.getenv("FED_NSI_USER_KEY")}
    resp = requests.get(url + "/passport", params=payload, verify=False)

    if resp.status_code == 200:
        data = resp.json()
        result["rows_count"] = data["rowsCount"]
        result["dict_name"] = data["fullName"]
        result["dict_id"] = data["nsiDictionaryId"]
        return result
    else:
        raise requests.RequestException(f"Ошибка при подключении к сервису passport: {resp.status_code}")


def get_clin_rec_data(url: str, code: Union[str, None] = None) -> Union[list[tuple[str, str]], tuple[str, str]]:
    results = []

    resp = requests.get(url)

    if resp.status_code == 200:
        data = resp.json()
        if code is not None:
            cr_data = list(filter(lambda x: x["code"] == int(code), data))
            if len(cr_data) > 0:
                return (cr_data[0]["code"], cr_data[0]["name"])
            raise ClinRecExcept(f"Клиническая рекомендация с кодом {code} не найдена")
        for x in data:
            results.append((x["code"], x["name"]))
        return results
    else:
        raise requests.RequestException(f"Ошибка при получении списка ID клинических рекомендаций: {resp.status_code}")
