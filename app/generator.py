import requests
from config import AI_TOKEN
from sandbox.test_list import LAW_CATEGORIES

def send_to_openai(message: str) -> str:
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
    print(prompt)
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]


# response = send_to_openai('привет меня зовут Aldiyar мне 23 и хочу узнать сколько штатов а США')
# print(response)


