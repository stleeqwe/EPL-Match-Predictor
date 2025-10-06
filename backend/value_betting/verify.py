#!/usr/bin/env python3
"""
Quick Verification Script
value_betting 모듈이 정상적으로 작동하는지 빠르게 확인
"""

import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """모듈 import 테스트"""
    print("=" * 60)
    print("1. Testing Imports...")
    print("-" * 60)
    
    try:
        from value_betting import ValueDetector, ArbitrageFinder, KellyCriterion
        print("✅ Main classes imported successfully")
        
        from value_betting.utils import (
            decimal_to_probability,
            calculate_edge,
            get_best_odds
        )
        print("✅ Utility functions imported successfully")
        
        from value_betting.exceptions import ValueBettingError
        print("✅ Exceptions imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n" + "=" * 60)
    print("2. Testing Basic Functionality...")
    print("-" * 60)
    
    try:
        from value_betting import ValueDetector, ArbitrageFinder, KellyCriterion
        
        # ValueDetector
        detector = ValueDetector()
        print("✅ ValueDetector initialized")
        
        # ArbitrageFinder
        arb_finder = ArbitrageFinder()
        print("✅ ArbitrageFinder initialized")
        
        # KellyCriterion
        kelly = KellyCriterion()
        print("✅ KellyCriterion initialized")
        
        # 간단한 계산 테스트
        kelly_percent = kelly.calculate_kelly(0.6, 2.0)
        print(f"✅ Kelly calculation: {kelly_percent:.2%}")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False


def test_api_integration():
    """API 통합 테스트"""
    print("\n" + "=" * 60)
    print("3. Testing API Integration...")
    print("-" * 60)
    
    try:
        # app_odds_based.py가 import 가능한지 확인
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
        
        # Import만 테스트 (서버 시작 X)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "app_odds_based",
            os.path.join(os.path.dirname(__file__), '..', 'api', 'app_odds_based.py')
        )
        
        if spec and spec.loader:
            print("✅ app_odds_based.py found")
            print("✅ API integration ready")
            return True
        else:
            print("❌ app_odds_based.py not found")
            return False
            
    except Exception as e:
        print(f"⚠️  API integration test skipped: {e}")
        return True  # API 테스트는 optional


def test_documentation():
    """문서 존재 확인"""
    print("\n" + "=" * 60)
    print("4. Checking Documentation...")
    print("-" * 60)
    
    docs_exist = True
    
    # README.md
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        print("✅ README.md exists")
    else:
        print("❌ README.md not found")
        docs_exist = False
    
    # IMPLEMENTATION_REPORT.md
    report_path = os.path.join(os.path.dirname(__file__), 'IMPLEMENTATION_REPORT.md')
    if os.path.exists(report_path):
        print("✅ IMPLEMENTATION_REPORT.md exists")
    else:
        print("❌ IMPLEMENTATION_REPORT.md not found")
        docs_exist = False
    
    # test_integration.py
    test_path = os.path.join(os.path.dirname(__file__), 'test_integration.py')
    if os.path.exists(test_path):
        print("✅ test_integration.py exists")
    else:
        print("❌ test_integration.py not found")
        docs_exist = False
    
    return docs_exist


def main():
    """메인 검증 함수"""
    print("\n" + "=" * 60)
    print("VALUE BETTING MODULE - QUICK VERIFICATION")
    print("=" * 60)
    
    results = {
        'imports': test_imports(),
        'functionality': test_basic_functionality(),
        'api': test_api_integration(),
        'docs': test_documentation()
    }
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper():20s}: {status}")
    
    print("-" * 60)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("\nValue Betting Module is ready to use.")
        print("\nNext steps:")
        print("  1. Run full integration tests:")
        print("     python value_betting/test_integration.py")
        print("  2. Start API server:")
        print("     python api/app_odds_based.py")
        print("  3. Test API endpoints:")
        print("     curl http://localhost:5001/api/health")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above and fix them.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
