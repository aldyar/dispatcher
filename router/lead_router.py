from fastapi import APIRouter, HTTPException
from database.pydantic import LeadRequest,LeadSchema
from app.generator import send_to_openai,ask_gpt_to_categorize, send_to_openai_req
from typing import List
from function.lead_function import LeadFunction
from function.crm_requserts import CRM_DB
from function.operator_function import OperatorFunction
from function.tiktoken_function import TiktokenFunction
from function.category_function import CategoryFunction
import time
import asyncio

router = APIRouter(tags=["Leads"])


@router.post("/assign-lead")
async def receive_lead(lead: LeadRequest):
    # Используем поле message как диалог
    dialog_text = lead.message
    category = send_to_openai_req(dialog_text)  # Получаем направление права

    best_operator_id = await CategoryFunction.get_best_available_operator_by_category(category)

    return {
        **lead.dict(),  # ← возвращает все поля из запроса
        "category": category,
        "best_operator_id": best_operator_id
    }

async def set_lead_ster(leads: List[LeadSchema]):
    try:
        await LeadFunction.set_leads(leads)
        return {"message": f"Заявки успешно добавлены: {len(leads)}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# @router.post('/main_weely')
async def main_weely():
    print('INFO_____MainWeekly')
    start_time = time.time()

    #Сперва получаем операторов из CRM
    operators = await CRM_DB.get_operator_id_name()
    await OperatorFunction.set_operators(operators)

    #Получение заявок за последние 3 мес из CRM
    leads = await CRM_DB.get_recent_crm_leads()
    leads = LeadFunction.serialize_leads(leads)

    #Сохранение заявок в БД
    validated_leads = [LeadSchema(**lead) for lead in leads]
    await set_lead_ster(validated_leads)
    print(f"Заявки успешно добавлены: {len(leads)}")

    leads = await LeadFunction.fetch_unlabeled_leads()
    print(f"Всего лидов без категории: {len(leads)}")
    
    batches = await TiktokenFunction.split_leads_by_tokens(leads, 1500)
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

    await CategoryFunction.update_category_stats()
    print('INFO_____Статистика обновлена ')

    end_time = time.time()
    print(f"\n✅ Обработка завершена. Всего обработано: {len(all_results)} лидов.")
    print(f"⏱ Время выполнения: {end_time - start_time:.2f} секунд.")



#######################################################################################################################
#######################################################################################################################
#######################################################################################################################