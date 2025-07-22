from sqlalchemy import ForeignKey, String, BigInteger, DateTime, Boolean, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from datetime import datetime
from sqlalchemy import JSON


engine = create_async_engine(url="mysql+aiomysql://root:1234@localhost:3306/dispatcher",
                             echo=False)
    
    
async_session = async_sessionmaker(engine,class_=AsyncSession)


class Base(AsyncAttrs, DeclarativeBase):
    pass

class Lead(Base):
    __tablename__ = 'leads'

    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=True)  
    source: Mapped[str] = mapped_column(String(64), nullable=True)
    operator: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    office: Mapped[str] = mapped_column(String(64), nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(255), nullable=True)


class Operator(Base):
    __tablename__ = "operators"

    operator_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=True)


class CategoryStats(Base):
    __tablename__ = 'category_stats'

    id: Mapped[int] = mapped_column(primary_key=True)
    operator_id: Mapped[int] = mapped_column(Integer, nullable=True)
    operator_name: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(255), nullable=True)
    three_month: Mapped[str] = mapped_column(String(64), nullable=True)
    last_week: Mapped[str] = mapped_column(String(64), nullable=True)
    last_month: Mapped[str] = mapped_column(String(64), nullable=True)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)