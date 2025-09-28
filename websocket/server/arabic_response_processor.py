#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import os
from arabic_number_converter import ArabicNumberConverter

class ArabicResponseProcessor:
    """
    Processes AI responses to ensure proper Arabic formatting for TTS.
    """
    
    def __init__(self):
        self.number_converter = ArabicNumberConverter()
    
    def process_response(self, response: str, language: str = "ar") -> str:
        """
        Process AI response for optimal Arabic TTS pronunciation.
        
        Args:
            response: The AI response text
            language: Language preference ("ar" for Arabic, "en" for English)
        
        Returns:
            Processed response optimized for TTS
        """
        if language.lower() in ["ar", "arabic"]:
            # Convert numbers to Arabic format
            processed_response = self.number_converter.convert_for_tts(response)
            
            # Additional Arabic-specific processing can be added here
            # For example: currency symbols, date formats, etc.
            
            return processed_response
        
        # For English responses, just convert digits to Arabic digits
        return self.number_converter.convert_digits_to_arabic(response)
    
    def process_for_tts(self, text: str) -> str:
        """
        Process any text for optimal TTS pronunciation.
        This is a convenience method that assumes Arabic context.
        """
        return self.number_converter.convert_for_tts(text)

# Example usage and testing
if __name__ == "__main__":
    processor = ArabicResponseProcessor()
    
    # Test cases
    test_responses = [
        "لدينا 25 موظف في القسم",
        "المبلغ المطلوب هو 1,500 ريال",
        "النسبة المئوية للنجاح هي 85%",
        "التاريخ المحدد هو 2024/12/15",
        "لدينا 3 مكاتب و 50 موظف",
        "المعدل العام هو 92.5%",
        "الرقم المرجعي هو 12345",
        "لدينا 100 عميل نشط",
        "المبلغ الإجمالي هو 2,500 ريال",
        "النسبة المئوية للزيادة هي 15%"
    ]
    
    print("🎤 Arabic Response Processing Test")
    print("=" * 50)
    
    for response in test_responses:
        print(f"Original: {response}")
        processed = processor.process_response(response, "ar")
        print(f"Processed: {processed}")
        print("-" * 30)
