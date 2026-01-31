from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============ 基础 CRUD Schemas ============

class TaskCreate(BaseModel):
    """创建任务请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """更新任务请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    tags: Optional[List[str]]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskResponse]
    total: int


# ============ AI 功能 Schemas ============

class NaturalLanguageInput(BaseModel):
    """自然语言输入"""
    text: str = Field(..., min_length=1, description="自然语言描述的任务")


class ParsedTask(BaseModel):
    """解析后的任务"""
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: List[str] = []
    due_date: Optional[str] = None  # ISO format string


class TagSuggestionRequest(BaseModel):
    """标签建议请求"""
    title: str
    description: Optional[str] = None


class TagSuggestionResponse(BaseModel):
    """标签建议响应"""
    suggested_tags: List[str]


class TaskBreakdownRequest(BaseModel):
    """任务分解请求"""
    task_description: str = Field(..., min_length=1)


class TaskBreakdownResponse(BaseModel):
    """任务分解响应"""
    original_task: str
    subtasks: List[str]


class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SemanticSearchResponse(BaseModel):
    """语义搜索响应"""
    query: str
    results: List[TaskResponse]


class PriorityRecommendRequest(BaseModel):
    """优先级推荐请求"""
    title: str
    description: Optional[str] = None


class PriorityRecommendResponse(BaseModel):
    """优先级推荐响应"""
    recommended_priority: TaskPriority
    reasoning: str
