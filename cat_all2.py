from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Lead
from openai import AsyncOpenAI
import asyncio
from config import AI_TOKEN
from function.lead_function import LeadFunction
import tiktoken
import time

# Константы
MAX_TOKENS = 9000  # для входа, чтобы ответ уместился
client = AsyncOpenAI(api_key=AI_TOKEN)

tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

def estimate_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

async def split_leads_by_tokens(leads: List[Dict[str, str]], max_tokens: int) -> List[List[Dict[str, str]]]:
    batches = []
    current_batch = []
    current_tokens = 0

    for lead in leads:
        line = f"id: {lead['id']}, сообщение: {lead['message']}"
        token_count = estimate_tokens(line)

        if current_tokens + token_count > max_tokens:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(lead)
        current_tokens += token_count

    if current_batch:
        print(f"[DEBUG] Финальный батч — {len(current_batch)} лидов, {current_tokens} токенов")
        batches.append(current_batch)

    return batches

async def ask_gpt_to_categorize(batch: List[Dict[str, str]]) -> List[Dict[str, str]]:
    system_prompt = (
        "Ты опытный помощник-юрист. Проанализируй текст обращения и определи его юридическую категорию, "
        "например: 'Семейное право', 'Трудовые споры', 'Военное право', 'Мошенничество', 'Социальные выплаты' и т.п. "
        "Используй понятные человеку юридические категории. "
        "Верни список в формате JSON: [{\"id\": <число>, \"category\": <строка>}]."
        "Не используй форматирование Markdown, не добавляй ```json и другие символы — только чистый JSON."
        "Важно: используй **только те ID**, что указаны в сообщениях, не придумывай ID сам."
        "Для каждого объекта укажи категорию. Если категория непонятна — напиши null"

    )

    user_input = "\n".join([
    f"id: {item['id']}, сообщение: {item['message']}" for item in batch
])

    # # 🔧 Логируем весь prompt перед отправкой
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
        return json.loads(content)
    except Exception as e:
        print("Ошибка парсинга JSON:", e)
        print("Ответ GPT:", response.choices[0].message.content)
        return []

async def run_full_job():
    start_time = time.time()
    leads = await LeadFunction.fetch_unlabeled_leads()
    print(f"Всего лидов без категории: {len(leads)}")

    batches = await split_leads_by_tokens(leads, MAX_TOKENS)
    print(f"Подготовлено батчей: {len(batches)}")

    all_results = []
    for i, batch in enumerate(batches):
        print(f"Обработка батча {i+1}/{len(batches)}...")
        ids = [lead['id'] for lead in batch]
        #print(f"IDs в батче: {ids}")

        try:
            categorized = await ask_gpt_to_categorize(batch)
            print(f"✅ Получено {len(categorized)} категорий")
            # print("✅ Ответ от GPT:")
            # print(categorized)
        except Exception as e:
            print("❌ Ошибка при обращении к GPT:", e)
            continue  # переходим к следующему батчу

        try:
            await LeadFunction.update_lead_categories(categorized)
            print(f"✅ Категории обновлены для {len(categorized)} лидов")
        except Exception as e:
            print("❌ Ошибка при обновлении категорий в базе данных:", e)
            continue

        all_results.extend(categorized)
        await asyncio.sleep(1)

    end_time = time.time()
    print(f"\n✅ Обработка завершена. Всего обработано: {len(all_results)} лидов.")
    print(f"⏱ Время выполнения: {end_time - start_time:.2f} секунд.")

    #await LeadFunction.update_lead_categories(all_results)
    #print("Обновление категорий завершено.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_full_job())