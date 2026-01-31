"""AI 提供商抽象层 - 支持 OpenAI 和 Google AI"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import json
import re
import logging

from src.models.schemas import TaskPriority

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """AI 提供商抽象基类"""
    
    @abstractmethod
    def parse_natural_language(self, text: str) -> dict:
        """解析自然语言任务描述"""
        pass
    
    @abstractmethod
    def suggest_tags(self, title: str, description: Optional[str] = None) -> List[str]:
        """建议标签"""
        pass
    
    @abstractmethod
    def breakdown_task(self, task_description: str) -> List[str]:
        """分解任务"""
        pass
    
    @abstractmethod
    def recommend_priority(self, title: str, description: Optional[str] = None) -> Tuple[TaskPriority, str]:
        """推荐优先级"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI 提供商"""
    
    def __init__(self, api_key: str):
        try:
            import openai
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4o-mini"
            self.available = True
        except Exception as e:
            logger.error(f"OpenAI 初始化失败: {e}")
            self.available = False
    
    def parse_natural_language(self, text: str) -> dict:
        """使用 OpenAI Function Calling 解析自然语言"""
        if not self.available:
            raise Exception("OpenAI 不可用")
        
        from datetime import datetime
        
        try:
            tools = [{
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "从自然语言描述中提取任务信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "任务标题"},
                            "description": {"type": "string", "description": "任务描述"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "优先级"},
                            "due_date": {"type": "string", "description": "截止日期，ISO 8601格式"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "标签"}
                        },
                        "required": ["title"]
                    }
                }
            }]
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""你是一个任务解析助手。从用户的自然语言中提取任务信息。

当前日期是: {today}

日期解析规则:
- "今天" = 当天
- "明天" = 当天 + 1天
- "后天" = 当天 + 2天
- "下周一" = 下一个周一
- "3点" = 15:00 (默认下午)
- "上午9点" = 09:00

优先级判断:
- 包含"紧急"、"重要"、"高优先级"、"尽快" → high
- 包含"低优先级"、"不急"、"有空再" → low
- 其他情况 → medium

请准确提取信息，不要添加用户没有提到的内容。"""
                    },
                    {"role": "user", "content": text}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "create_task"}}
            )
            
            if not response.choices[0].message.tool_calls:
                return {"title": text, "description": None, "priority": "medium", "tags": []}
            
            tool_call = response.choices[0].message.tool_calls[0]
            return json.loads(tool_call.function.arguments)
        except Exception as e:
            logger.error(f"OpenAI 解析失败: {e}")
            raise
    
    def suggest_tags(self, title: str, description: Optional[str] = None) -> List[str]:
        """使用 OpenAI 建议标签"""
        if not self.available:
            raise Exception("OpenAI 不可用")
        
        try:
            content = f"{title}. {description}" if description else title
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个任务分类助手。根据任务内容建议合适的标签。

规则:
1. 返回 2-4 个最相关的标签
2. 标签要简洁（1-4个字）
3. 使用常见的分类，如：工作、学习、生活、购物、健康、社交、财务、家庭等
4. 只返回 JSON 数组格式，如 ["工作", "会议"]

不要添加任何其他解释。"""
                    },
                    {"role": "user", "content": f"任务内容: {content}"}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            try:
                tags = json.loads(result_text)
                return tags if isinstance(tags, list) else []
            except:
                tags = re.findall(r'"([^"]+)"', result_text)
                return tags[:4]
        except Exception as e:
            logger.error(f"OpenAI 标签建议失败: {e}")
            raise
    
    def breakdown_task(self, task_description: str) -> List[str]:
        """使用 OpenAI 分解任务"""
        if not self.available:
            raise Exception("OpenAI 不可用")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个任务规划助手。将复杂任务分解为可执行的子任务。

规则:
1. 每个子任务应该是具体、可操作的
2. 子任务数量控制在 3-7 个
3. 按执行顺序排列
4. 只返回 JSON 数组格式，如 ["子任务1", "子任务2", ...]

不要添加任何其他解释。"""
                    },
                    {"role": "user", "content": f"请分解这个任务: {task_description}"}
                ],
                temperature=0.5
            )
            
            result_text = response.choices[0].message.content.strip()
            try:
                subtasks = json.loads(result_text)
                return subtasks if isinstance(subtasks, list) else []
            except:
                lines = result_text.split('\n')
                subtasks = [line.strip().lstrip('0123456789.-) ') for line in lines if line.strip()]
                return subtasks[:7]
        except Exception as e:
            logger.error(f"OpenAI 任务分解失败: {e}")
            raise
    
    def recommend_priority(self, title: str, description: Optional[str] = None) -> Tuple[TaskPriority, str]:
        """使用 OpenAI 推荐优先级"""
        if not self.available:
            raise Exception("OpenAI 不可用")
        
        try:
            content = f"{title}. {description}" if description else title
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个任务优先级评估助手。根据任务内容推荐优先级。

评估标准:
- HIGH (高): 紧急且重要、有明确截止日期、影响他人、核心工作任务
- MEDIUM (中): 重要但不紧急、常规工作任务、个人发展
- LOW (低): 不紧急不重要、娱乐休闲、可延期任务

返回 JSON 格式:
{"priority": "low|medium|high", "reasoning": "简短说明理由"}"""
                    },
                    {"role": "user", "content": f"任务: {content}"}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            try:
                result = json.loads(result_text)
                priority = result.get("priority", "medium")
                reasoning = result.get("reasoning", "")
                return (TaskPriority(priority), reasoning)
            except:
                return (TaskPriority.MEDIUM, "无法确定，默认为中优先级")
        except Exception as e:
            logger.error(f"OpenAI 优先级推荐失败: {e}")
            raise


