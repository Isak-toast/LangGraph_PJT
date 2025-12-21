"""
config.py - Deep Research 설정 관리
=====================================

Phase 6: Multi-LLM 지원을 위한 역할별 모델 설정

역할:
- Planner: 리서치 계획 수립 (빠른 모델)
- Searcher: 검색 전략 (기본 모델)
- Analyzer: 정보 분석 (분석 특화)
- Writer: 최종 응답 (고품질 모델)
- Critic: 품질 평가 (분석 특화)
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict
from langchain_google_genai import ChatGoogleGenerativeAI


@dataclass
class ModelConfig:
    """개별 모델 설정"""
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> dict:
        config = {
            "model": self.model_name,
            "temperature": self.temperature,
        }
        if self.max_tokens:
            config["max_tokens"] = self.max_tokens
        return config


@dataclass
class ResearchConfig:
    """
    역할별 LLM 설정
    
    환경변수로 오버라이드 가능:
    - PLANNER_MODEL
    - SEARCHER_MODEL
    - ANALYZER_MODEL
    - WRITER_MODEL
    - CRITIC_MODEL
    """
    
    # 기본 모델 (모든 역할에서 fallback으로 사용)
    default_model: str = "gemini-2.0-flash"
    
    # 역할별 모델 설정
    planner: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name=os.getenv("PLANNER_MODEL", "gemini-2.0-flash"),
        temperature=0.3  # 계획은 일관성 있게
    ))
    
    searcher: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name=os.getenv("SEARCHER_MODEL", "gemini-2.0-flash"),
        temperature=0.5
    ))
    
    analyzer: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name=os.getenv("ANALYZER_MODEL", "gemini-2.0-flash"),
        temperature=0.3  # 분석은 일관성 있게
    ))
    
    writer: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name=os.getenv("WRITER_MODEL", "gemini-2.0-flash"),
        temperature=0.7  # 글쓰기는 창의적으로
    ))
    
    critic: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name=os.getenv("CRITIC_MODEL", "gemini-2.0-flash"),
        temperature=0.2  # 비평은 객관적으로
    ))
    
    # 연구 설정
    max_research_iterations: int = 3
    max_urls_per_search: int = 5
    max_content_length: int = 4000
    
    # 로깅 설정
    verbose_mode: bool = field(default_factory=lambda: 
        os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
    )
    
    def get_llm(self, role: str) -> ChatGoogleGenerativeAI:
        """역할에 맞는 LLM 인스턴스 반환"""
        
        role_configs = {
            "planner": self.planner,
            "searcher": self.searcher,
            "analyzer": self.analyzer,
            "writer": self.writer,
            "critic": self.critic,
        }
        
        config = role_configs.get(role.lower(), self.planner)
        
        return ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
        )
    
    def get_model_info(self) -> Dict[str, str]:
        """현재 설정된 모델 정보 반환"""
        return {
            "planner": self.planner.model_name,
            "searcher": self.searcher.model_name,
            "analyzer": self.analyzer.model_name,
            "writer": self.writer.model_name,
            "critic": self.critic.model_name,
        }
    
    def print_config(self):
        """설정 정보 출력"""
        print("\n📋 Research Config:")
        print(f"   └─ Default Model: {self.default_model}")
        print("   └─ Role Models:")
        for role, model in self.get_model_info().items():
            temp = getattr(self, role).temperature
            print(f"      • {role.capitalize()}: {model} (temp={temp})")
        print(f"   └─ Max Iterations: {self.max_research_iterations}")
        print(f"   └─ Verbose Mode: {self.verbose_mode}")


# 글로벌 설정 인스턴스
research_config = ResearchConfig()
