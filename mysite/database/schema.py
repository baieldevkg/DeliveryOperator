from typing import List, Optional
from pydantic import BaseModel, Field


# analyze
class MeetingTextInputSchema(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class MeetingTaskSchema(BaseModel):
    title: str
    assignee: Optional[str] = None
    deadline_text: Optional[str] = None


class MeetingTaskListSchema(BaseModel):
    tasks: List[MeetingTaskSchema]


# /check_tasks
class MeetingTaskStatsSchema(BaseModel):
    total_tasks: int
    complete_tasks: int
    without_assignee: int
    without_deadline: int


class MeetingTaskCheckSchema(BaseModel):
    task_number: int
    needs_clarification: bool
    missing_fields: List[str]


class MeetingTaskReportSchema(BaseModel):
    stats: MeetingTaskStatsSchema
    checks: List[MeetingTaskCheckSchema]


# plan_create
class TodoPlanInputSchema(BaseModel):
    goal: str = Field(min_length=1, max_length=1000)
    constraints: Optional[str] = None
    count_tasks: int = Field(default=3, ge=1, le=10)


class TodoPlanItemSchema(BaseModel):
    task_number: int
    title: str
    details: str
    priority: int
    status: str


class TodoPlanOutSchema(BaseModel):
    plan_status: str
    tasks: List[TodoPlanItemSchema]