class GoogleAIProvider(AIProvider):
    """Google AI (Gemini) 提供商"""
    
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True
            logger.info("Google AI 初始化成功")
        except Exception as e:
            logger.error(f"Google AI 初始化失败: {e}")
            self.available = False
    
    def parse_natural_language(self, text: str) -> dict:
        """使用 Google AI 解析自然语言"""
        if not self.available:
            raise Exception("Google AI 不可用")
        
        from datetime import datetime
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            prompt = f"""你是一个任务解析助手。从用户的自然语言中提取任务信息。

当前日期是: {today}

日期解析规则:
- "今天" = 当天
- "明天" = 当天 + 1天
- "后天" = 当天 + 2天
- "下周一" = 下一个周一
- "3点" = 15:00 (默认下午)
- "上午9点" = 09:00

优先级判断:
- 包含"紧急"、"重要"、"高优先级"、"尽快" → high
- 包含"低优先级"、"不急"、"有空再" → low
- 其他情况 → medium

请从以下文本中提取任务信息，只返回 JSON 格式，不要添加任何解释：
{text}

返回格式：
{{
  "title": "任务标题",
  "description": "任务描述（可选）",
  "priority": "low|medium|high",
  "due_date": "ISO 8601格式日期（可选）",
  "tags": ["标签1", "标签2"]
}}"""
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # 清理可能的 markdown 代码块
            if result_text.startswith("```"):
                result_text = re.sub(r'```json\s*', '', result_text)
                result_text = re.sub(r'```\s*', '', result_text)
            
            result = json.loads(result_text)
            return result
        except Exception as e:
            logger.error(f"Google AI 解析失败: {e}")
            raise
    
    def suggest_tags(self, title: str, description: Optional[str] = None) -> List[str]:
        """使用 Google AI 建议标签"""
        if not self.available:
            raise Exception("Google AI 不可用")
        
        try:
            content = f"{title}. {description}" if description else title
            
            prompt = f"""你是一个任务分类助手。根据任务内容建议合适的标签。

规则:
1. 返回 2-4 个最相关的标签
2. 标签要简洁（1-4个字）
3. 使用常见的分类，如：工作、学习、生活、购物、健康、社交、财务、家庭等
4. 只返回 JSON 数组格式，如 ["工作", "会议"]

任务内容: {content}

只返回 JSON 数组，不要添加任何解释："""
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```"):
                result_text = re.sub(r'```json\s*', '', result_text)
                result_text = re.sub(r'```\s*', '', result_text)
            
            try:
                tags = json.loads(result_text)
                return tags if isinstance(tags, list) else []
            except:
                tags = re.findall(r'"([^"]+)"', result_text)
                return tags[:4]
        except Exception as e:
            logger.error(f"Google AI 标签建议失败: {e}")
            raise
    
    def breakdown_task(self, task_description: str) -> List[str]:
        """使用 Google AI 分解任务"""
        if not self.available:
            raise Exception("Google AI 不可用")
        
        try:
            prompt = f"""你是一个任务规划助手。将复杂任务分解为可执行的子任务。

规则:
1. 每个子任务应该是具体、可操作的
2. 子任务数量控制在 3-7 个
3. 按执行顺序排列
4. 只返回 JSON 数组格式，如 ["子任务1", "子任务2", ...]

请分解这个任务: {task_description}

只返回 JSON 数组，不要添加任何解释："""
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```"):
                result_text = re.sub(r'```json\s*', '', result_text)
                result_text = re.sub(r'```\s*', '', result_text)
            
            try:
                subtasks = json.loads(result_text)
                return subtasks if isinstance(subtasks, list) else []
            except:
                lines = result_text.split('\n')
                subtasks = [line.strip().lstrip('0123456789.-) ') for line in lines if line.strip()]
                return subtasks[:7]
        except Exception as e:
            logger.error(f"Google AI 任务分解失败: {e}")
            raise
    
    def recommend_priority(self, title: str, description: Optional[str] = None) -> Tuple[TaskPriority, str]:
        """使用 Google AI 推荐优先级"""
        if not self.available:
            raise Exception("Google AI 不可用")
        
        try:
            content = f"{title}. {description}" if description else title
            
            prompt = f"""你是一个任务优先级评估助手。根据任务内容推荐优先级。

评估标准:
- HIGH (高): 紧急且重要、有明确截止日期、影响他人、核心工作任务
- MEDIUM (中): 重要但不紧急、常规工作任务、个人发展
- LOW (低): 不紧急不重要、娱乐休闲、可延期任务

任务: {content}

返回 JSON 格式:
{{
  "priority": "low|medium|high",
  "reasoning": "简短说明理由"
}}

只返回 JSON，不要添加任何解释："""
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```"):
                result_text = re.sub(r'```json\s*', '', result_text)
                result_text = re.sub(r'```\s*', '', result_text)
            
            try:
                result = json.loads(result_text)
                priority = result.get("priority", "medium")
                reasoning = result.get("reasoning", "")
                return (TaskPriority(priority), reasoning)
            except:
                return (TaskPriority.MEDIUM, "无法确定，默认为中优先级")
        except Exception as e:
            logger.error(f"Google AI 优先级推荐失败: {e}")
            raise
