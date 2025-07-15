from fastapi import APIRouter, HTTPException
from database.pydantic import LeadRequest,LeadSchema
from app.generator import send_to_openai
from typing import List
from function.lead_function import LeadFunction
from function.crm_requserts import CRM_DB
from function.operator_function import OperatorFunction
import json

router = APIRouter(
    prefix="/leads",
    tags=["Leads"]
)

@router.post("/")
async def receive_lead(lead: LeadRequest):
    # Используем поле message как диалог
    dialog_text = lead.message
    category = send_to_openai(dialog_text)  # Получаем направление права

    return {
        "status": "ok",
        "category": category
    }

@router.post("/import")
async def receive_leads(leads: List[LeadSchema]):
    try:
        await LeadFunction.set_leads(leads)
        return {"message": f"Заявки успешно добавлены: {len(leads)}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/all_leads')
async def export_recent_leads():
    print('INFO______ /all_leads')

    #Сперва получаем операторов из CRM
    operators = await CRM_DB.get_operator_id_name()
    await OperatorFunction.set_operators(operators)

    #Получение заявок за последние 3 мес из CRM
    leads = await CRM_DB.get_recent_crm_leads()
    leads = LeadFunction.serialize_leads(leads)

    #Сохранение заявок в БД
    validated_leads = [LeadSchema(**lead) for lead in leads]
    await receive_leads(validated_leads)
    print(f"Заявки успешно добавлены: {len(leads)}")

    leads = await LeadFunction.fetch_unlabeled_leads()
    
    # with open("test_leads.json", "w", encoding="utf-8") as f:
    #     json.dump(leads, f, ensure_ascii=False, indent=2)

    # return {"message": f"{len(leads)} заявок сохранено в test_leads.json"}


@router.post("/test")
async def test_handler():
    print("/Test started")

    # Шаг 1: Получение операторов из CRM
    operators = await CRM_DB.get_operator_id_name()
    print(f"Найдено операторов с ролью 3: {len(operators)}")

    # Шаг 2: Запись операторов в БД
    await OperatorFunction.set_operators(operators)
    print("Операторы записаны в БД:")

    # Печать списка
    for op_id, name in operators:
        print(f"  ID: {op_id}, Name: {name}")

    return {"status": "ok", "inserted": len(operators)}

@router.post('/testto')
async def test_handler():
    return {'OK!'}
