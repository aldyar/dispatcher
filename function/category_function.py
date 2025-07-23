from database.models import async_session
from database.models import Lead,Operator,CategoryStats
from sqlalchemy import select, update, delete, desc, case
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_,func,not_
from sqlalchemy.sql import exists
from database.pydantic import LeadSchema
from typing import List, Dict
from app.category_list import LAW_CATEGORIES,SUCCESS_STATUSES,FAIL_STATUSES
import random

def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner

class CategoryFunction:

    # OK
    @connection
    async def update_category_stats(session):
        # Получаем всех операторов
        operators = await session.execute(select(Operator))
        operators = operators.scalars().all()

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        for operator in operators:
            for category in LAW_CATEGORIES:
                # Базовый фильтр
                base_filter = and_(
                    Lead.operator == operator.operator_id,
                    Lead.category == category,
                    Lead.status.in_(SUCCESS_STATUSES.union(FAIL_STATUSES))
                )

                # За всё время
                all_time_q = await session.execute(
                    select(
                        func.count().label("total"),
                        func.sum(case((Lead.status.in_(SUCCESS_STATUSES), 1),else_=0)).label("success")
                    ).where(base_filter)
                )
                all_time_total, all_time_success = all_time_q.first() or (0, 0)
                all_time_total = all_time_total or 0
                all_time_success = all_time_success or 0

                # За последнюю неделю
                last_week_q = await session.execute(
                    select(
                        func.count().label("total"),
                        func.sum(case((Lead.status.in_(SUCCESS_STATUSES), 1), else_=0)).label("success")
                    ).where(
                        and_(
                            base_filter,
                            Lead.created_at >= week_ago
                        )
                    )
                )
                week_total, week_success = last_week_q.first() or (0, 0)
                week_total = week_total or 0
                week_success = week_success or 0

                # За последний месяц
                last_month_q = await session.execute(
                    select(
                        func.count().label("total"),
                        func.sum(case((Lead.status.in_(SUCCESS_STATUSES), 1), else_=0)).label("success")
                    ).where(
                        and_(
                            base_filter,
                            Lead.created_at >= month_ago
                        )
                    )
                )
                month_total, month_success = last_month_q.first() or (0, 0)
                month_total = month_total or 0
                month_success = month_success or 0

                # Формируем строки
                all_time_str = f"{all_time_total},{all_time_success}"
                week_str = f"{week_total},{week_success}"
                month_str = f"{month_total},{month_success}"

                # Проверка: есть ли уже запись
                existing = await session.execute(
                    select(CategoryStats).where(
                        and_(
                            CategoryStats.operator_id == operator.operator_id,
                            CategoryStats.category == category
                        )
                    )
                )
                existing_stat = existing.scalars().first()

                if existing_stat:
                    existing_stat.three_month = all_time_str
                    existing_stat.last_week = week_str
                    existing_stat.last_month = month_str
                else:
                    new_stat = CategoryStats(
                        operator_id=operator.operator_id,
                        operator_name =operator.name,
                        category=category,
                        three_month=all_time_str,
                        last_week=week_str,
                        last_month=month_str
                    )
                    session.add(new_stat)

        await session.commit()

    # @connection
    # async def generate_stats_text(session) -> str:
    #     stats_query = await session.execute(select(CategoryStats))
    #     stats = stats_query.scalars().all()

    #     result = []

    #     for stat in stats:
    #         operator = stat.operator_name or f"Оператор #{stat.operator_id}"
    #         category = stat.category

    #         def parse_stats(stat_str):
    #             if not stat_str:
    #                 return 0, 0
    #             try:
    #                 total, success = map(int, stat_str.split(","))
    #                 fail = total - success
    #                 percent = f"{(success / total * 100):.1f}%" if total > 0 else "0%"
    #                 return total, success, fail, percent
    #             except:
    #                 return 0, 0, 0, "0%"

    #         all_total, all_success, all_fail, all_percent = parse_stats(stat.three_month)
    #         week_total, week_success, week_fail, week_percent = parse_stats(stat.last_week)
    #         month_total, month_success, month_fail, month_percent = parse_stats(stat.last_month)

    #         block = (
    #             f"Оператор: {operator}\n"
    #             f"Категория: {category}\n"
    #             f"📊 За всё время: {all_total} лидов | Успешных: {all_success} | Неуспешных: {all_fail} | Успешность: {all_percent}\n"
    #             f"📅 За последнюю неделю: {week_total} | Успешных: {week_success} | Неуспешных: {week_fail} | {week_percent}\n"
    #             f"🗓️ За последний месяц: {month_total} | Успешных: {month_success} | Неуспешных: {month_fail} | {month_percent}\n"
    #             f"{'-'*40}"
    #         )
    #         result.append(block)

    #     return "\n".join(result)
    

    # Ниже похожая функция
    # @connection
    # async def generate_compact_stats_text(session) -> str:
    #     stats_query = await session.execute(select(CategoryStats))
    #     stats = stats_query.scalars().all()

    #     result = ["Имя|Категория|All:Всего/Усп.(%)|W:Всего/Усп.(%)|M:Всего/Усп.(%)"]

    #     def parse(stat_str):
    #         try:
    #             total, success = map(int, (stat_str or "0,0").split(","))
    #             percent = f"{(success / total * 100):.1f}%" if total > 0 else "0%"
    #         except Exception:
    #             total, success, percent = 0, 0, "0%"
    #         return total, success, percent

    #     for stat in stats:
    #         operator = stat.operator_name or f"Оператор#{stat.operator_id}"
    #         category = stat.category

    #         all_t, all_s, all_p = parse(stat.three_month)
    #         week_t, week_s, week_p = parse(stat.last_week)
    #         month_t, month_s, month_p = parse(stat.last_month)

    #         line = (
    #             f"{operator}|{category}"
    #             f"|All:{all_t}/{all_s}({all_p})"
    #             f"|W:{week_t}/{week_s}({week_p})"
    #             f"|M:{month_t}/{month_s}({month_p})"
    #         )
    #         result.append(line)

    #     return "\n".join(result)

    # @connection
    # async def get_best_operator_by_category(session, category: str):
    #     stmt = select(CategoryStats).where(CategoryStats.category == category)
    #     result = await session.execute(stmt)
    #     stats = result.scalars().all()

    #     best_operator_id = None
    #     best_percent = -1.0

    #     for stat in stats:
    #         if not stat.three_month:
    #             continue

    #         try:
    #             total_str, success_str = stat.three_month.split(',')
    #             total = int(total_str)
    #             success = int(success_str)
    #         except ValueError:
    #             continue  # если данные невалидны

    #         if total < 5:
    #             continue

    #         efficiency = (success / total) * 100

    #         if efficiency > best_percent:
    #             best_percent = efficiency
    #             best_operator_id = stat.operator_id

    #     return best_operator_id
    
    # OK
    @connection
    async def get_best_available_operator_by_category(session, category: str) -> int | None:
        # Получаем все записи по категории
        stmt = select(CategoryStats).where(CategoryStats.category == category)
        result = await session.execute(stmt)
        stats = result.scalars().all()

        if not stats:
            return None

        # Получаем всех операторов (для проверки онлайн)
        operators_stmt = select(Operator)
        op_result = await session.execute(operators_stmt)
        all_operators = op_result.scalars().all()
        online_map = {op.operator_id: op.online for op in all_operators}

        best_operator_id = None
        best_percent = -1.0
        online_candidates = []

        for stat in stats:
            if not stat.three_month:
                continue

            try:
                total_str, success_str = stat.three_month.split(',')
                total = int(total_str)
                success = int(success_str)
            except ValueError:
                continue

            if total < 5:
                continue

            efficiency = (success / total) * 100
            is_online = online_map.get(stat.operator_id, False)

            if is_online:
                online_candidates.append((stat.operator_id, efficiency))

            if efficiency > best_percent:
                best_percent = efficiency
                best_operator_id = stat.operator_id

        # Приоритет: среди онлайн, у кого efficiency > 0
        if online_candidates:
            online_candidates.sort(key=lambda x: x[1], reverse=True)
            chosen_id = online_candidates[0][0]
            print(f"✅ Выбран лучший онлайн оператор с ID: {chosen_id}")
            return chosen_id

        # Если онлайн, но нет подходящих по эффективности — выбираем рандомного онлайн
        online_ids = [op_id for op_id, is_on in online_map.items() if is_on]
        if online_ids:
            chosen_id = random.choice(online_ids)
            print(f"⚠️ Подходящих не найдено, выбран случайный онлайн оператор с ID: {chosen_id}")
            return chosen_id

        # Если вообще никто не онлайн — вернём рандомного из всех
        all_ids = list(online_map.keys())
        if all_ids:
            chosen_id = random.choice(all_ids)
            print(f"🔄 Никто не онлайн, выбран случайный оператор из всех с ID: {chosen_id}")
            return chosen_id

        return None  # если никого нет вообще