#!/usr/bin/env python3
"""
简单的 API 测试脚本
用于测试任务管理系统的 API 接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("=" * 50)
    print("测试健康检查...")
    response = requests.get(f"{BASE_URL}/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    return response.status_code == 200

def test_parse_natural_language():
    """测试自然语言解析"""
    print("\n" + "=" * 50)
    print("测试自然语言解析...")
    data = {"text": "明天下午3点提醒我和老板开会，很重要"}
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/parse",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        print(f"请求: {data}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_create_task():
    """测试创建任务"""
    print("\n" + "=" * 50)
    print("测试创建任务...")
    data = {
        "title": "测试任务",
        "description": "这是一个测试任务",
        "priority": "high",
        "tags": ["测试", "工作"]
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/tasks",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        print(f"请求: {data}")
        if response.status_code == 201:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.json().get("id")
        else:
            print(f"错误响应: {response.text}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_list_tasks():
    """测试获取任务列表"""
    print("\n" + "=" * 50)
    print("测试获取任务列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks", timeout=30)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"总任务数: {result.get('total', 0)}")
            print(f"任务列表: {json.dumps(result.get('tasks', [])[:3], indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_suggest_tags():
    """测试标签建议"""
    print("\n" + "=" * 50)
    print("测试标签建议...")
    data = {
        "title": "完成项目报告",
        "description": "需要在下周之前完成项目进度报告"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/suggest-tags",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        print(f"请求: {data}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_breakdown_task():
    """测试任务分解"""
    print("\n" + "=" * 50)
    print("测试任务分解...")
    data = {
        "task_description": "开发一个用户登录功能"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/breakdown",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        print(f"请求: {data}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 AI 任务管理系统 API")
    print("=" * 50)
    
    try:
        # 测试健康检查
        if not test_health():
            print("\n❌ 健康检查失败，请确保服务器正在运行！")
            print("启动服务器: python -m src.main")
            return
        
        # 测试自然语言解析
        test_parse_natural_language()
        
        # 测试创建任务
        task_id = test_create_task()
        
        # 测试获取任务列表
        test_list_tasks()
        
        # 测试标签建议
        test_suggest_tags()
        
        # 测试任务分解
        test_breakdown_task()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成！")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器！")
        print("请确保服务器正在运行：")
        print("  cd /home/huang-chengwei/workplace/task-ai-manager")
        print("  source venv/bin/activate")
        print("  python -m src.main")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
