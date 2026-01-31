# 使用指南

## 🚀 快速开始

### 1. 启动服务器

```bash
cd /home/huang-chengwei/workplace/task-ai-manager
source venv/bin/activate
python -m src.main
```

服务器启动后，你会看到类似这样的输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. 访问智能 Web 界面（🌟 最推荐！）

**无需编写 JSON，直接用自然语言创建任务！**

在浏览器中打开：**http://localhost:8000**

你会看到一个美观的 Web 界面，可以：
- ✨ **自然语言创建**：直接输入"明天下午3点提醒我开会，很重要"
- 📝 **手动创建**：如果需要精确控制，也可以手动填写表单
- 📋 **任务列表**：查看所有任务，支持筛选和搜索

**特点：**
- 🎨 现代化 UI 设计
- 💬 自然语言输入，无需 JSON
- ⚡ 实时反馈和加载状态
- 📱 响应式设计，支持移动端

### 3. 使用智能 CLI 工具（命令行用户推荐）

**无需编写 JSON，直接用自然语言创建任务！**

```bash
# 进入项目目录并激活虚拟环境
cd /home/huang-chengwei/workplace/task-ai-manager
source venv/bin/activate

# 启动交互式模式
python cli.py
```

然后直接输入自然语言即可：
```
📝 > 明天下午3点提醒我开会，很重要
✅ 任务创建成功！
📋 任务详情
==================================================
ID:        abc123...
标题:      和老板开会
状态:      待处理
优先级:    高
截止日期:  2026-02-01 15:00:00
标签:      工作, 会议
==================================================

📝 > 下周一之前完成项目报告
✅ 任务创建成功！

📝 > list
ℹ️  共找到 5 个任务，显示前 5 个：
1. ⏳ 🔴 和老板开会 (截止: 2026-02-01 15:00) [工作, 会议] (ID: abc123...)
2. ⏳ 🟡 完成项目报告 (截止: 2026-02-05 23:59) [工作] (ID: def456...)
...
```

**命令行模式示例：**
```bash
# 直接创建任务（自然语言）
python cli.py add "明天下午3点提醒我开会，很重要"

# 列出所有任务
python cli.py list

# 列出已完成的任务
python cli.py list --status completed

# 语义搜索
python cli.py search "会议"

# 任务分解
python cli.py breakdown "开发一个用户登录功能"

# 获取标签建议
python cli.py tags "完成项目报告" --description "需要在下周之前完成"
```

---

## 📖 使用方式

### 方式一：使用 Web 界面（🌟 最推荐！）

**直接在浏览器中使用，无需任何技术知识！**

1. 启动服务器后，访问 **http://localhost:8000**
2. 在"自然语言创建"标签页中，直接输入你的任务描述
3. 点击"创建任务"按钮
4. 系统会自动解析并创建任务

**示例：**
- 输入："明天下午3点提醒我开会，很重要"
- 系统自动提取：标题、时间、优先级、标签等

### 方式二：使用智能 CLI 工具（命令行用户推荐）

**无需编写 JSON，直接用自然语言！** 见上方说明。

### 方式三：使用 Swagger UI（适合查看 API 文档和测试）

1. 打开 http://localhost:8000/docs
2. 点击任意 API 端点展开
3. 点击 "Try it out" 按钮
4. 填写请求参数
5. 点击 "Execute" 执行
6. 查看响应结果

**示例：创建任务**
1. 展开 `POST /api/tasks`
2. 点击 "Try it out"
3. 在请求体中输入：
```json
{
  "title": "完成项目报告",
  "description": "需要在下周之前完成",
  "priority": "high",
  "tags": ["工作", "报告"]
}
```
4. 点击 "Execute"
5. 查看返回的任务信息

---

### 方式二：使用 Python 测试脚本

```bash
# 在另一个终端运行
cd /home/huang-chengwei/workplace/task-ai-manager
source venv/bin/activate
python test_api.py
```

这会自动测试所有功能。

---

### 方式三：使用 curl 命令（如果已安装）

```bash
# 创建任务
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 FastAPI",
    "description": "完成 FastAPI 教程",
    "priority": "medium",
    "tags": ["学习", "技术"]
  }'

# 获取任务列表
curl -X GET "http://localhost:8000/api/tasks"

# 自然语言解析（会使用降级方案）
curl -X POST "http://localhost:8000/api/ai/parse" \
  -H "Content-Type: application/json" \
  -d '{"text": "明天下午3点提醒我开会"}'
```

