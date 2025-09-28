#!/usr/bin/env python3
#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Test script for Arabic-first organizational AI agent.
This script helps verify that the Arabic configuration is working correctly.
"""

import os
import sys
from dotenv import load_dotenv
from organizational_filter import OrganizationalKnowledgeFilter

# Load environment variables
load_dotenv(override=True)

def test_environment_config():
    """Test environment configuration."""
    print("🔧 Testing Environment Configuration:")
    print("=" * 50)
    
    required_vars = ["GOOGLE_API_KEY", "DEFAULT_LANGUAGE", "ORGANIZATION_NAME", "ASSISTANT_NAME"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    print()

def test_organizational_filter():
    """Test the organizational knowledge filter."""
    print("🔍 Testing Organizational Knowledge Filter:")
    print("=" * 50)
    
    filter_instance = OrganizationalKnowledgeFilter()
    
    test_queries = [
        # Arabic organizational queries
        "ما هي سياسة الإجازات السنوية؟",
        "كيف يمكنني الحصول على دعم تقني؟",
        "ما هي مزايا التأمين الصحي؟",
        "كيف يمكنني تحديث بياناتي الشخصية؟",
        "ما هي ساعات العمل الرسمية؟",
        
        # English organizational queries
        "What is the HR policy for sick leave?",
        "How do I request vacation time?",
        "What are the employee benefits?",
        "How can I update my personal information?",
        
        # Non-organizational queries (should be filtered out)
        "ما هو الطقس اليوم؟",
        "ما هي آخر أخبار كرة القدم؟",
        "كيف أطبخ الكبسة؟",
        "What's the weather like today?",
        "Tell me about the latest movies",
        "How do I cook pasta?"
    ]
    
    for query in test_queries:
        is_org, reason = filter_instance.is_organizational_query(query)
        status = "✅ ORGANIZATIONAL" if is_org else "❌ NON-ORGANIZATIONAL"
        print(f"Query: {query}")
        print(f"Status: {status}")
        print(f"Reason: {reason}")
        print("-" * 30)

def test_arabic_responses():
    """Test Arabic response generation."""
    print("🗣️ Testing Arabic Response Generation:")
    print("=" * 50)
    
    filter_instance = OrganizationalKnowledgeFilter()
    
    # Test escalation response
    escalation_ar = filter_instance.get_escalation_response("ar")
    escalation_en = filter_instance.get_escalation_response("en")
    
    print("Arabic escalation response:")
    print(f"  {escalation_ar}")
    print()
    print("English escalation response:")
    print(f"  {escalation_en}")
    print()
    
    # Test out-of-scope response
    out_of_scope_ar = filter_instance.get_out_of_scope_response("ar")
    out_of_scope_en = filter_instance.get_out_of_scope_response("en")
    
    print("Arabic out-of-scope response:")
    print(f"  {out_of_scope_ar}")
    print()
    print("English out-of-scope response:")
    print(f"  {out_of_scope_en}")
    print()

def test_system_instruction():
    """Test the system instruction generation."""
    print("📝 Testing System Instruction:")
    print("=" * 50)
    
    # Simulate the system instruction from bot_fast_api.py
    organization_name = os.getenv('ORGANIZATION_NAME', 'الهيئة')
    assistant_name = os.getenv('ASSISTANT_NAME', 'مساعد الهيئة')
    
    system_instruction = f"""
أنت مساعد ذكي للموظفين في {organization_name} باسم "{assistant_name}".

القواعد الأساسية:
1. ابدأ دائماً بالترحيب باللغة العربية (اللهجة السعودية)
2. استمر بالعربية ما لم يطلب الموظف التحدث بالإنجليزية صراحة
3. أجب فقط عن الأسئلة المتعلقة بالهيئة والعمل
4. إذا لم تجد الإجابة، اعرض التحويل لموظف بشري
5. لا تجب عن أسئلة خارج نطاق الهيئة أبداً
6. كن مهذباً ومفيداً ومختصراً
"""
    
    print("Generated System Instruction:")
    print(system_instruction)
    print()

def main():
    """Run all tests."""
    print("🚀 Arabic-First Organizational AI Agent - Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_environment_config()
        test_organizational_filter()
        test_arabic_responses()
        test_system_instruction()
        
        print("✅ All tests completed successfully!")
        print()
        print("📋 Next Steps:")
        print("1. Copy env.example to .env and fill in your Google API key")
        print("2. Set ORGANIZATION_NAME to your organization's name")
        print("3. Run: python server.py")
        print("4. Test with Arabic voice input")
        print("5. Verify the agent responds in Arabic (Saudi accent)")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
