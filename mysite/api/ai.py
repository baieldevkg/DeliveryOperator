import asyncio
from typing import List
from fastapi import APIRouter, HTTPException
from langchain_core.exceptions import OutputParserException
from mysite.chain.analyze_chain import analyze_chain
from mysite.chain.create_chain import plan_chain
from mysite.database.schema import (
    MeetingTextInputSchema, MeetingTaskSchema,
    MeetingTaskStatsSchema, MeetingTaskCheckSchema, MeetingTaskReportSchema,
    TodoPlanInputSchema, TodoPlanOutSchema,
)

meeting_router = APIRouter(prefix='/meetings', tags=['Meetings'])


@meeting_router.post('/analyze/', response_model=List[MeetingTaskSchema])
async def analyze_meeting(meeting: MeetingTextInputSchema):
    text = meeting.text.strip()

    if not text:
        raise HTTPException(status_code=422, detail='Маалымат туура эмес формата берилип жатат')

    try:
        result = await asyncio.wait_for(
            analyze_chain.ainvoke({"text": text}), timeout=120
        )
    except TimeoutError:
        raise HTTPException(status_code=500, detail='Модел тапшырманы аткарганы жетишкен жок')

    except OutputParserException:
        raise HTTPException(status_code=500, detail='Моделдин жообу схемага туура келбейт')

    return result.tasks


@meeting_router.post('/check_tasks/', response_model=MeetingTaskReportSchema)
async def check_tasks(tasks: List[MeetingTaskSchema]):
    # без нейросети: обычный подсчёт
    checks = []
    without_assignee = 0
    without_deadline = 0

    for number, task in enumerate(tasks, start=1):
        missing = []

        if not (task.assignee and task.assignee.strip()):
            missing.append('assignee')
            without_assignee += 1

        if not (task.deadline_text and task.deadline_text.strip()):
            missing.append('deadline_text')
            without_deadline += 1

        checks.append(MeetingTaskCheckSchema(
            task_number=number,
            needs_clarification=bool(missing),
            missing_fields=missing,
        ))

    complete = sum(1 for check in checks if not check.needs_clarification)

    return MeetingTaskReportSchema(
        stats=MeetingTaskStatsSchema(
            total_tasks=len(tasks),
            complete_tasks=complete,
            without_assignee=without_assignee,
            without_deadline=without_deadline,
        ),
        checks=checks,
    )


@meeting_router.post('/todos/plan_create/', response_model=TodoPlanOutSchema)
async def plan_create(plan: TodoPlanInputSchema):
    goal = plan.goal.strip()

    if not goal:
        raise HTTPException(status_code=422, detail='Маалымат туура эмес формата берилип жатат')

    try:
        result = await asyncio.wait_for(
            plan_chain.ainvoke({
                "goal": goal,
                "constraints": (plan.constraints or 'нет').strip(),
                "count_tasks": plan.count_tasks,
            }),
            timeout=120
        )
    except TimeoutError:
        raise HTTPException(status_code=500, detail='Модел тапшырманы аткарганы жетишкен жок')

    except OutputParserException:
        raise HTTPException(status_code=500, detail='Моделдин жообу схемага туура келбейт')

    # модель может ошибиться в числе задач и нумерации, поэтому выравниваем сами
    result.tasks = result.tasks[:plan.count_tasks]
    for number, task in enumerate(result.tasks, start=1):
        task.task_number = number
        task.status = 'todo'
    result.plan_status = 'draft'

    return result