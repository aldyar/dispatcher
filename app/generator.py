import requests
from config import AI_TOKEN
from app.category_list import LAW_CATEGORIES
from typing import List, Dict
from openai import AsyncOpenAI
from config import PROXY
import httpx

proxy_url = PROXY

transport = httpx.AsyncHTTPTransport(proxy=proxy_url)

client = AsyncOpenAI(
    api_key=AI_TOKEN
    ,http_client=httpx.AsyncClient(transport=transport)
)

def send_to_openai_req(message: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_TOKEN}",  # ← замени на свой ключ
        "Content-Type": "application/json"
    }
    prompt = f"""
Прочитай следующий диалог между клиентом и ботом. Определи, к какому разделу права он относится. 
Ответ должен быть одной строкой, без лишнего текста, только тип права строго из этого списка: {LAW_CATEGORIES}

Диалог:
{message}
"""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    proxies = {
        "http": PROXY,
        "https": PROXY,
    }
    # print(prompt)
    response = requests.post(url, headers=headers, json=data, proxies=proxies)

    response.raise_for_status()  # поднимет исключение, если ошибка

    return response.json()["choices"][0]["message"]["content"]


# response = send_to_openai('привет меня зовут Aldiyar мне 23 и хочу узнать сколько штатов а США')
# print(response)


async def ask_gpt_to_categorize(batch: List[Dict[str, str]]) -> List[Dict[str, str]]:
    allowed_categories = "\n".join(f"- {cat}" for cat in LAW_CATEGORIES)
    system_prompt = (
        "Ты опытный помощник-юрист. Проанализируй текст обращения и определи его юридическую категорию, "
        # "например: 'Семейное право', 'Трудовые споры', 'Военное право', 'Мошенничество', 'Социальные выплаты' и т.п. "
        # "Используй понятные человеку юридические категории. "
        # "Используй только **одну категорию** из строго ограниченного списка:\n\n"
        "Выбирай **только одну категорию** строго из следующего списка и не придумывай сам:\n\n"
        f"{allowed_categories}\n\n"
        "Верни список в формате JSON: [{\"id\": <число>, \"category\": <строка>}]."
        "Не используй форматирование Markdown, не добавляй ```json и другие символы — только чистый JSON."
        "Важно: используй **только те ID**, что указаны в сообщениях, не придумывай ID сам."
        "Если категория непонятна — напиши null. Не пропускай ни одно обращение."

    )

    user_input = "\n".join([
    f"id: {item['id']}, сообщение: {item['message']}" for item in batch
])

    # 🔧 Логируем весь prompt перед отправкой
    # print("========== GPT SYSTEM PROMPT ==========")
    # print(system_prompt)
    # print("========== GPT USER INPUT (batched) ==========")
    # print(user_input)
    # print("========================================")

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3
    )

    import json
    try:
        content = response.choices[0].message.content
        # print("========== RAW RESPONSE FROM GPT ==========")
        # print(content)
        # print("===========================================")
        return json.loads(content)
    except Exception as e:
        print("Ошибка парсинга JSON:", e)
        # print("Ответ GPT:", response.choices[0].message.content)
        return []
    

async def send_to_openai(data: str,message) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_TOKEN}",  # ← замени на свой ключ
        "Content-Type": "application/json"
    }
    prompt = f"""
Ты — умный аналитик. Получаешь статистику операторов:

📋 Формат данных:
Имя|Категория|All:всего/усп.(%)|W:всего/усп.(%)|M:всего/усп.(%)

📌 Условия:
— Учитывай только тех операторов, у кого за нужный период (W, M, All) минимум 5 заявок
— Не включай в ответ операторов с меньшим числом — даже если у них 100%
— Отвечай кратко, понятно и по-человечески
— Укажи имя, категорию, всего заявок, успешных и процент
— Не пиши формулы

Данные:
{data}

Вопрос:
{message}
"""
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    proxies = {
        "http": PROXY,
        "https": PROXY,
    }
    try:
        response = requests.post(url, headers=headers, json=data,proxies=proxies)
        response.raise_for_status()  # выбросит ошибку, если код ответа не 2xx
        res_json = response.json()

        if "choices" in res_json:
            return res_json["choices"][0]["message"]["content"]
        elif "error" in res_json:
            raise Exception(f"Ошибка от OpenAI: {res_json['error']['message']}")
        else:
            raise Exception(f"Неожиданный ответ от OpenAI: {res_json}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при запросе к OpenAI: {str(e)}")
    except Exception as e:
        raise Exception(f"Ошибка обработки ответа OpenAI: {str(e)}")