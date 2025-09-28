#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import re
from typing import List, Tuple

class OrganizationalKnowledgeFilter:
    """
    Simple filter to help ensure responses stay within organizational scope.
    This is a basic implementation that can be enhanced with more sophisticated NLP.
    """
    
    def __init__(self):
        # Organizational topics in Arabic and English
        self.organizational_keywords = [
            # Arabic keywords
            "سياسات الموارد البشرية", "الموارد البشرية", "HR", "hr",
            "الدعم التقني", "التقنية", "IT", "it", "تقنية المعلومات",
            "الإجراءات الإدارية", "الإدارة", "administrative",
            "المزايا", "الفوائد", "benefits", "مزايا الموظفين",
            "الإجازات", "الإجازة", "leave", "vacation", "إجازة سنوية", "إجازة مرضية",
            "التدريب", "التطوير", "training", "development",
            "الرواتب", "الراتب", "salary", "payroll", "الأجور",
            "التأمين", "insurance", "التأمين الصحي",
            "التقاعد", "retirement", "معاش التقاعد",
            "ساعات العمل", "working hours", "وقت العمل",
            "المرافق", "facilities", "الخدمات", "services",
            "السياسات", "policies", "القوانين", "regulations",
            "الإجراءات", "procedures", "الخطوات", "steps",
            "الموظفين", "employees", "العاملين", "staff",
            "الهيئة", "organization", "الشركة", "company",
            "العمل", "work", "الوظيفة", "job", "المهام", "tasks",
            "التوظيف", "recruitment", "الاستقدام", "hiring",
            "التقييم", "evaluation", "التقييم السنوي", "annual review",
            "الترقية", "promotion", "الترقيات", "advancement",
            "الانضباط", "discipline", "العقوبات", "penalties",
            "الشكاوى", "complaints", "الاعتراضات", "grievances",
            "الأمان", "security", "الأمان السيبراني", "cybersecurity",
            "البيانات", "data", "المعلومات", "information",
            "الخصوصية", "privacy", "حماية البيانات", "data protection"
        ]
        
        # Non-organizational topics to explicitly avoid
        self.non_organizational_keywords = [
            # Arabic
            "الطقس", "الجو", "المطر", "الشمس",
            "السياسة", "الحكومة", "الرئيس", "الوزير",
            "الرياضة", "كرة القدم", "المباراة", "الفريق",
            "الطبخ", "الطعام", "الوصفات", "المطاعم", "الطبخ المنزلي",
            "السفر", "السياحة", "الرحلات", "الطيران",
            "الأفلام", "المسلسلات", "الترفيه", "السينما",
            "الموسيقى", "الأغاني", "الفنانين", "المطربين",
            "الأخبار", "الأحداث", "العالم", "الدول",
            "التاريخ", "الحضارات", "القديمة", "الفراعنة",
            "العلوم", "الفيزياء", "الكيمياء", "الرياضيات",
            "الطب", "الأمراض", "العلاج", "الطبيب",
            "الاقتصاد", "الأسهم", "البنوك", "المال",
            "التعليم", "الجامعات", "الدراسة", "الطلاب",
            "الدين", "الصلاة", "الصوم", "الحج",
            "الفلسفة", "الأفكار", "النظريات", "المنطق",
            
            # English
            "weather", "rain", "sunny", "cloudy",
            "politics", "government", "president", "minister",
            "sports", "football", "soccer", "basketball",
            "cooking", "food", "recipe", "restaurant",
            "travel", "tourism", "vacation", "airline",
            "movies", "series", "entertainment", "cinema",
            "music", "songs", "artists", "singers",
            "news", "events", "world", "countries",
            "history", "civilizations", "ancient", "pharaohs",
            "science", "physics", "chemistry", "mathematics",
            "medicine", "diseases", "treatment", "doctor",
            "economy", "stocks", "banks", "money",
            "education", "universities", "study", "students",
            "religion", "prayer", "fasting", "pilgrimage",
            "philosophy", "ideas", "theories", "logic"
        ]
    
    def is_organizational_query(self, query: str) -> Tuple[bool, str]:
        """
        Check if a query is related to organizational topics.
        Returns (is_organizational, reason)
        """
        query_lower = query.lower()
        
        # Check for non-organizational topics first
        for keyword in self.non_organizational_keywords:
            if keyword.lower() in query_lower:
                return False, f"Query contains non-organizational topic: {keyword}"
        
        # Check for organizational topics
        organizational_matches = []
        for keyword in self.organizational_keywords:
            if keyword.lower() in query_lower:
                organizational_matches.append(keyword)
        
        if organizational_matches:
            return True, f"Query matches organizational topics: {', '.join(organizational_matches[:3])}"
        
        # If no clear matches, assume it might be organizational but flag for review
        return True, "No clear topic match - defaulting to organizational scope"
    
    def get_escalation_response(self, language: str = "ar") -> str:
        """
        Get appropriate escalation response based on language preference.
        """
        if language.lower() in ["ar", "arabic"]:
            return "آسف، لا أملك هذه المعلومة في قاعدة بيانات الهيئة. هل تريد التحويل لموظف بشري للمساعده؟"
        else:
            return "Sorry, I don't have this information in the organization's database. Would you like me to transfer you to a human for assistance?"
    
    def get_out_of_scope_response(self, language: str = "ar") -> str:
        """
        Get appropriate response for out-of-scope queries.
        """
        if language.lower() in ["ar", "arabic"]:
            return "أعتذر، يمكنني فقط الإجابة عن الأسئلة المتعلقة بالهيئة والعمل. كيف يمكنني مساعدتك في شؤون العمل؟"
        else:
            return "I apologize, I can only answer questions related to the organization and work. How can I help you with work-related matters?"

# Example usage and testing
if __name__ == "__main__":
    filter_instance = OrganizationalKnowledgeFilter()
    
    # Test cases
    test_queries = [
        "ما هي سياسة الإجازات السنوية؟",
        "كيف يمكنني الحصول على دعم تقني؟",
        "ما هو الطقس اليوم؟",
        "كيف يمكنني تحديث بياناتي الشخصية؟",
        "ما هي آخر أخبار كرة القدم؟",
        "What is the HR policy for sick leave?",
        "How do I request vacation time?",
        "What's the weather like today?",
        "Tell me about the latest movies"
    ]
    
    print("Testing Organizational Knowledge Filter:")
    print("=" * 50)
    
    for query in test_queries:
        is_org, reason = filter_instance.is_organizational_query(query)
        status = "✅ ORGANIZATIONAL" if is_org else "❌ NON-ORGANIZATIONAL"
        print(f"Query: {query}")
        print(f"Status: {status}")
        print(f"Reason: {reason}")
        print("-" * 30)
