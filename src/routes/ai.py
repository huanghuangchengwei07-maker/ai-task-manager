from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.models.schemas import (
    NaturalLanguageInput, ParsedTask,
    TagSuggestionRequest, TagSuggestionResponse,
    TaskBreakdownRequest, TaskBreakdownResponse,
    SemanticSearchRequest, SemanticSearchResponse,
    PriorityRecommendRequest, PriorityRecommendResponse,
    TaskCreate, TaskResponse
)
from src.services.ai_service import get_ai_service
from src.services.vector_service import get_vector_service
from src.services.task_service import TaskService, _task_to_dict

router = APIRouter(prefix="/api/ai", tags=["AI Features"])


@router.post("/parse", response_model=ParsedTask)
def parse_natural_language(input_data: NaturalLanguageInput):
    """
    解析自然语言任务描述
    
    示例输入: "明天下午3点提醒我开会，很重要"
    """
    try:
        ai_service = get_ai_service()
        result = ai_service.parse_natural_language(input_data.text)
        return result
    except Exception as e:
        from fastapi import HTTPException
        error_msg = str(e)
        # 如果是配额错误，返回更友好的消息
        if "quota" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="OpenAI API 配额已用完，请检查账户余额或稍后重试。当前返回默认解析结果。"
            )
        raise HTTPException(status_code=500, detail=f"解析失败: {error_msg}")


@router.post("/parse-and-create", response_model=TaskResponse)
def parse_and_create_task(
    input_data: NaturalLanguageInput,
    db: Session = Depends(get_db)
):
    """
    解析自然语言并直接创建任务
    """
    ai_service = get_ai_service()
    parsed = ai_service.parse_natural_language(input_data.text)
    
    # 处理 due_date 字符串转 datetime
    due_date = None
    if parsed.get("due_date"):
        from datetime import datetime
        try:
            due_date = datetime.fromisoformat(parsed["due_date"].replace('Z', '+00:00'))
        except:
            pass
    
    # 如果没有标签，自动生成
    tags = parsed.get("tags", [])
    if not tags or len(tags) == 0:
        try:
            tags = ai_service.suggest_tags(parsed.get("title"), parsed.get("description"))
        except:
            # 如果生成标签失败，使用降级方案
            tags = []
    
    # 创建任务
    task_data = TaskCreate(
        title=parsed.get("title"),
        description=parsed.get("description"),
        priority=parsed.get("priority", "medium"),
        tags=tags,
        due_date=due_date
    )
    
    service = TaskService(db)
    task = service.create(task_data)
    return _task_to_dict(task)


@router.post("/suggest-tags", response_model=TagSuggestionResponse)
def suggest_tags(request: TagSuggestionRequest):
    """
    根据任务内容建议标签
    """
    try:
        ai_service = get_ai_service()
        tags = ai_service.suggest_tags(request.title, request.description)
        return {"suggested_tags": tags}
    except Exception as e:
        from fastapi import HTTPException
        error_msg = str(e)
        # 如果是配额错误，返回降级结果而不是错误
        if "quota" in error_msg.lower() or "429" in error_msg:
            # 使用降级方案
            ai_service = get_ai_service()
            tags = ai_service.suggest_tags(request.title, request.description)
            return {"suggested_tags": tags}
        raise HTTPException(status_code=500, detail=f"标签建议失败: {error_msg}")


@router.post("/breakdown", response_model=TaskBreakdownResponse)
def breakdown_task(request: TaskBreakdownRequest):
    """
    将复杂任务分解为子任务
    
    示例输入: "开发一个用户登录功能"
    """
    try:
        ai_service = get_ai_service()
        subtasks = ai_service.breakdown_task(request.task_description)
        return {
            "original_task": request.task_description,
            "subtasks": subtasks
        }
    except Exception as e:
        from fastapi import HTTPException
        error_msg = str(e)
        # 如果是配额错误，返回降级结果而不是错误
        if "quota" in error_msg.lower() or "429" in error_msg:
            # 使用降级方案
            ai_service = get_ai_service()
            subtasks = ai_service.breakdown_task(request.task_description)
            return {
                "original_task": request.task_description,
                "subtasks": subtasks
            }
        raise HTTPException(status_code=500, detail=f"任务分解失败: {error_msg}")


@router.post("/search", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db)
):
    """
    语义搜索任务（基于向量相似度）
    
    示例: 搜索 "购物" 会找到 "去超市买菜" 等语义相关任务
    """
    vector_service = get_vector_service()
    results = vector_service.search(request.query, request.top_k)
    
    if not results:
        return {"query": request.query, "results": []}
    
    # 获取任务详情
    task_ids = [r[0] for r in results]
    service = TaskService(db)
    tasks = service.get_by_ids(task_ids)
    
    # 按搜索结果顺序排序
    task_map = {t.id: t for t in tasks}
    ordered_tasks = [task_map[tid] for tid in task_ids if tid in task_map]
    
    return {
        "query": request.query,
        "results": [_task_to_dict(t) for t in ordered_tasks]
    }


@router.post("/recommend-priority", response_model=PriorityRecommendResponse)
def recommend_priority(request: PriorityRecommendRequest):
    """
    根据任务内容推荐优先级
    """
    try:
        ai_service = get_ai_service()
        priority, reasoning = ai_service.recommend_priority(
            request.title,
            request.description
        )
        return {
            "recommended_priority": priority,
            "reasoning": reasoning
        }
    except Exception as e:
        from fastapi import HTTPException
        error_msg = str(e)
        # 如果是配额错误，返回降级结果而不是错误
        if "quota" in error_msg.lower() or "429" in error_msg:
            # 使用降级方案
            ai_service = get_ai_service()
            priority, reasoning = ai_service.recommend_priority(
                request.title,
                request.description
            )
            return {
                "recommended_priority": priority,
                "reasoning": reasoning
            }
        raise HTTPException(status_code=500, detail=f"优先级推荐失败: {error_msg}")