---

## 🎯 常用操作示例

### 1. 创建任务

**在 Swagger UI 中：**
- 展开 `POST /api/tasks`
- 点击 "Try it out"
- 输入：
```json
{
  "title": "完成代码审查",
  "description": "审查团队成员的 PR",
  "priority": "high",
  "status": "pending",
  "tags": ["工作", "代码审查"]
}
```

### 2. 获取所有任务

**在 Swagger UI 中：**
- 展开 `GET /api/tasks`
- 点击 "Try it out"
- 可以添加查询参数：
  - `status`: pending / in_progress / completed
  - `priority`: low / medium / high
  - `skip`: 跳过数量（分页）
  - `limit`: 返回数量（分页）
- 点击 "Execute"

### 3. 使用自然语言创建任务

**在 Swagger UI 中：**
- 展开 `POST /api/ai/parse-and-create`
- 点击 "Try it out"
- 输入：
```json
{
  "text": "下周一之前完成项目文档，很重要"
}
```
- 点击 "Execute"
- 系统会自动解析并创建任务

### 4. 获取标签建议

**在 Swagger UI 中：**
- 展开 `POST /api/ai/suggest-tags`
- 点击 "Try it out"
- 输入：
```json
{
  "title": "完成项目报告",
  "description": "需要在下周之前完成项目进度报告"
}
```
- 点击 "Execute"
- 查看建议的标签（如果 API 配额用完，会使用降级方案）

### 5. 任务分解

**在 Swagger UI 中：**
- 展开 `POST /api/ai/breakdown`
- 点击 "Try it out"
- 输入：
```json
{
  "task_description": "开发一个用户登录功能"
}
```
- 点击 "Execute"
- 查看分解后的子任务列表

### 6. 更新任务

**在 Swagger UI 中：**
- 先创建一个任务，获取 `id`
- 展开 `PUT /api/tasks/{task_id}`
- 点击 "Try it out"
- 在 `task_id` 参数中输入任务的 ID
- 在请求体中输入要更新的字段：
```json
{
  "status": "in_progress",
  "priority": "high"
}
```
- 点击 "Execute"

### 7. 删除任务

**在 Swagger UI 中：**
- 展开 `DELETE /api/tasks/{task_id}`
- 点击 "Try it out"
- 输入任务的 `id`
- 点击 "Execute"

---

## 💡 使用技巧

### 1. 查看任务 ID
创建任务后，响应中会返回 `id` 字段，复制这个 ID 用于后续的更新/删除操作。

### 2. 过滤任务
在获取任务列表时，可以使用查询参数：
- `?status=completed` - 只获取已完成的任务
- `?priority=high` - 只获取高优先级任务
- `?status=pending&priority=high` - 组合过滤

### 3. 分页
- `?skip=0&limit=10` - 获取前 10 条
- `?skip=10&limit=10` - 获取第 11-20 条

### 4. 语义搜索
即使 API 配额用完，语义搜索功能（需要向量数据库）可能仍然可用，因为它是基于已存储的任务向量。

---

## ⚠️ 注意事项

1. **API 配额**：当前 OpenAI API 配额已用完，AI 功能会使用降级方案
2. **数据持久化**：所有任务数据保存在 `tasks.db` 文件中
3. **向量数据库**：ChromaDB 数据保存在 `chroma_data/` 目录

---

## 🔍 故障排查

### 服务器无法启动
- 检查虚拟环境是否激活：`which python` 应该指向 `venv/bin/python`
- 检查端口 8000 是否被占用：`lsof -i:8000`

### API 返回 500 错误
- 查看服务器控制台的错误日志
- 检查 `.env` 文件中的 API Key 是否正确

### 找不到模块
- 确保已安装所有依赖：`pip install -r requirements.txt`
- 确保在虚拟环境中：`source venv/bin/activate`

---

## 📚 更多信息

- 查看 `README.md` 了解项目详情
- 查看 `STATUS.md` 了解当前状态
- 查看 `IMPLEMENTATION_GUIDE.md` 了解实现细节
