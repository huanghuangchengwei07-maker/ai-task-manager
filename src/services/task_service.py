from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from src.models.task import Task, TaskStatus, TaskPriority
from src.models.schemas import TaskCreate, TaskUpdate
from src.services.vector_service import get_vector_service
from src.services.ai_service import get_ai_service


class TaskService:
    """任务 CRUD 服务"""
    
    def __init__(self, db: Session):
        self.db = db
        # 延迟初始化向量服务，避免启动时失败
        self._vector_service = None
    
    @property
    def vector_service(self):
        """延迟加载向量服务"""
        if self._vector_service is None:
            try:
                self._vector_service = get_vector_service()
            except Exception as e:
                print(f"警告: 向量服务初始化失败: {e}")
                # 返回一个空对象，避免后续调用失败
                class DummyVectorService:
                    def add_task(self, *args, **kwargs): pass
                    def update_task(self, *args, **kwargs): pass
                    def delete_task(self, *args, **kwargs): pass
                self._vector_service = DummyVectorService()
        return self._vector_service
    
    def create(self, task_data: TaskCreate) -> Task:
        """创建任务"""
        # 将 tags 列表转为 JSON 字符串
        tags_json = json.dumps(task_data.tags) if task_data.tags else None
        
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            tags=tags_json,
            due_date=task_data.due_date
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # 添加到向量数据库（如果失败不影响主流程）
        try:
            self.vector_service.add_task(
                task.id,
                task.title,
                task.description
            )
        except Exception as e:
            # 向量服务失败不影响任务创建
            print(f"警告: 向量数据库添加失败: {e}")
        
        return task
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据 ID 获取任务"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def get_all(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple:
        """获取任务列表，支持过滤和分页"""
        query = self.db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        
        total = query.count()
        tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
        
        return tasks, total
    
    def update(self, task_id: str, task_data: TaskUpdate) -> Optional[Task]:
        """更新任务"""
        task = self.get_by_id(task_id)
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        title_changed = "title" in update_data and update_data["title"] != task.title
        
        # 处理 tags
        if 'tags' in update_data:
            update_data['tags'] = json.dumps(update_data['tags']) if update_data['tags'] else None
        elif title_changed:
            # 标题变化但未传 tags 时，自动更新 tags
            try:
                ai_service = get_ai_service()
                suggested_tags = ai_service.suggest_tags(
                    update_data.get("title", task.title),
                    update_data.get("description", task.description)
                )
                update_data['tags'] = json.dumps(suggested_tags) if suggested_tags else None
            except Exception as e:
                print(f"警告: 标签自动更新失败: {e}")
        
        for key, value in update_data.items():
            setattr(task, key, value)
        
        # 确保更新时间记录
        task.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task)
        
        # 更新向量数据库（如果失败不影响主流程）
        try:
            self.vector_service.update_task(
                task.id,
                task.title,
                task.description
            )
        except Exception as e:
            print(f"警告: 向量数据库更新失败: {e}")
        
        return task
    
    def delete(self, task_id: str) -> bool:
        """删除任务"""
        task = self.get_by_id(task_id)
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        
        # 从向量数据库删除（如果失败不影响主流程）
        try:
            self.vector_service.delete_task(task_id)
        except Exception as e:
            print(f"警告: 向量数据库删除失败: {e}")
        
        return True
    
    def get_by_ids(self, task_ids: List[str]) -> List[Task]:
        """根据 ID 列表获取任务"""
        return self.db.query(Task).filter(Task.id.in_(task_ids)).all()


def _task_to_dict(task: Task) -> dict:
    """将 Task 模型转为字典，处理 tags"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "tags": json.loads(task.tags) if task.tags else None,
        "due_date": task.due_date,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }
