# AI 提供商配置说明

## 支持的 AI 提供商

系统现在同时支持 **OpenAI** 和 **Google AI (Gemini)**，并支持自动降级策略。

## 配置方式

在 `.env` 文件中配置：

```env
OPENAI_API_KEY=your-openai-key
GOOGLE_AI_API_KEY=your-google-ai-key
AI_PROVIDER=auto
```

### AI_PROVIDER 选项

- `auto` (推荐): 自动模式
  - 优先使用 OpenAI
  - 如果 OpenAI 失败（配额用完、网络错误等），自动切换到 Google AI
  - 如果所有提供商都失败，使用降级方案（基于关键词的简单规则）

- `openai`: 仅使用 OpenAI
  - 如果 OpenAI 失败，使用降级方案

- `google`: 仅使用 Google AI
  - 如果 Google AI 失败，使用降级方案

## 工作原理

### 自动降级策略

1. **第一优先级**: 根据 `AI_PROVIDER` 配置选择提供商
2. **自动切换**: 如果主提供商失败，自动尝试备用提供商
3. **降级方案**: 如果所有 AI 提供商都失败，使用基于关键词的简单规则

### 示例流程

```
用户请求 → 尝试 OpenAI → 失败（配额用完）
         → 自动切换到 Google AI → 成功 ✅
```

## 功能支持

所有 AI 功能都支持多提供商：

- ✅ 自然语言解析 (`parse_natural_language`)
- ✅ 标签建议 (`suggest_tags`)
- ✅ 任务分解 (`breakdown_task`)
- ✅ 优先级推荐 (`recommend_priority`)

## 日志

系统会记录使用的提供商：

```
INFO: 使用 OpenAIProvider 成功执行 parse_natural_language
WARNING: OpenAIProvider 执行 parse_natural_language 失败: 429 insufficient_quota
INFO: 使用 GoogleAIProvider 成功执行 parse_natural_language
```

## 注意事项

1. **API Key 配置**: 确保至少配置一个有效的 API Key
2. **配额管理**: 如果 OpenAI 配额用完，系统会自动使用 Google AI
3. **降级方案**: 即使所有 AI 提供商都失败，系统仍能工作（使用简单规则）

## 测试

测试 AI 服务是否正常工作：

```bash
python -c "from src.services.ai_service import get_ai_service; s = get_ai_service(); print(f'可用提供商: {len(s.providers)}')"
```
