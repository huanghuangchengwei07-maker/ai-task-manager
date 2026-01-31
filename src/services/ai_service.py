"""AI/LLM 服务 - 支持多个提供商和自动降级"""
from typing import List, Optional, Tuple
import logging
import re
from datetime import datetime, timedelta

from src.config import get_settings
from src.models.schemas import TaskPriority
from src.services.ai_providers import OpenAIProvider, GoogleAIProvider, AIProvider

settings = get_settings()
logger = logging.getLogger(__name__)


def _get_fallback_tags(title: str, description: Optional[str] = None) -> List[str]:
    """降级方案：基于关键词的标签建议（支持中英文，覆盖常见工作任务）"""
    simple_tags = []
    content = f"{title} {description or ''}".lower()
    
    # Work/Job related (工作相关)
    work_keywords = ['工作', '项目', '报告', '会议', '任务', '项目', '代码', '审查', '开发', '设计',
                     'work', 'project', 'report', 'meeting', 'task', 'code', 'review', 'develop', 'development', 
                     'design', 'implement', 'implementation', 'bug', 'fix', 'feature', 'deploy', 'deployment',
                     'test', 'testing', 'document', 'documentation', 'plan', 'planning', 'analysis']
    if any(word in content for word in work_keywords):
        # 更具体的标签
        if any(word in content for word in ['meeting', '会议', 'conference', 'call']):
            simple_tags.append('Meeting')
        elif any(word in content for word in ['code', '代码', 'programming', 'program', 'coding']):
            simple_tags.append('Code')
        elif any(word in content for word in ['review', '审查', 'check', '检查']):
            simple_tags.append('Review')
        elif any(word in content for word in ['project', '项目']):
            simple_tags.append('Project')
        elif any(word in content for word in ['report', '报告']):
            simple_tags.append('Report')
        else:
            simple_tags.append('Work')
    
    # Learning/Study (学习相关)
    study_keywords = ['学习', '课程', '作业', '考试', '培训', '教程',
                      'learn', 'study', 'course', 'homework', 'exam', 'test', 'training', 'tutorial']
    if any(word in content for word in study_keywords):
        simple_tags.append('Study')
    
    # Shopping (购物相关)
    shopping_keywords = ['购物', '买', '超市', '商店', '采购',
                         'shopping', 'buy', 'purchase', 'shop', 'grocery', 'store']
    if any(word in content for word in shopping_keywords):
        simple_tags.append('Shopping')
    
    # Health (健康相关)
    health_keywords = ['健康', '运动', '锻炼', '医院', '医生', '健身',
                       'health', 'exercise', 'workout', 'hospital', 'doctor', 'fitness', 'gym']
    if any(word in content for word in health_keywords):
        simple_tags.append('Health')
    
    # Personal/Life (个人/生活)
    personal_keywords = ['个人', '生活', '家庭', '朋友', '社交',
                         'personal', 'life', 'family', 'friend', 'social', 'home']
    if any(word in content for word in personal_keywords):
        simple_tags.append('Personal')
    
    # Finance (财务相关)
    finance_keywords = ['财务', '账单', '支付', '银行', '投资',
                        'finance', 'bill', 'payment', 'bank', 'investment', 'money']
    if any(word in content for word in finance_keywords):
        simple_tags.append('Finance')
    
    # Travel (旅行相关)
    travel_keywords = ['旅行', '旅游', '出差', '航班', '酒店',
                       'travel', 'trip', 'flight', 'hotel', 'vacation', 'journey']
    if any(word in content for word in travel_keywords):
        simple_tags.append('Travel')
    
    # Default: if no specific tag found, try to infer from common patterns
    if not simple_tags:
        if 'meeting' in content or '会议' in content:
            simple_tags.append('Meeting')
        elif 'code' in content or '代码' in content:
            simple_tags.append('Code')
        elif 'review' in content or '审查' in content:
            simple_tags.append('Review')
        else:
            simple_tags.append('Work')  # Default to Work for most tasks
    
    return simple_tags[:3] if simple_tags else ['Other']


def _get_fallback_priority(title: str, description: Optional[str] = None) -> Tuple[TaskPriority, str]:
    """降级方案：基于关键词的优先级判断（支持中英文）"""
    content = f"{title} {description or ''}".lower()
    # High priority keywords (Chinese and English)
    high_keywords = ['紧急', '重要', '很重要', '尽快', '立即', '必须', '优先级高', '高优先级',
                     'urgent', 'important', 'critical', 'asap', 'as soon as possible', 'high priority', 'priority high']
    # Low priority keywords (Chinese and English)
    low_keywords = ['不急', '有空', '随意', '休闲', '优先级低', '低优先级',
                    'low priority', 'priority low', 'whenever', 'optional', 'leisure']
    
    if any(word in content for word in high_keywords):
        return (TaskPriority.HIGH, "Based on keywords: contains urgent/important words")
    elif any(word in content for word in low_keywords):
        return (TaskPriority.LOW, "Based on keywords: contains low priority words")
    else:
        return (TaskPriority.MEDIUM, "Based on keywords: default medium priority")


