import streamlit as st
from openai import OpenAI
import requests
import json
import os
import parse_hh
import re

def is_valid_url(url: str) -> bool:
    """
    Проверяет, является ли строка корректным URL.

    :param url: Строка, которую нужно проверить.
    :return: True, если строка является URL, иначе False.
    """
    # Регулярное выражение для проверки URL
    regex = re.compile(
          r'^(?:http|https)://'  # Протокол (http, https, ftp)
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.)|'  # Доменное имя
        r'localhost|'  # Локальный хост
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
        r'\[?[A-F0-9]*:[A-F0-9:%.{1,}\[\\]?]+'  # IPv6
        r')'  # Закрывающая скобка
        r'(?::\d+)?'  # Порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, url) is not None

PROXY_API_KEY = os.getenv("PROXY_API_KEY")

SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.
Сначала напиши краткое заключение, которое будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими 
задачами сталкивался кандидат и каким образом их решал?), 
представь результат в виде оценки от 1 до 10.. 
Эта оценка заполнения резюме должна учитываться при выставлении финальной оценки - 
важно нанимать таких кандидатов, которые могут рассказать про свою работу.
Потом представь финальный результат в виде оценки от 1 до 10.
В дополнительной части укажи таблицу требуемых компетенций вакансии и соответствие компетенций в резюме.
""".strip()

def request_deep_seek(system_prompt: str, user_message: str, api_key: str = PROXY_API_KEY) -> dict:
    """
    Получает ответ от API deepseek-chat с системным промптом.

    :param system_prompt: Системный промпт для задания контекста.
    :param user_message: Сообщение от пользователя.
    :param api_key: Ключ API для авторизации.
    :return: Ответ от API в формате JSON.
    """
    url = "https://api.proxyapi.ru/deepseek/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        return  response_json['choices'][0]['message']['content']
    else:
        raise Exception(f"Ошибка {response.status_code}: {response.text}")



client = OpenAI(
    api_key = PROXY_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)

def request_gpt(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
        temperature=0,
    )
    return response.choices[0].message.content



st.title("CV Scoring App")

job_description_url = st.text_area("Enter the job description or desc-url").strip()
job_description = parse_hh.get_job_description(job_description_url) if is_valid_url(job_description_url) else job_description_url
cv_url = st.text_area("Enter the CV or CV-url").strip()
cv = parse_hh.get_candidate_info(cv_url) if is_valid_url(cv_url) else cv_url
if st.button("Score CV"):

    with st.spinner("Scoring CV..."):
        user_prompt = f"# ВАКАНСИЯ\n{job_description}\n\n # РЕЗЮМЕ\n{cv}"
        response = request_deep_seek(SYSTEM_PROMPT, user_prompt)

    st.write(response)