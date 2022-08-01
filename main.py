import os

import requests

from urllib.parse import urlencode

from dotenv import load_dotenv
from terminaltables import AsciiTable


SJ_DEVELOPERS_CATALOGUE_ID = 33
VACANCIES_PER_PAGE = 100


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
    if not vacancy.get('salary'):
        return

    if vacancy['salary']['currency'] != 'RUR':
        return

    salary = predict_salary(
        vacancy['salary'].get('from'),
        vacancy['salary'].get('to'),
    )

    return salary


def process_sj_vacancies(url, headers, params):
    params = params.copy()

    found_vacancies = 0
    vacancies_processed = 0
    all_salary = 0
    params['page'] = 0
    params['count'] = VACANCIES_PER_PAGE
    max_vacancies = 500

    while params['page'] * params['count'] < max_vacancies:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        for vacancy in response.json()['objects']:
            salary = predict_rub_salary_sj(vacancy)

            if salary:
                vacancies_processed += 1
                all_salary += salary

        if not params['page']:
            found_vacancies = response.json()['total']
            max_vacancies = min(found_vacancies, max_vacancies)

        params['page'] += 1

    if not vacancies_processed:
        average_salary = 0
    else:
        average_salary = all_salary // vacancies_processed

    return [found_vacancies, vacancies_processed, average_salary]


def process_hh_vacancies(url, params):
    params = params.copy()

    found_vacancies = 0
    vacancies_processed = 0
    all_salary = 0
    params['page'] = 0
    params['per_page'] = VACANCIES_PER_PAGE
    max_vacancies = 2000

    while params['page'] * params['per_page'] < max_vacancies:
        response = requests.get(url, params=params)
        response.raise_for_status()

        for vacancy in response.json()['items']:
            salary = predict_rub_salary_hh(vacancy)

            if salary:
                vacancies_processed += 1
                all_salary += salary

        if not params['page']:
            found_vacancies = response.json()['found']
            max_vacancies = min(found_vacancies, max_vacancies)

        params['page'] += 1

        print(params['page'], params['per_page'], found_vacancies, 'hh')

    if not vacancies_processed:
        average_salary = 0
    else:
        average_salary = all_salary // vacancies_processed

    return [found_vacancies, vacancies_processed, average_salary]


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
        print(language)

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

                    print(
                        f'Для работы скрипта нужно пройти капчу по ссылке: '
                        f'{base_url}?{query_string}'
                    )
                    break

            print(exception)

    sj_table = get_table_format(sj_title, sj_vacancies_analytics)
    hh_table = get_table_format(hh_title, hh_vacancies_analytics)

    print(sj_table)
    print(hh_table)


if __name__ == '__main__':
    main()