def _normalize_priority(value: Optional[str]) -> Optional[str]:
    """将优先级归一化为 low/medium/high"""
    if not value:
        return None
    normalized = str(value).strip().lower()
    if normalized in ["high", "h", "高", "高优先级", "优先级高"]:
        return "high"
    if normalized in ["medium", "med", "中", "中优先级", "优先级中"]:
        return "medium"
    if normalized in ["low", "l", "低", "低优先级", "优先级低"]:
        return "low"
    # 模糊匹配
    if "高" in normalized:
        return "high"
    if "低" in normalized:
        return "low"
    if "中" in normalized:
        return "medium"
    return normalized


def _parse_time_hint(text: str) -> Optional[Tuple[int, int]]:
    """解析时间提示，返回 (hour, minute) - 支持中英文"""
    text_lower = text.lower()
    
    # 英文时间格式: "3pm", "3 pm", "15:00", "at 3pm", "3:00 PM"
    pm_match = re.search(r'(\d{1,2})\s*(?:pm|p\.m\.)', text_lower)
    am_match = re.search(r'(\d{1,2})\s*(?:am|a\.m\.)', text_lower)
    time_match = re.search(r'(\d{1,2}):(\d{2})', text_lower)
    
    if pm_match:
        hour = int(pm_match.group(1))
        if hour < 12:
            hour += 12
        return (hour, 0)
    elif am_match:
        hour = int(am_match.group(1))
        if hour == 12:
            hour = 0
        return (hour, 0)
    elif time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        # 检查是否有 PM 标识
        if 'pm' in text_lower[time_match.end():time_match.end()+10]:
            if hour < 12:
                hour += 12
        elif 'am' in text_lower[time_match.end():time_match.end()+10]:
            if hour == 12:
                hour = 0
        return (hour, minute)
    
    # 中文时间格式: "3点", "下午3点"
    match = re.search(r'(上午|下午|晚上)?\s*(\d{1,2})点', text)
    if match:
        period = match.group(1) or ""
        hour = int(match.group(2))
        if period in ["下午", "晚上"] and hour < 12:
            hour += 12
        elif not period and hour <= 12:
            # 默认下午
            if hour < 12:
                hour += 12
        return (hour, 0)
    
    return None


def _parse_relative_date(text: str) -> Optional[datetime]:
    """解析相对日期（支持中英文：今天/明天/后天/today/tomorrow/next week等）"""
    now = datetime.now()
    text_lower = text.lower()
    weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
    weekday_map_en = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
                       "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

    base = None
    
    # 中文日期
    if "今天" in text or "today" in text_lower:
        base = now
    elif "明天" in text or "tomorrow" in text_lower:
        base = now + timedelta(days=1)
    elif "后天" in text or "day after tomorrow" in text_lower:
        base = now + timedelta(days=2)
    # 英文星期几
    elif "next" in text_lower:
        for day_name, day_num in weekday_map_en.items():
            if day_name in text_lower:
                current_weekday = now.weekday()
                delta = (day_num - current_weekday + 7) % 7
                if delta == 0:
                    delta = 7  # 如果是今天，则下周
                base = now + timedelta(days=delta)
                break
        if base is None:
            # "next week" 或 "next monday" 等
            if "monday" in text_lower or "mon" in text_lower:
                base = now + timedelta(days=(7 - now.weekday()))
            elif "tuesday" in text_lower or "tue" in text_lower:
                base = now + timedelta(days=(8 - now.weekday()))
            elif "wednesday" in text_lower or "wed" in text_lower:
                base = now + timedelta(days=(9 - now.weekday()))
            elif "thursday" in text_lower or "thu" in text_lower:
                base = now + timedelta(days=(10 - now.weekday()))
            elif "friday" in text_lower or "fri" in text_lower:
                base = now + timedelta(days=(11 - now.weekday()))
            elif "saturday" in text_lower or "sat" in text_lower:
                base = now + timedelta(days=(12 - now.weekday()))
            elif "sunday" in text_lower or "sun" in text_lower:
                base = now + timedelta(days=(13 - now.weekday()))
    # 中文星期几
    else:
        match = re.search(r'(本周|下周)[一二三四五六日天]', text)
        if match:
            week_flag = match.group(1)
            target_char = match.group(0)[2]
            target_weekday = weekday_map.get(target_char)
            if target_weekday is not None:
                current_weekday = now.weekday()
                if week_flag == "本周":
                    delta = target_weekday - current_weekday
                    if delta < 0:
                        delta += 7
                else:
                    delta = (target_weekday - current_weekday) + 7
                base = now + timedelta(days=delta)

    if base is None:
        return None

    time_hint = _parse_time_hint(text)
    if time_hint:
        return base.replace(hour=time_hint[0], minute=time_hint[1], second=0, microsecond=0)
    return base.replace(hour=23, minute=59, second=0, microsecond=0)


