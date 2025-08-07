from typing import Optional, List, Dict


class LLMConfig:
    """LLM 配置表"""
    base_url: str = ""
    model: str = ""
    max_tokens: int = 32768
    default_temp: float = 0.5

class OpenRouter:
    """
    通过 OpenRouter API 与中转平台交互
    该实现利用 `AsyncOpenAI` 客户端进行异步操作
    """

    def __init__(self, api_key: str):
        """加载 API key 以初始化 OpenRouter

        Args:
            api_key (str): OpenRouter API key
        """
        self.config = LLMConfig()
        self.client = AsyncOpenAI(
            base_url=self.config.base_url,
            api_key=api_key
        )
        self._is_authenticated = False

async def agenerate(
    self, 
    messages: List[Dict], 
    temperature: Optional[float] = None
) -> str:
    """异步生成文本
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature (0.0 to 1.0, 默认从 LLMConfig.default_temp 中获取)
    
    Returns:
        str: 生成的文本
    
    Example:
        >>> messages = [
        ...     {"role": "system", "content": "You are a helpful assistant."},
        ...     {"role": "user", "content": "Plan my study schedule."}
        ... ]
        >>> response = await llm.agenerate(messages, temperature=0.7)
    """
    completion = await self.client.chat.completions.create(
        model=self.config.model,
        messages=messages,
        temperature=temperature or self.config.default_temp,
        max_tokens=self.config.max_tokens,
        stream=False
    )
    return completion.choices[0].message.content
