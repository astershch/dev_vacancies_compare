import os

import requests

from urllib.parse import urlencode

from dotenv import load_dotenv
from terminaltables import AsciiTable


SJ_DEVELOPERS_CATALOGUE_ID = 33


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


def process_sj_vacancies(url, headers, params):
    params = params.copy()

    vacancies_processed = 0
    all_salary = 0
    params['page'] = 0
    max_per_page = 100
    max_vacancies = 500

    found_vacancies = found_vacancies_amount_sj(url, headers=headers, params=params)

    if found_vacancies < max_vacancies:
        max_vacancies = found_vacancies

    if max_vacancies > max_per_page:
        params['count'] = max_per_page
    else:
        params['count'] = max_vacancies

    while params['page'] * params['count'] < max_vacancies:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        for vacancy in response.json()['objects']:
            salary = predict_rub_salary_sj(vacancy)

            if salary:
                vacancies_processed += 1
                all_salary += salary

        params['page'] += 1

    if vacancies_processed == 0:
        average_salary = 0
    else:
        average_salary = all_salary // vacancies_processed

    return [found_vacancies, vacancies_processed, average_salary]


def process_hh_vacancies(url, params):
    params = params.copy()

    vacancies_processed = 0
    all_salary = 0
    params['page'] = 0
    max_per_page = 100
    max_vacancies = 2000

    found_vacancies = found_vacancies_amount_hh(url, params=params)

    if found_vacancies < max_vacancies:
        max_vacancies = found_vacancies

    if max_vacancies > max_per_page:
        params['per_page'] = max_per_page
    else:
        params['per_page'] = max_vacancies

    while params['page'] * params['per_page'] < max_vacancies:
        response = requests.get(url, params=params)
        response.raise_for_status()

        for vacancy in response.json()['items']:
            salary = predict_rub_salary_hh(vacancy)

            if salary:
                vacancies_processed += 1
                all_salary += salary

        params['page'] += 1

    if vacancies_processed == 0:
        average_salary = 0
    else:
        average_salary = all_salary // vacancies_processed

    return [found_vacancies, vacancies_processed, average_salary]


def found_vacancies_amount_sj(url, headers, params):
    params = params.copy()

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()['total']


def found_vacancies_amount_hh(url, params):
    params = params.copy()

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()['found']


def get_table_format(title, output):
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

    return table_instance.table


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

    sj_vacancies_analytics = []
    sj_title = f'SuperJob {city}'
    sj_api_endpoint = 'https://api.superjob.ru/2.0/vacancies/'

    sj_headers = {
        'X-Api-App-Id': sj_api_key,
    }

    sj_params = {
        'catalogues': SJ_DEVELOPERS_CATALOGUE_ID,
        'town': city,
    }

    hh_vacancies_analytics = []
    hh_title = f'HeadHunter {city}'
    hh_area_id = get_area_id('Russia', city)
    hh_api_endpoint = 'https://api.hh.ru/vacancies'

    hh_params = {
        'area': hh_area_id,
        'period': 30,
    }

    for language in programming_languages:
        sj_params['keyword'] = language

        processed_sj_vacancies = process_sj_vacancies(
            sj_api_endpoint,
            headers=sj_headers,
            params=sj_params,
        )

        sj_vacancies_analytics.append(
            (language, *processed_sj_vacancies)
        )

        hh_params['text'] = f'Программист {language}'

        try:
            processed_hh_vacancies = process_hh_vacancies(
                hh_api_endpoint,
                params=hh_params,
            )

            hh_vacancies_analytics.append(
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

    sj_table = get_table_format(sj_title, sj_vacancies_analytics)
    hh_table = get_table_format(hh_title, hh_vacancies_analytics)

    print(sj_table)
    print(hh_table)


if __name__ == '__main__':
    main()
