from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database.db import get_db
from src.models.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskStatus, TaskPriority
)
from src.services.task_service import TaskService, _task_to_dict

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """创建新任务"""
    try:
        service = TaskService(db)
        task = service.create(task_data)
        return _task_to_dict(task)
    except Exception as e:
        from fastapi import HTTPException
        import traceback
        error_detail = f"创建任务失败: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    try:
        service = TaskService(db)
        tasks, total = service.get_all(status, priority, skip, limit)
        return {
            "tasks": [_task_to_dict(t) for t in tasks],
            "total": total
        }
    except Exception as e:
        from fastapi import HTTPException
        import traceback
        error_detail = f"获取任务列表失败: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """获取单个任务"""
    service = TaskService(db)
    task = service.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_data: TaskUpdate, db: Session = Depends(get_db)):
    """更新任务"""
    service = TaskService(db)
    task = service.update(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """删除任务"""
    service = TaskService(db)
    success = service.delete(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
