# Сравниваем вакансии программистов
Скрипт позволяет сравнить средние зарплаты программистов для 10 языков программирования (JavaScript, Java, Python, PHP, C#, TypeScript, Kotlin, C++, C, Go) на сайтах hh.ru и superjob.ru.

### Как установить

Для работы скрипта необходимо добавить переменную окружения (или файл .env в корне скрипта):
- SUPERJOB_API_KEY - ключ для работы с API SuperJob (для получения необходимо [зарегистрировать](https://api.superjob.ru/register) приложение)

Python3 должен быть уже установлен. 
Затем используйте `pip` (или `pip3`, есть есть конфликт с Python2) для установки зависимостей:
```bash
pip install -r requirements.txt
```

### Как использовать

Запустить main.py:
```bash
>python main.py

+SuperJob Moscow--------+------------------+---------------------+-------------------+
| Язык программирования | Вакансий найдено | Вакансий обработано | Средняя зарплата  |
+-----------------------+------------------+---------------------+-------------------+
| JavaScript            | 62               | 43                  | 108569.0          |
| Java                  | 24               | 15                  | 173000.0          |
| Python                | 53               | 32                  | 116398.0          |
| PHP                   | 39               | 30                  | 138527.0          |
| C#                    | 15               | 12                  | 178666.0          |
| TypeScript            | 17               | 8                   | 159125.0          |
| Kotlin                | 4                | 4                   | 217750.0          |
| C++                   | 26               | 17                  | 157382.0          |
| C                     | 33               | 22                  | 121465.0          |
| Go                    | 7                | 3                   | 153000.0          |
+-----------------------+------------------+---------------------+-------------------+
+HeadHunter Moscow------+------------------+---------------------+-------------------+
| Язык программирования | Вакансий найдено | Вакансий обработано | Средняя зарплата  |
+-----------------------+------------------+---------------------+-------------------+
| JavaScript            | 7986             | 1053                | 137568.0          |
| Java                  | 4929             | 429                 | 181956.0          |
| Python                | 4820             | 627                 | 181574.0          |
| PHP                   | 3799             | 1078                | 134659.0          |
| C#                    | 3137             | 630                 | 145802.0          |
| TypeScript            | 2661             | 609                 | 186792.0          |
| Kotlin                | 1454             | 283                 | 203725.0          |
| C++                   | 3088             | 682                 | 146290.0          |
| C                     | 7127             | 1054                | 143177.0          |
| Go                    | 1426             | 380                 | 185271.0          |
+-----------------------+------------------+---------------------+-------------------+
```

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).