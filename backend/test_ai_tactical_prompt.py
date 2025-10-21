#!/usr/bin/env python3
"""
AI Tactical Prompt 출력 테스트
실제로 AI에게 전달되는 프롬프트를 보여줍니다.
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from services.enriched_data_loader import EnrichedDomainDataLoader
from simulation.v3.models.ai_tactical_model import AITacticalModel

# Load data
loader = EnrichedDomainDataLoader()
arsenal = loader.load_team_data("Arsenal")
liverpool = loader.load_team_data("Liverpool")

# Create AI Tactical Model (without calling AI)
model = AITacticalModel()

# Math reference (예시)
math_reference = {
    'home_win': 0.354,
    'draw': 0.263,
    'away_win': 0.383
}

# Build prompts (AI 호출 없이 프롬프트만 생성)
system_prompt = model._build_system_prompt()
user_prompt = model._build_user_prompt(arsenal, liverpool, math_reference)

print("\n" + "="*100)
print("SYSTEM PROMPT (AI의 역할 정의)")
print("="*100)
print(system_prompt)

print("\n\n" + "="*100)
print("USER PROMPT (실제 데이터)")
print("="*100)
print(user_prompt)

print("\n\n" + "="*100)
print("SUMMARY")
print("="*100)
print(f"System Prompt 길이: {len(system_prompt)} chars")
print(f"User Prompt 길이: {len(user_prompt)} chars")
print(f"Total: {len(system_prompt) + len(user_prompt)} chars")
print(f"예상 토큰: ~{(len(system_prompt) + len(user_prompt)) / 4:.0f} tokens")
print()