def _clean_title(text: str) -> str:
    """清理自然语言文本，得到标题（支持中英文）"""
    cleanup_patterns = [
        # 日期
        r'今天|明天|后天|本周[一二三四五六日天]|下周[一二三四五六日天]',
        r'\b(today|tomorrow|day after tomorrow|next (monday|tuesday|wednesday|thursday|friday|saturday|sunday|week))\b',
        # 时间
        r'(上午|下午|晚上)?\s*\d{1,2}点',
        r'\b\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)\b',
        r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b',
        r'\bat\s+\d{1,2}\s*(?:am|pm)?\b',
        # 优先级和修饰词
        r'优先级高|高优先级|很重要|紧急|尽快|优先级低|低优先级|不急|有空再',
        r'\b(urgent|important|critical|asap|high priority|low priority|priority (high|low))\b',
        r'\b(it\'?s\s+)?(very\s+)?(important|urgent)\b',
        # 常见开头和结尾
        r'\b(remind me to|remember to|don\'?t forget to|make sure to)\b',
        r'\b(to|at|in|on|for|with|by)\s+(it\'?s|the|a|an|this|that)\b',
        r'\b(it\'?s|that\'?s|this is)\s+(important|urgent|critical)\b',
        # 标点
        r'[，,。.!！]',
    ]
    title = text
    for pattern in cleanup_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    # 清理多余的空格和连词
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'\b(at|in|on|for|with|by|to)\s+(it\'?s|the|a|an|this|that)\b', '', title, flags=re.IGNORECASE)
    title = title.strip()
    return title or text


class AIService:
    """AI/LLM 服务 - 支持多个提供商和自动降级"""
    
    def __init__(self):
        self.providers: List[AIProvider] = []
        self.provider_mode = settings.ai_provider.lower()
        
        # 初始化提供商
        if self.provider_mode in ["openai", "auto"]:
            if settings.openai_api_key:
                try:
                    provider = OpenAIProvider(settings.openai_api_key)
                    if provider.available:
                        self.providers.append(provider)
                        logger.info("OpenAI 提供商已加载")
                except Exception as e:
                    logger.warning(f"OpenAI 提供商初始化失败: {e}")
        
        if self.provider_mode in ["google", "auto"]:
            if settings.google_ai_api_key:
                try:
                    provider = GoogleAIProvider(settings.google_ai_api_key)
                    if provider.available:
                        self.providers.append(provider)
                        logger.info("Google AI 提供商已加载")
                except Exception as e:
                    logger.warning(f"Google AI 提供商初始化失败: {e}")
        
        if not self.providers:
            logger.warning("没有可用的 AI 提供商，将使用降级方案")
    
    def _try_providers(self, func_name: str, *args, **kwargs):
        """尝试所有可用的提供商，失败时自动降级"""
        last_error = None
        
        for provider in self.providers:
            try:
                func = getattr(provider, func_name)
                result = func(*args, **kwargs)
                logger.info(f"使用 {provider.__class__.__name__} 成功执行 {func_name}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"{provider.__class__.__name__} 执行 {func_name} 失败: {e}")
                continue
        
        # 所有提供商都失败，使用降级方案
        logger.warning(f"所有 AI 提供商都失败，使用降级方案: {last_error}")
        return None
    
    def parse_natural_language(self, text: str) -> dict:
        """解析自然语言任务描述"""
        result = self._try_providers("parse_natural_language", text)
        if result:
            # 如果文本里明确包含优先级关键词，强制覆盖解析结果
            forced_priority, _reasoning = _get_fallback_priority(text, None)
            if forced_priority != TaskPriority.MEDIUM:
                result["priority"] = forced_priority.value
            # 归一化返回的优先级（防止模型返回中文或大小写不一致）
            result["priority"] = _normalize_priority(result.get("priority")) or "medium"
            return result
        
        # 降级方案
        logger.info("使用降级方案解析自然语言")
        priority, _reasoning = _get_fallback_priority(text, None)
        due_date = _parse_relative_date(text)
        title = _clean_title(text)
        return {
            "title": title,
            "description": None,
            "priority": priority.value,
            "due_date": due_date.isoformat() if due_date else None,
            "tags": []
        }
    
    def suggest_tags(self, title: str, description: Optional[str] = None) -> List[str]:
        """根据任务内容建议标签"""
        result = self._try_providers("suggest_tags", title, description)
        if result:
            return result
        
        # 降级方案
        logger.info("使用降级方案建议标签")
        return _get_fallback_tags(title, description)
    
    def breakdown_task(self, task_description: str) -> List[str]:
        """将复杂任务分解为子任务"""
        result = self._try_providers("breakdown_task", task_description)
        if result:
            return result
        
        # 降级方案
        logger.info("使用降级方案分解任务")
        return [
            f"准备 {task_description}",
            f"执行 {task_description}",
            f"完成 {task_description}"
        ]
    
    def recommend_priority(self, title: str, description: Optional[str] = None) -> Tuple[TaskPriority, str]:
        """推荐任务优先级"""
        result = self._try_providers("recommend_priority", title, description)
        if result:
            return result
        
        # 降级方案
        logger.info("使用降级方案推荐优先级")
        return _get_fallback_priority(title, description)


# 单例
_ai_service = None

def get_ai_service() -> AIService:
    """获取 AI 服务单例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
