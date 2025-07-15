from database.models import async_session
from database.models import Lead
from sqlalchemy import select, update, delete, desc
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_,func,not_
from sqlalchemy.sql import exists
from database.pydantic import LeadSchema
from typing import List, Dict
from function.operator_function import OperatorFunction
def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner

VALID_OPERATORS = {'231', '233', '239', '245', '271', '321', '444', '541', '543'}
class LeadFunction:

    @connection
    async def set_leads(session, leads_data: list[LeadSchema]):
        for item in leads_data:
            lead = Lead(
                id=item.id,
                message=item.message,
                status=item.status,
                source=item.source,
                operator=item.operator,
                created_at=item.created_at,
                office=item.office,
                city=item.city
            )
            session.add(lead)
        await session.commit()

    def serialize_leads(leads):
        # преобразуем datetime → str
        for lead in leads:
            if isinstance(lead.get("created_at"), datetime):
                lead["created_at"] = lead["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return leads


    

    @connection
    async def fetch_two_leads_per_operator(session) -> list[tuple[int, str]]:
        all_leads = []

        for op in VALID_OPERATORS:
            stmt = (
                select(Lead.id, Lead.message)
                .where(
                    Lead.operator == op,
                    Lead.category.is_(None),
                    Lead.message.is_not(None)
                )
                .limit(2)
            )
            result = await session.execute(stmt)
            leads = result.all()
            all_leads.extend(leads)

        return all_leads
    
    @connection
    async def update_lead_categories(session, categorized_data: List[Dict[str, str]]):
        """
        Обновляет категории у лидов на основе результата GPT.
        """
        for item in categorized_data:
            lead_id = item["id"]
            category = item["category"]

            # Найдём лид по id
            result = await session.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()

            if lead:
                lead.category = category

        await session.commit()

    @connection
    async def fetch_unlabeled_leads(session) -> List[Dict[str, str]]:

        valid_operator_ids = await OperatorFunction.get_valid_operator_ids()

        stmt = select(Lead.id, Lead.message).where(
            Lead.category.is_(None),
            Lead.message.is_not(None),
            Lead.operator.in_(VALID_OPERATORS)
        )
        result = await session.execute(stmt)
        rows = result.all()
        return [{"id": row[0], "message": row[1]} for row in rows]
    
    @connection
    async def update_lead_categories(session, categorized_data: List[Dict[str, str]]):
        for item in categorized_data:
            lead_id = item["id"]
            category = item["category"]

            result = await session.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()

            if lead:
                lead.category = category

        await session.commit()