import os

import requests

from urllib.parse import urlencode

from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_area_id(base_country, base_area):
    area_api_endpoint = 'https://api.hh.ru/areas'

    response = requests.get(area_api_endpoint)
    response.raise_for_status()

    for country in response.json():
        if country['name'] == base_country:
            for area in country['areas']:
                if area['name'] == base_area:
                    return area['id']


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2

    elif salary_from:
        return 1.2 * salary_from

    elif salary_to:
        return 0.8 * salary_to


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return

    salary = predict_salary(
        vacancy['payment_from'],
        vacancy['payment_to'],
    )

    return salary


def predict_rub_salary_hh(vacancy):
    if vacancy.get('salary'):
        if vacancy['salary']['currency'] != 'RUR':
            return

        salary = predict_salary(
            vacancy['salary'].get('from'),
            vacancy['salary'].get('to'),
        )

        return salary


def process_vacancies(params, settings, headers=None):
    params = params.copy()

    predict_func = None

    if settings['platform'] == 'sj':
        predict_func = predict_rub_salary_sj
    elif settings['platform'] == 'hh':
        predict_func = predict_rub_salary_hh

    vacancies_processed = 0
    all_salary = 0

    found_vacancies = found_vacancies_amount(
        headers=headers,
        params=params,
        settings=settings,
    )

    page_key = settings['page_key']
    per_page_key = settings['per_page_key']
    vacancies_key = settings['vacancies_key']
    params[page_key] = settings['start_page']
    max_per_page = settings['max_per_page']
    max_vacancies = settings['max_vacancies']

    if found_vacancies < max_vacancies:
        max_vacancies = found_vacancies

    if max_vacancies > max_per_page:
        params[per_page_key] = max_per_page
    else:
        params[per_page_key] = max_vacancies

    while params[page_key] * params[per_page_key] < max_vacancies:
        response = requests.get(settings['api_endpoint'], headers=headers, params=params)
        response.raise_for_status()

        for vacancy in response.json()[vacancies_key]:
            salary = predict_func(vacancy)

            if salary:
                vacancies_processed += 1
                all_salary += salary

        params[page_key] += 1

    if vacancies_processed == 0:
        average_salary = 0
    else:
        average_salary = all_salary // vacancies_processed

    return [found_vacancies, vacancies_processed, average_salary]


def found_vacancies_amount(params, settings, headers=None):
    params = params.copy()

    found_key = settings['found_key']

    response = requests.get(settings['api_endpoint'], headers=headers, params=params)
    response.raise_for_status()

    return response.json()[found_key]


def print_table(title, output):

    table_output = [
        (
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата '
        )
    ]
    table_output.extend(output)

    table_instance = AsciiTable(table_output, title)

    print(table_instance.table)


def main():
    city = 'Moscow'

    programming_languages = [
        'JavaScript',
        'Java',
        'Python',
        'PHP',
        'C#',
        'TypeScript',
        'Kotlin',
        'C++',
        'C',
        'Go',
    ]

    load_dotenv()
    sj_api_key = os.environ['SUPERJOB_API_KEY']

    sj_vacancies_table = []
    sj_title = f'SuperJob {city}'

    sj_headers = {
        'X-Api-App-Id': sj_api_key,
    }

    sj_params = {
        'catalogues': 33,
        'town': city,
    }

    sj_settings = {
        'platform': 'sj',
        'api_endpoint': 'https://api.superjob.ru/2.0/vacancies/',
        'page_key': 'page',
        'per_page_key': 'count',
        'vacancies_key': 'objects',
        'found_key': 'total',
        'start_page': 0,
        'max_per_page': 100,
        'max_vacancies': 500,

    }

    hh_vacancies_table = []
    hh_title = f'HeadHunter {city}'
    hh_area_id = get_area_id('Russia', city)

    hh_params = {
        'area': hh_area_id,
        'period': 30,
    }

    hh_settings = {
        'platform': 'hh',
        'api_endpoint': 'https://api.hh.ru/vacancies',
        'page_key': 'page',
        'per_page_key': 'per_page',
        'vacancies_key': 'items',
        'found_key': 'found',
        'start_page': 0,
        'max_per_page': 100,
        'max_vacancies': 2000,
    }

    for language in programming_languages:
        sj_params['keyword'] = language

        processed_sj_vacancies = process_vacancies(
            headers=sj_headers,
            params=sj_params,
            settings=sj_settings,
        )

        sj_vacancies_table.append(
            (language, *processed_sj_vacancies)
        )

        hh_params['text'] = f'Программист {language}'

        try:
            processed_hh_vacancies = process_vacancies(
                params=hh_params,
                settings=hh_settings,
            )

            hh_vacancies_table.append(
                (language, *processed_hh_vacancies)
            )

        except requests.exceptions.HTTPError as exception:
            for error in exception.response.json()['errors']:
                if error.get('value') == 'captcha_required':
                    params = {
                        'backurl': 'https://hh.ru'
                    }
                    base_url = error['captcha_url']
                    query_string = urlencode(params)

                    print(f'Для работы скрипта нужно пройти капчу по ссылке: {base_url}?{query_string}')
                    break

            print(exception)

    print_table(sj_title, sj_vacancies_table)
    print_table(hh_title, hh_vacancies_table)


if __name__ == '__main__':
    main()
