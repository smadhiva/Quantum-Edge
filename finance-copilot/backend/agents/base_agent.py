"""
Base Agent - Foundation for all specialized agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from config import settings


class BaseAgent(ABC):
    """
    Base class for all agents in the Finance Portfolio Copilot
    Provides common functionality and interface
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = None
        self.memory: List[Dict[str, Any]] = []
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize Gemini LLM"""
        if settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.llm = genai.GenerativeModel(
                    model_name=settings.gemini_model,
                    generation_config={
                        "temperature": settings.gemini_temperature,
                        "top_p": 0.95,
                        "top_k": 64,
                        "max_output_tokens": 8192,
                    }
                )
            except Exception as e:
                print(f"Failed to initialize LLM for {self.name}: {e}")
    
    async def think(self, prompt: str, context: str = "") -> str:
        """
        Use LLM to reason about a problem
        """
        if not self.llm:
            return "LLM not initialized"
        
        full_prompt = f"""You are {self.name}, a specialized financial analysis agent.
{self.description}

Context:
{context}

Task:
{prompt}

Provide a detailed, professional analysis:"""
        
        try:
            response = self.llm.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    async def structured_think(
        self, 
        prompt: str, 
        context: str = "",
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Use LLM to generate structured output
        """
        format_instruction = """
Please respond in valid JSON format with the following structure:
{
    "analysis": "your detailed analysis",
    "key_points": ["point 1", "point 2"],
    "recommendation": "your recommendation",
    "confidence": 0.0 to 1.0
}"""
        
        response = await self.think(prompt + format_instruction, context)
        
        # Try to parse JSON response
        try:
            import json
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        
        return {"analysis": response, "confidence": 0.5}
    
    def add_to_memory(self, entry: Dict[str, Any]):
        """Add entry to agent memory"""
        entry["timestamp"] = datetime.now().isoformat()
        entry["agent"] = self.name
        self.memory.append(entry)
        
        # Keep memory bounded
        if len(self.memory) > 100:
            self.memory = self.memory[-50:]
    
    def get_relevant_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant memory entries (simple keyword matching)"""
        query_lower = query.lower()
        relevant = []
        
        for entry in reversed(self.memory):
            content = str(entry).lower()
            if any(word in content for word in query_lower.split()):
                relevant.append(entry)
                if len(relevant) >= limit:
                    break
        
        return relevant
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task - must be implemented by subclasses
        """
        pass
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class AgentState:
    """
    State management for agent workflows
    Used with LangGraph for multi-step reasoning
    """
    
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        self.current_step: str = "start"
        self.completed_steps: List[str] = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_context(self, key: str, value: Any):
        """Update context with new information"""
        self.context[key] = value
    
    def set_result(self, key: str, value: Any):
        """Store a result"""
        self.results[key] = value
    
    def complete_step(self, step: str):
        """Mark a step as completed"""
        self.completed_steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "messages": self.messages,
            "context": self.context,
            "results": self.results,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps
        }


class Tool:
    """
    Base class for agent tools
    """
    
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool"""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)


import asyncio
