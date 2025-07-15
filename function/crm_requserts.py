from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta
from sqlalchemy import JSON


engine = create_async_engine(url="mysql+aiomysql://aldi:Test2025@194.58.123.164:3306/pkcrm",
                             echo=False)
    
    
async_session = async_sessionmaker(engine,class_=AsyncSession)

def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner


class CRM_DB:
    
    @connection
    async def get_recent_crm_leads(session):
        three_months_ago = datetime.now() - timedelta(days=90)
        query = text("""
            SELECT id, city, message, status, source, office, operator, created_at
            FROM leads
            WHERE created_at >= :start_date
        """)

        result = await session.execute(query, {"start_date": three_months_ago})
        rows = result.mappings().all()  # Возвращает список словарей
        return [dict(row) for row in rows]
    
    @connection
    async def get_operator_id_name(session) -> list[tuple[int, str]]:
        result = await session.execute(
            text("""
                SELECT users.id, users.name
                FROM users
                JOIN model_has_roles ON users.id = model_has_roles.model_id
                WHERE model_has_roles.role_id = 3
            """)
        )
        return result.all()  # список кортежей (id, name)
