#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import re
from typing import Union

class ArabicNumberConverter:
    """
    Converts English numbers to Arabic numerals and Arabic text for better TTS pronunciation.
    """
    
    def __init__(self):
        # Arabic numerals mapping
        self.english_to_arabic_digits = {
            '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
            '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
        }
        
        # Arabic text for numbers
        self.numbers_arabic_text = {
            0: 'صفر', 1: 'واحد', 2: 'اثنان', 3: 'ثلاثة', 4: 'أربعة',
            5: 'خمسة', 6: 'ستة', 7: 'سبعة', 8: 'ثمانية', 9: 'تسعة',
            10: 'عشرة', 11: 'أحد عشر', 12: 'اثنا عشر', 13: 'ثلاثة عشر',
            14: 'أربعة عشر', 15: 'خمسة عشر', 16: 'ستة عشر', 17: 'سبعة عشر',
            18: 'ثمانية عشر', 19: 'تسعة عشر', 20: 'عشرون', 30: 'ثلاثون',
            40: 'أربعون', 50: 'خمسون', 60: 'ستون', 70: 'سبعون',
            80: 'ثمانون', 90: 'تسعون', 100: 'مئة', 1000: 'ألف',
            1000000: 'مليون', 1000000000: 'مليار'
        }
        
        # Common number patterns
        self.number_patterns = [
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b',  # Numbers with commas and decimals
            r'\b\d+\b',  # Simple numbers
            r'\b\d+\.\d+\b',  # Decimal numbers
            r'\b\d+/\d+\b',  # Fractions
            r'\b\d+%\b',  # Percentages
        ]
    
    def convert_digits_to_arabic(self, text: str) -> str:
        """Convert English digits to Arabic digits."""
        result = text
        for eng_digit, arab_digit in self.english_to_arabic_digits.items():
            result = result.replace(eng_digit, arab_digit)
        return result
    
    def number_to_arabic_text(self, num: Union[int, float]) -> str:
        """Convert a number to Arabic text representation."""
        if isinstance(num, float):
            # Handle decimal numbers
            integer_part = int(num)
            decimal_part = int((num - integer_part) * 100)  # Assume 2 decimal places
            
            if decimal_part == 0:
                return self._integer_to_arabic_text(integer_part)
            else:
                integer_text = self._integer_to_arabic_text(integer_part)
                decimal_text = self._integer_to_arabic_text(decimal_part)
                return f"{integer_text} فاصلة {decimal_text}"
        
        return self._integer_to_arabic_text(int(num))
    
    def _integer_to_arabic_text(self, num: int) -> str:
        """Convert integer to Arabic text."""
        if num in self.numbers_arabic_text:
            return self.numbers_arabic_text[num]
        
        if num < 100:
            # Handle numbers 21-99
            tens = (num // 10) * 10
            ones = num % 10
            if tens in self.numbers_arabic_text and ones in self.numbers_arabic_text:
                return f"{self.numbers_arabic_text[ones]} و {self.numbers_arabic_text[tens]}"
            elif tens in self.numbers_arabic_text:
                return f"{self.numbers_arabic_text[tens]} و {self.numbers_arabic_text[ones]}"
        
        if num < 1000:
            # Handle hundreds
            hundreds = num // 100
            remainder = num % 100
            if remainder == 0:
                return f"{self.numbers_arabic_text[hundreds]} مئة"
            else:
                return f"{self.numbers_arabic_text[hundreds]} مئة و {self._integer_to_arabic_text(remainder)}"
        
        if num < 1000000:
            # Handle thousands
            thousands = num // 1000
            remainder = num % 1000
            if remainder == 0:
                return f"{self._integer_to_arabic_text(thousands)} ألف"
            else:
                return f"{self._integer_to_arabic_text(thousands)} ألف و {self._integer_to_arabic_text(remainder)}"
        
        # For very large numbers, return Arabic digits
        return self.convert_digits_to_arabic(str(num))
    
    def convert_text_numbers(self, text: str, use_arabic_digits: bool = True, use_arabic_text: bool = False) -> str:
        """
        Convert all numbers in text to Arabic format.
        
        Args:
            text: Input text containing numbers
            use_arabic_digits: Convert to Arabic digits (٠١٢٣٤٥٦٧٨٩)
            use_arabic_text: Convert to Arabic text (واحد، اثنان، إلخ)
        """
        result = text
        
        # Find all number patterns
        for pattern in self.number_patterns:
            matches = re.findall(pattern, result)
            for match in matches:
                try:
                    # Clean the number (remove commas)
                    clean_number = match.replace(',', '')
                    
                    # Handle different number formats
                    if '%' in clean_number:
                        # Percentage
                        num_value = float(clean_number.replace('%', ''))
                        if use_arabic_text:
                            arabic_replacement = f"{self.number_to_arabic_text(num_value)} بالمئة"
                        else:
                            arabic_replacement = f"{self.convert_digits_to_arabic(clean_number)}%"
                    
                    elif '/' in clean_number:
                        # Fraction
                        parts = clean_number.split('/')
                        if len(parts) == 2:
                            numerator = int(parts[0])
                            denominator = int(parts[1])
                            if use_arabic_text:
                                arabic_replacement = f"{self.number_to_arabic_text(numerator)} على {self.number_to_arabic_text(denominator)}"
                            else:
                                arabic_replacement = f"{self.convert_digits_to_arabic(parts[0])}/{self.convert_digits_to_arabic(parts[1])}"
                    
                    elif '.' in clean_number:
                        # Decimal number
                        num_value = float(clean_number)
                        if use_arabic_text:
                            arabic_replacement = self.number_to_arabic_text(num_value)
                        else:
                            arabic_replacement = self.convert_digits_to_arabic(clean_number)
                    
                    else:
                        # Integer
                        num_value = int(clean_number)
                        if use_arabic_text:
                            arabic_replacement = self.number_to_arabic_text(num_value)
                        else:
                            arabic_replacement = self.convert_digits_to_arabic(clean_number)
                    
                    # Replace in the result
                    result = result.replace(match, arabic_replacement)
                    
                except (ValueError, TypeError):
                    # If conversion fails, just convert digits
                    if use_arabic_digits:
                        result = result.replace(match, self.convert_digits_to_arabic(match))
        
        return result
    
    def convert_for_tts(self, text: str) -> str:
        """
        Convert text for optimal TTS pronunciation in Arabic.
        Uses Arabic text for small numbers and Arabic digits for larger numbers.
        """
        result = text
        
        # Find all number patterns
        for pattern in self.number_patterns:
            matches = re.findall(pattern, result)
            for match in matches:
                try:
                    # Clean the number (remove commas)
                    clean_number = match.replace(',', '')
                    
                    # Handle different number formats
                    if '%' in clean_number:
                        # Percentage
                        num_value = float(clean_number.replace('%', ''))
                        if num_value <= 100:
                            arabic_replacement = f"{self.number_to_arabic_text(num_value)} بالمئة"
                        else:
                            arabic_replacement = f"{self.convert_digits_to_arabic(clean_number)}%"
                    
                    elif '/' in clean_number:
                        # Fraction
                        parts = clean_number.split('/')
                        if len(parts) == 2:
                            numerator = int(parts[0])
                            denominator = int(parts[1])
                            if numerator <= 20 and denominator <= 20:
                                arabic_replacement = f"{self.number_to_arabic_text(numerator)} على {self.number_to_arabic_text(denominator)}"
                            else:
                                arabic_replacement = f"{self.convert_digits_to_arabic(parts[0])}/{self.convert_digits_to_arabic(parts[1])}"
                    
                    elif '.' in clean_number:
                        # Decimal number
                        num_value = float(clean_number)
                        if num_value <= 100:
                            arabic_replacement = self.number_to_arabic_text(num_value)
                        else:
                            arabic_replacement = self.convert_digits_to_arabic(clean_number)
                    
                    else:
                        # Integer
                        num_value = int(clean_number)
                        if num_value <= 100:
                            arabic_replacement = self.number_to_arabic_text(num_value)
                        else:
                            arabic_replacement = self.convert_digits_to_arabic(clean_number)
                    
                    # Replace in the result
                    result = result.replace(match, arabic_replacement)
                    
                except (ValueError, TypeError):
                    # If conversion fails, just convert digits
                    result = result.replace(match, self.convert_digits_to_arabic(match))
        
        return result

# Example usage and testing
if __name__ == "__main__":
    converter = ArabicNumberConverter()
    
    # Test cases
    test_texts = [
        "لدينا 25 موظف في القسم",
        "المبلغ هو 1,500 ريال",
        "النسبة المئوية هي 75%",
        "التاريخ هو 2024/12/15",
        "الرقم هو 3.14",
        "لدينا 1000 عميل",
        "المعدل هو 85.5%",
        "الوقت هو 2:30",
        "الرقم السري هو 1234",
        "لدينا 50 موظف و 25 متدرب"
    ]
    
    print("🧮 Arabic Number Conversion Test")
    print("=" * 50)
    
    for text in test_texts:
        print(f"Original: {text}")
        converted = converter.convert_for_tts(text)
        print(f"Converted: {converted}")
        print("-" * 30)
