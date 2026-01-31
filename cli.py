#!/usr/bin/env python3
"""
智能任务管理 CLI 工具
支持自然语言输入，无需手动编写 JSON
"""

import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Optional

BASE_URL = "http://localhost:8000"


def print_success(message):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误消息"""
    print(f"❌ {message}")


def print_info(message):
    """打印信息"""
    print(f"ℹ️  {message}")


def create_task_natural(text: str) -> dict:
    """
    使用自然语言创建任务
    示例: "明天下午3点提醒我开会，很重要"
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/parse-and-create",
            json={"text": text},
            timeout=10
        )
        response.raise_for_status()
        task = response.json()
        print_success(f"任务创建成功！")
        print_task(task)
        return task
    except requests.exceptions.RequestException as e:
        print_error(f"创建任务失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print_error(f"错误详情: {error_detail.get('detail', '未知错误')}")
            except:
                print_error(f"错误响应: {e.response.text}")
        return None


def create_task_manual(title: str, description: Optional[str] = None,
                      priority: str = "medium", tags: Optional[list] = None) -> dict:
    """手动创建任务（传统方式）"""
    try:
        data = {
            "title": title,
            "priority": priority,
        }
        if description:
            data["description"] = description
        if tags:
            data["tags"] = tags
        
        response = requests.post(
            f"{BASE_URL}/api/tasks",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        task = response.json()
        print_success(f"任务创建成功！")
        print_task(task)
        return task
    except requests.exceptions.RequestException as e:
        print_error(f"创建任务失败: {e}")
        return None


def list_tasks(status: Optional[str] = None, priority: Optional[str] = None,
               limit: int = 20) -> list:
    """获取任务列表"""
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        
        response = requests.get(f"{BASE_URL}/api/tasks", params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        tasks = result.get("tasks", [])
        total = result.get("total", 0)
        
        print_info(f"共找到 {total} 个任务，显示前 {len(tasks)} 个：\n")
        
        if not tasks:
            print("📝 暂无任务")
            return []
        
        for i, task in enumerate(tasks, 1):
            print(f"{i}. ", end="")
            print_task(task, compact=True)
            print()
        
        return tasks
    except requests.exceptions.RequestException as e:
        print_error(f"获取任务列表失败: {e}")
        return []


def get_task(task_id: str) -> Optional[dict]:
    """获取单个任务详情"""
    try:
        response = requests.get(f"{BASE_URL}/api/tasks/{task_id}", timeout=10)
        response.raise_for_status()
        task = response.json()
        print_task(task)
        return task
    except requests.exceptions.RequestException as e:
        print_error(f"获取任务失败: {e}")
        return None


def update_task(task_id: str, **kwargs) -> Optional[dict]:
    """更新任务"""
    try:
        # 只发送非空字段
        data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not data:
            print_error("没有提供要更新的字段")
            return None
        
        response = requests.put(
            f"{BASE_URL}/api/tasks/{task_id}",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        task = response.json()
        print_success("任务更新成功！")
        print_task(task)
        return task
    except requests.exceptions.RequestException as e:
        print_error(f"更新任务失败: {e}")
        return None


def delete_task(task_id: str) -> bool:
    """删除任务"""
    try:
        response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}", timeout=10)
        response.raise_for_status()
        print_success(f"任务 {task_id} 已删除")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"删除任务失败: {e}")
        return False


def suggest_tags(title: str, description: Optional[str] = None) -> list:
    """获取标签建议"""
    try:
        data = {"title": title}
        if description:
            data["description"] = description
        
        response = requests.post(
            f"{BASE_URL}/api/ai/suggest-tags",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        tags = result.get("suggested_tags", [])
        
        if tags:
            print_success(f"建议的标签: {', '.join(tags)}")
        else:
            print_info("未找到建议的标签")
        
        return tags
    except requests.exceptions.RequestException as e:
        print_error(f"获取标签建议失败: {e}")
        return []


def breakdown_task(description: str) -> list:
    """任务分解"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/breakdown",
            json={"task_description": description},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        subtasks = result.get("subtasks", [])
        
        print_success("任务分解结果：")
        for i, subtask in enumerate(subtasks, 1):
            print(f"  {i}. {subtask}")
        
        return subtasks
    except requests.exceptions.RequestException as e:
        print_error(f"任务分解失败: {e}")
        return []


def search_tasks(query: str, top_k: int = 5) -> list:
    """语义搜索任务"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/search",
            json={"query": query, "top_k": top_k},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        tasks = result.get("results", [])
        
        print_info(f"找到 {len(tasks)} 个相关任务：\n")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. ", end="")
            print_task(task, compact=True)
            print()
        
        return tasks
    except requests.exceptions.RequestException as e:
        print_error(f"搜索失败: {e}")
        return []


def print_task(task: dict, compact: bool = False):
    """打印任务信息"""
    if compact:
        status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(task.get("status"), "📝")
        priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(task.get("priority"), "⚪")
        
        print(f"{status_emoji} {priority_emoji} {task.get('title', 'N/A')}", end="")
        if task.get("due_date"):
            due_date = datetime.fromisoformat(task["due_date"].replace('Z', '+00:00'))
            print(f" (截止: {due_date.strftime('%Y-%m-%d %H:%M')})", end="")
        if task.get("tags"):
            print(f" [{', '.join(task['tags'])}]", end="")
        print(f" (ID: {task.get('id', 'N/A')[:8]}...)")
    else:
        print("\n" + "="*50)
        print(f"📋 任务详情")
        print("="*50)
        print(f"ID:        {task.get('id', 'N/A')}")
        print(f"标题:      {task.get('title', 'N/A')}")
        if task.get('description'):
            print(f"描述:      {task.get('description')}")
        
        status_map = {"pending": "待处理", "in_progress": "进行中", "completed": "已完成"}
        priority_map = {"low": "低", "medium": "中", "high": "高"}
        
        print(f"状态:      {status_map.get(task.get('status'), task.get('status', 'N/A'))}")
        print(f"优先级:    {priority_map.get(task.get('priority'), task.get('priority', 'N/A'))}")
        
        if task.get('tags'):
            print(f"标签:      {', '.join(task['tags'])}")
        
        if task.get('due_date'):
            due_date = datetime.fromisoformat(task["due_date"].replace('Z', '+00:00'))
            print(f"截止日期:  {due_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        created_at = datetime.fromisoformat(task["created_at"].replace('Z', '+00:00'))
        print(f"创建时间:  {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)


def interactive_mode():
    """交互式模式"""
    print("\n" + "="*60)
    print("🤖 智能任务管理系统 - 交互模式")
    print("="*60)
    print("\n提示：直接输入自然语言即可创建任务！")
    print("例如：'明天下午3点提醒我开会，很重要'")
    print("输入 'help' 查看所有命令，输入 'exit' 退出\n")
    
    while True:
        try:
            user_input = input("📝 > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 再见！")
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            if user_input.lower() == 'list':
                list_tasks()
                continue
            
            if user_input.lower().startswith('list '):
                # 解析过滤条件，如 "list status=completed"
                parts = user_input[5:].split()
                status = None
                priority = None
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        if key == 'status':
                            status = value
                        elif key == 'priority':
                            priority = value
                list_tasks(status=status, priority=priority)
                continue
            
            if user_input.lower().startswith('get '):
                task_id = user_input[4:].strip()
                get_task(task_id)
                continue
            
            if user_input.lower().startswith('delete '):
                task_id = user_input[7:].strip()
                confirm = input(f"确定要删除任务 {task_id} 吗？(y/N): ")
                if confirm.lower() == 'y':
                    delete_task(task_id)
                continue
            
            if user_input.lower().startswith('update '):
                # 格式: update <task_id> status=completed priority=high
                parts = user_input[7:].strip().split()
                if not parts:
                    print_error("请提供任务 ID 和更新字段")
                    continue
                task_id = parts[0]
                updates = {}
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        updates[key] = value
                if updates:
                    update_task(task_id, **updates)
                else:
                    print_error("请提供要更新的字段，格式: update <id> status=completed")
                continue
            
            if user_input.lower().startswith('search '):
                query = user_input[7:].strip()
                search_tasks(query)
                continue
            
            if user_input.lower().startswith('breakdown '):
                description = user_input[10:].strip()
                breakdown_task(description)
                continue
            
            if user_input.lower().startswith('tags '):
                # 格式: tags "标题" "描述"
                parts = user_input[5:].strip().split('"')
                title = parts[1] if len(parts) > 1 else ""
                description = parts[3] if len(parts) > 3 else None
                suggest_tags(title, description)
                continue
            
            # 默认：当作自然语言任务创建
            create_task_natural(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print_error(f"发生错误: {e}")


def print_help():
    """打印帮助信息"""
    print("\n" + "="*60)
    print("📖 命令帮助")
    print("="*60)
    print("\n【自然语言创建任务】")
    print("  直接输入自然语言即可，例如：")
    print("    > 明天下午3点提醒我开会，很重要")
    print("    > 下周一之前完成项目报告")
    print("    > 记得买牛奶和面包")
    print("\n【查看任务】")
    print("  list                    - 列出所有任务")
    print("  list status=completed    - 列出已完成的任务")
    print("  list priority=high      - 列出高优先级任务")
    print("  get <task_id>            - 查看任务详情")
    print("\n【管理任务】")
    print("  update <id> status=completed    - 更新任务状态")
    print("  update <id> priority=high       - 更新任务优先级")
    print("  delete <task_id>                - 删除任务")
    print("\n【AI 功能】")
    print("  search <关键词>         - 语义搜索任务")
    print("  breakdown <任务描述>    - 分解复杂任务")
    print("  tags \"标题\" \"描述\"    - 获取标签建议")
    print("\n【其他】")
    print("  help                    - 显示此帮助")
    print("  exit / quit             - 退出程序")
    print("="*60 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能任务管理 CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 交互式模式（推荐）
  python cli.py
  
  # 直接创建任务
  python cli.py add "明天下午3点提醒我开会，很重要"
  
  # 列出任务
  python cli.py list
  
  # 搜索任务
  python cli.py search "会议"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加任务
    add_parser = subparsers.add_parser('add', help='创建任务（自然语言）')
    add_parser.add_argument('text', help='任务描述（自然语言）')
    
    # 列出任务
    list_parser = subparsers.add_parser('list', help='列出任务')
    list_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed'], help='按状态过滤')
    list_parser.add_argument('--priority', choices=['low', 'medium', 'high'], help='按优先级过滤')
    list_parser.add_argument('--limit', type=int, default=20, help='返回数量限制')
    
    # 获取任务
    get_parser = subparsers.add_parser('get', help='获取任务详情')
    get_parser.add_argument('task_id', help='任务 ID')
    
    # 更新任务
    update_parser = subparsers.add_parser('update', help='更新任务')
    update_parser.add_argument('task_id', help='任务 ID')
    update_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed'], help='更新状态')
    update_parser.add_argument('--priority', choices=['low', 'medium', 'high'], help='更新优先级')
    update_parser.add_argument('--title', help='更新标题')
    update_parser.add_argument('--description', help='更新描述')
    
    # 删除任务
    delete_parser = subparsers.add_parser('delete', help='删除任务')
    delete_parser.add_argument('task_id', help='任务 ID')
    
    # 搜索
    search_parser = subparsers.add_parser('search', help='语义搜索任务')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('--top-k', type=int, default=5, help='返回数量')
    
    # 分解任务
    breakdown_parser = subparsers.add_parser('breakdown', help='分解任务')
    breakdown_parser.add_argument('description', help='任务描述')
    
    # 标签建议
    tags_parser = subparsers.add_parser('tags', help='获取标签建议')
    tags_parser.add_argument('title', help='任务标题')
    tags_parser.add_argument('--description', help='任务描述')
    
    args = parser.parse_args()
    
    # 如果没有提供命令，进入交互模式
    if not args.command:
        interactive_mode()
        return
    
    # 执行对应命令
    if args.command == 'add':
        create_task_natural(args.text)
    elif args.command == 'list':
        list_tasks(status=args.status, priority=args.priority, limit=args.limit)
    elif args.command == 'get':
        get_task(args.task_id)
    elif args.command == 'update':
        updates = {}
        if args.status:
            updates['status'] = args.status
        if args.priority:
            updates['priority'] = args.priority
        if args.title:
            updates['title'] = args.title
        if args.description:
            updates['description'] = args.description
        update_task(args.task_id, **updates)
    elif args.command == 'delete':
        delete_task(args.task_id)
    elif args.command == 'search':
        search_tasks(args.query, top_k=args.top_k)
    elif args.command == 'breakdown':
        breakdown_task(args.description)
    elif args.command == 'tags':
        suggest_tags(args.title, args.description)


if __name__ == "__main__":
    main()
