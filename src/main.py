from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.database.db import init_db
from src.routes import tasks, ai

# 创建 FastAPI 应用
app = FastAPI(
    title="AI Task Manager",
    description="智能任务管理系统 - AI/LLM Developer Track",
    version="1.0.0"
)

# 静态文件服务
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tasks.router)
app.include_router(ai.router)


@app.on_event("startup")
def startup():
    """应用启动时初始化数据库"""
    init_db()


@app.get("/", tags=["Health"])
def root():
    """返回前端页面"""
    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, headers={"Cache-Control": "no-store"})
    return {"status": "healthy", "message": "AI Task Manager is running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "AI Task Manager is running"}


@app.get("/api/health", tags=["Health"])
def api_health():
    """API 健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": [
            "Task CRUD",
            "Natural Language Parsing",
            "Tag Suggestion",
            "Task Breakdown",
            "Semantic Search",
            "Priority Recommendation"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
