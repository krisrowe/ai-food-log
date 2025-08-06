"""
Gemini API Client for Food Analysis
"""

import os
import json
import re
import time
import configparser
import yaml
from datetime import datetime
from typing import Optional
import google.generativeai as genai


class GeminiClient:
    """Real Gemini API client implementation with tracing support"""
    
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            # Try loading from config.ini
            api_key = self._load_api_key_from_config()
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable or api_key parameter is required")
        
        genai.configure(api_key=api_key)
        # Use latest Gemini Flash model for better nutrition analysis accuracy
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash-latest',
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent nutrition facts
                top_p=0.8,
                top_k=20,
                max_output_tokens=4096,
            )
        )
        
        # Load configuration for tracing
        self.config = self._load_config()
        self.trace_enabled = self.config.get('logging', {}).get('enable_ai_api_trace', False)
    
    def _load_api_key_from_config(self) -> Optional[str]:
        """Load API key from config.ini file"""
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            return config.get('gemini', 'api_key', fallback=None)
        except Exception:
            return None
    
    def _load_config(self) -> dict:
        """Load configuration from config.yaml"""
        try:
            with open('config.yaml', 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    
    def _write_trace(self, input_text: str, request_data: dict, response_data: dict, duration: float, error: str = None):
        """Write human-readable trace to ai_api_trace.log"""
        if not self.trace_enabled:
            return
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open('ai_api_trace.log', 'a', encoding='utf-8') as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write("🤖 AI API CALL\n")
                f.write("=" * 80 + "\n")
                f.write(f"📅 Timestamp: {timestamp}\n")
                f.write(f"🍽️  Input: \"{input_text}\"\n")
                f.write(f"⏱️  Duration: {duration:.1f}s\n")
                f.write("-" * 40 + " REQUEST " + "-" * 40 + "\n")
                
                # Format request more readably
                if 'contents' in request_data and request_data['contents']:
                    prompt_text = request_data['contents'][0]['parts'][0]['text']
                    # Extract just the key parts of the prompt
                    lines = prompt_text.split('\n')
                    food_line = next((line for line in lines if 'Food description:' in line), '')
                    f.write(f"Model: {request_data.get('model', 'unknown')}\n")
                    f.write(f"Prompt: Food analysis request\n")
                    f.write(f"{food_line}\n")
                else:
                    f.write(json.dumps(request_data, indent=2, ensure_ascii=False))
                
                f.write("-" * 40 + " RESPONSE " + "-" * 39 + "\n")
                
                if error:
                    f.write(f"❌ Error: {error}\n")
                else:
                    # Format response more readably
                    if isinstance(response_data, dict):
                        f.write(f"✅ Status: Success\n")
                        for key, value in response_data.items():
                            if key == 'source_notes':
                                f.write(f"📝 {key}: {value}\n")
                            elif key == 'confidence_score':
                                f.write(f"🎯 {key}: {value}/10\n")
                            elif key == 'food_name':
                                f.write(f"🥘 {key}: {value}\n")
                            elif key in ['serving_amount', 'serving_unit']:
                                f.write(f"⚖️  {key}: {value}\n")
                            elif 'calorie' in key.lower():
                                f.write(f"🔥 {key}: {value}\n")
                            elif key.endswith('_g'):
                                f.write(f"🧪 {key}: {value}g\n")
                            elif key.endswith('_mg'):
                                f.write(f"💊 {key}: {value}mg\n")
                            else:
                                f.write(f"📊 {key}: {value}\n")
                        
                        # Add raw JSON for debugging
                        f.write("\n" + "-" * 35 + " RAW JSON " + "-" * 35 + "\n")
                        f.write(json.dumps(response_data, indent=2, ensure_ascii=False))
                        f.write("\n")
                    else:
                        f.write(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                f.write("=" * 80 + "\n")
        except Exception as e:
            # Don't let tracing errors break the main functionality
            print(f"Warning: Failed to write trace: {e}")
    

    
    def analyze_food(self, description: str) -> Optional[list]:
        """Analyze food description using Gemini API with Google Search grounding"""
        prompt = f"""
        Analyze the following food description(s) and provide detailed nutritional information grounded in reliable sources from Google Search.
        
        Food description: "{description}"
        
        If multiple foods are listed, analyze each one separately. Return a JSON array of food objects.
        If only one food is described, return an array with one object.
        
        CRITICAL: For each food, provide BOTH standard serving info AND the user's consumed amount separately:
        
        Please return a JSON response with the following structure:
        [
            {{
                "food_name": "Standardized food name",
                "standard_serving": {{
                    "amount": <standard serving amount as a number>,
                    "unit": "g|ml|cup|tbsp|tsp|oz|lb|kg|piece|slice|medium|large|small",
                    "calories": <calories per standard serving>,
                    "protein_g": <protein in grams per standard serving>,
                    "carbs_g": <carbohydrates in grams per standard serving>,
                    "fat_g": <fat in grams per standard serving>,
                    "fiber_g": <fiber in grams per standard serving>,
                    "sugar_g": <sugar in grams per standard serving>,
                    "sodium_mg": <sodium in milligrams per standard serving>,
                    "potassium_mg": <potassium in milligrams per standard serving>,
                    "vitamin_c_mg": <vitamin C in milligrams per standard serving>,
                    "calcium_mg": <calcium in milligrams per standard serving>,
                    "iron_mg": <iron in milligrams per standard serving>
                }},
                "user_consumed": {{
                    "amount": <amount user actually consumed as a number>,
                    "unit": "g|ml|cup|tbsp|tsp|oz|lb|kg|piece|slice|medium|large|small",
                    "description": "Exact description of what user said they ate"
                }},
                "confidence_score": <confidence from 1-10, where 10 is highest confidence>,
                "source_notes": "Brief note about data sources and any assumptions made"
            }}
        ]
        
        Important guidelines:
        - Use Google Search to find accurate, up-to-date nutrition information
        - Provide standardized food names that would be consistent across queries
        - For standard_serving: Use typical/official serving sizes (e.g., 100g for chicken, 1 cup for milk, 1 medium for banana)
        - For user_consumed: Extract exactly what the user said they ate, preserving their units and amounts
        - Use 'g' for solids, 'ml' for liquids, or appropriate volume/count units
        - The system will handle conversions and scaling calculations after parsing
        
        CRITICAL - Confidence scoring (1-10):
        - 9-10: Very specific foods with reliable data (e.g., "160g grilled chicken breast", "1 large egg")
        - 7-8: Good specificity with solid data (e.g., "100g salmon fillet", "1 cup whole milk")
        - 5-6: Reasonable estimates for moderately specific foods
        - 3-4: Rough estimates for ambiguous foods (e.g., "chicken" could be fried/grilled/nuggets)
        - 1-2: Very uncertain - extremely vague or nonsensical input
        
        AMBIGUITY DETECTION - Use LOW confidence (≤4) for vague inputs like:
        - "chicken" (could be fried, grilled, breast, thigh, nuggets, etc.)
        - "fish" (species and preparation method unknown)
        - "pasta" (type, sauce, and preparation unknown)
        - "bread" (white/wheat/sourdough, size unknown)
        
        - If the food description is ambiguous, make reasonable assumptions and note them in source_notes
        - For branded products, try to find the specific product's nutrition facts
        - Return only valid JSON, no additional text
        """
        
        start_time = time.time()
        request_data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        response_data = {}
        error_msg = None
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            duration = time.time() - start_time
            
            # Extract JSON from response (handle potential markdown formatting)
            # Look for array format first, then fallback to object format
            array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            object_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if array_match:
                json_str = array_match.group(0)
                data = json.loads(json_str)
                response_data = data
                
                # Write trace if enabled
                self._write_trace(description, request_data, response_data, duration)
                
                # Return the array of food dictionaries with new two-part structure
                foods = []
                for i, item in enumerate(data):
                    try:
                        # Extract standard serving info
                        standard = item.get('standard_serving', {})
                        user_consumed = item.get('user_consumed', {})
                        
                        foods.append({
                            'food_name': item.get('food_name', ''),
                            'standard_serving': {
                                'amount': float(standard.get('amount') or 0),
                                'unit': standard.get('unit', 'g'),
                                'calories': float(standard.get('calories') or 0),
                                'protein_g': float(standard.get('protein_g') or 0),
                                'carbs_g': float(standard.get('carbs_g') or 0),
                                'fat_g': float(standard.get('fat_g') or 0),
                                'fiber_g': float(standard.get('fiber_g') or 0),
                                'sugar_g': float(standard.get('sugar_g') or 0),
                                'sodium_mg': float(standard.get('sodium_mg') or 0),
                                'potassium_mg': float(standard.get('potassium_mg') or 0),
                                'vitamin_c_mg': float(standard.get('vitamin_c_mg') or 0),
                                'calcium_mg': float(standard.get('calcium_mg') or 0),
                                'iron_mg': float(standard.get('iron_mg') or 0)
                            },
                            'user_consumed': {
                                'amount': float(user_consumed.get('amount') or 0),
                                'unit': user_consumed.get('unit', 'g'),
                                'description': user_consumed.get('description', '')
                            },
                            'confidence_score': float(item.get('confidence_score') or 1),
                            'source_notes': item.get('source_notes', '')
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Error parsing food item {i+1}: {e}")
                        print(f"Item data: {item}")
                        # Skip this item and continue
                        continue
                
                # Save results for CSV export

                return foods
            elif object_match:
                # Fallback for single object responses - wrap in array
                json_str = object_match.group(0)
                data = json.loads(json_str)
                response_data = [data]  # Wrap single object in array for consistent logging
                
                # Write trace if enabled
                self._write_trace(description, request_data, response_data, duration)
                
                # Return single food wrapped in array with new schema
                try:
                    standard = data.get('standard_serving', {})
                    user_consumed = data.get('user_consumed', {})
                    
                    foods = [{
                        'food_name': data.get('food_name', ''),
                        'standard_serving': {
                            'amount': float(standard.get('amount') or 0),
                            'unit': standard.get('unit', 'g'),
                            'calories': float(standard.get('calories') or 0),
                            'protein_g': float(standard.get('protein_g') or 0),
                            'carbs_g': float(standard.get('carbs_g') or 0),
                            'fat_g': float(standard.get('fat_g') or 0),
                            'fiber_g': float(standard.get('fiber_g') or 0),
                            'sugar_g': float(standard.get('sugar_g') or 0),
                            'sodium_mg': float(standard.get('sodium_mg') or 0),
                            'potassium_mg': float(standard.get('potassium_mg') or 0),
                            'vitamin_c_mg': float(standard.get('vitamin_c_mg') or 0),
                            'calcium_mg': float(standard.get('calcium_mg') or 0),
                            'iron_mg': float(standard.get('iron_mg') or 0)
                        },
                        'user_consumed': {
                            'amount': float(user_consumed.get('amount') or 0),
                            'unit': user_consumed.get('unit', 'g'),
                            'description': user_consumed.get('description', '')
                        },
                        'confidence_score': float(data.get('confidence_score') or 1),
                        'source_notes': data.get('source_notes', '')
                    }]
                except (ValueError, TypeError) as e:
                    print(f"Warning: Error parsing single food item: {e}")
                    print(f"Item data: {data}")
                    return None
                
                # Save results for CSV export

                return foods
            else:
                error_msg = f"Could not extract JSON from response: {response_text}"
                duration = time.time() - start_time
                self._write_trace(description, request_data, {"raw_response": response_text}, duration, error_msg)
                print(f"Error: {error_msg}")
                return None
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self._write_trace(description, request_data, {}, duration, error_msg)
            print(f"Error analyzing food with Gemini: {e}")
            return None


def main():
    """Thin CLI interface - delegates all business logic to FoodLoggerService"""
    import sys
    from .food_logger_service import FoodLoggerService
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python -m src.food_logger 'food description' [--csv] [--sheets]")
        print("Example: python -m src.food_logger '160g grilled chicken breast'")
        print("Multi-food: python -m src.food_logger 'Turkey 121g, Core Power 26g, 2 bananas'")
        print("With CSV: python -m src.food_logger 'Turkey 121g, Core Power 26g' --csv")
        print("With Sheets: python -m src.food_logger 'Turkey 121g, Core Power 26g' --sheets")
        return 1
    
    food_description = sys.argv[1]
    export_csv = '--csv' in sys.argv or True  # Always export CSV for now
    log_sheets = '--sheets' in sys.argv
    
    # Delegate to core service
    try:
        service = FoodLoggerService()
        analysis = service.process_meal(food_description, export_csv=export_csv, log_sheets=log_sheets)
        
        if analysis:
            # Display results (formatting handled by service)
            print(service.format_console_output(analysis))
            return 0
        else:
            print("❌ Failed to analyze meal")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
