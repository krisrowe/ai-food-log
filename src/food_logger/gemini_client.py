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
from .core import FoodData, FoodAnalyzer


class GeminiClient(FoodAnalyzer):
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
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
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
                    else:
                        f.write(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                f.write("=" * 80 + "\n")
        except Exception as e:
            # Don't let tracing errors break the main functionality
            print(f"Warning: Failed to write trace: {e}")
    
    def analyze_food(self, description: str) -> Optional[FoodData]:
        """Analyze food description using Gemini API with Google Search grounding"""
        prompt = f"""
        Analyze the following food description and provide detailed nutritional information grounded in reliable sources from Google Search.
        
        Food description: "{description}"
        
        Please return a JSON response with the following structure:
        {{
            "food_name": "Standardized food name",
            "serving_amount": <serving amount as a number>,
            "serving_unit": "g|ml|cup|tbsp|tsp|oz|lb|kg|piece|slice|medium|large|small",
            "calories_per_serving": <calories per serving as a number>,
            "protein_g": <protein in grams as a number>,
            "carbs_g": <carbohydrates in grams as a number>,
            "fat_g": <fat in grams as a number>,
            "fiber_g": <fiber in grams as a number>,
            "sugar_g": <sugar in grams as a number>,
            "sodium_mg": <sodium in milligrams as a number>,
            "potassium_mg": <potassium in milligrams as a number>,
            "vitamin_c_mg": <vitamin C in milligrams as a number>,
            "calcium_mg": <calcium in milligrams as a number>,
            "iron_mg": <iron in milligrams as a number>,
            "confidence_score": <confidence from 1-10, where 10 is highest confidence>,
            "source_notes": "Brief note about data sources and any assumptions made"
        }}
        
        Important guidelines:
        - Use Google Search to find accurate, up-to-date nutrition information
        - Provide standardized food names that would be consistent across queries
        - Split serving size into amount (number) and unit (enum from list above)
        - Use 'g' for solids, 'ml' for liquids, or appropriate volume/count units
        - Score confidence 1-10: 9-10=very reliable data, 7-8=good data, 5-6=reasonable estimates, 3-4=rough estimates, 1-2=very uncertain
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
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                response_data = data
                
                # Write trace if enabled
                self._write_trace(description, request_data, response_data, duration)
                
                # Return the raw JSON dictionary with validated structure
                return {
                    'food_name': data.get('food_name', ''),
                    'serving_amount': float(data.get('serving_amount', 0)),
                    'serving_unit': data.get('serving_unit', 'g'),
                    'calories_per_serving': float(data.get('calories_per_serving', 0)),
                    'protein_g': float(data.get('protein_g', 0)),
                    'carbs_g': float(data.get('carbs_g', 0)),
                    'fat_g': float(data.get('fat_g', 0)),
                    'fiber_g': float(data.get('fiber_g', 0)),
                    'sugar_g': float(data.get('sugar_g', 0)),
                    'sodium_mg': float(data.get('sodium_mg', 0)),
                    'potassium_mg': float(data.get('potassium_mg', 0)),
                    'vitamin_c_mg': float(data.get('vitamin_c_mg', 0)),
                    'calcium_mg': float(data.get('calcium_mg', 0)),
                    'iron_mg': float(data.get('iron_mg', 0)),
                    'confidence_score': float(data.get('confidence_score', 1)),
                    'source_notes': data.get('source_notes', '')
                }
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
