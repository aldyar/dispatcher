from database.models import async_session
from database.models import Lead, Operator
from sqlalchemy import select, update, delete, desc
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_,func,not_
from sqlalchemy.sql import exists
from database.pydantic import LeadSchema
from typing import List, Dict

def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner

class OperatorFunction:

    @connection
    async def sync_operators_from_leads(session):
        stmt = select(Lead.operator).distinct().where(Lead.operator.isnot(None))
        result = await session.execute(stmt)
        raw_operators = [row[0] for row in result.fetchall()]

        valid_operator_ids = set()
        for raw_op in raw_operators:
            try:
                op_id = int(raw_op)
                valid_operator_ids.add(op_id)
            except ValueError:
                continue  # пропускаем строки вроде "Не выбран", "None", "abc"

        if not valid_operator_ids:
            print("Нет валидных операторов для вставки.")
            return

        # Получаем уже существующие operator_id
        existing_stmt = select(Operator.operator_id).where(Operator.operator_id.in_(valid_operator_ids))
        existing_result = await session.execute(existing_stmt)
        existing_ids = {row[0] for row in existing_result.fetchall()}

        new_ids = valid_operator_ids - existing_ids
        if not new_ids:
            print("Все операторы уже есть в таблице.")
            return

        for op_id in new_ids:
            session.add(Operator(operator_id=op_id, name=None))  # Или name="Без имени"

        await session.commit()
        print(f"✅ Добавлено новых операторов: {len(new_ids)}")

    @connection
    async def set_operators(session, operators: list[tuple[int, str]]):
        for operator_id, name in operators:
            exists = await session.get(Operator, operator_id)
            if exists:
                continue  # если оператор уже есть, пропускаем
            session.add(Operator(operator_id=operator_id, name=name))
        await session.commit()

    @connection
    async def get_valid_operator_ids(session) -> list[int]:
        stmt = select(Operator.operator_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]
