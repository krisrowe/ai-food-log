"""
Gemini API Client for Food Analysis
"""

import os
import json
import time
import configparser
import yaml
from datetime import datetime
from typing import Optional, List, Dict
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from jsonschema import validate, ValidationError
from proto.marshal.collections import maps
from proto.marshal.collections import repeated

class SchemaValidationError(ValueError):
    """Custom exception for schema validation errors."""
    pass

class GeminiClient:
    """Real Gemini API client implementation with tracing and function calling."""
    
    def __init__(self):
        self.config = self._load_config()
        model_name = self.config.get('gemini_model', 'gemini-2.5-flash')
        
        tested_models = ['gemini-2.5-flash', 'gemini-2.5-pro']
        if model_name not in tested_models:
            raise ValueError(
                f"Invalid Gemini model '{model_name}' in config.yaml. "
                f"Please use one of the tested models: {tested_models}"
            )

        self.schema = self._load_schema('food_analysis_response.json')
        tool_schema = self._load_schema('food_analysis_response.gemini.json')
        
        log_food_data_declaration = FunctionDeclaration(
            name="log_food_data",
            description="Logs a list of food items with their nutritional information.",
            parameters=tool_schema,
        )
        
        food_tool = Tool(function_declarations=[log_food_data_declaration])

        self.model = genai.GenerativeModel(
            model_name,
            tools=[food_tool]
        )
        
        print(f"Using Gemini model: {model_name}")
        self.trace_enabled = self.config.get('logging', {}).get('enable_ai_api_trace', False)

    def _load_schema(self, filename: str) -> dict:
        """Load a schema from file."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schemas', filename)
            with open(schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"API response schema '{filename}' not found.")
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse API response schema '{filename}'.")

    

    def _load_config(self) -> dict:
        """Load configuration from config.yaml"""
        try:
            with open('config.yaml', 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    
    def _write_trace(self, input_text: str, request_data: dict, response_data: dict, duration: float, error: str = None):
        """Write human-readable trace to ai_api_trace.log"""
        # ... (implementation remains the same)
    
    def _convert_proto_map_to_dict(self, proto_map_or_list):
        """Recursively convert a proto MapComposite or list to a standard Python dict or list."""
        if isinstance(proto_map_or_list, maps.MapComposite):
            return {k: self._convert_proto_map_to_dict(v) for k, v in proto_map_or_list.items()}
        elif isinstance(proto_map_or_list, repeated.RepeatedComposite):
            return [self._convert_proto_map_to_dict(v) for v in proto_map_or_list]
        else:
            return proto_map_or_list

    def analyze_food(self, description: str) -> Optional[List[Dict]]:
        """
        Analyze food description and return structured data using function calling.
        
        Raises:
            SchemaValidationError: If the API response does not conform to the schema.
        """
        prompt = f"""
        Analyze the food description below. Your task is to structure the information for each food item identified.

        Food description: "{description}"
        
        CRITICAL GUIDELINES:
        - For each food item, you MUST populate the `user_description` field. This field should contain the exact substring from the user's original prompt that corresponds to that specific food item.
        - For food_name: 
          - Your primary goal is to identify and return a standardized food name. It is critical that you use a consistent naming approach that is likely to yield the same result every time for the same food.
          - If the food is a packaged product, use its official product name (e.g., "Six Star Pro Nutrition 100% Whey Protein Plus").
          - If the food is a generic item, use a clear and common name (e.g., "Apple", "Grilled Chicken Breast").
          - Do NOT simply echo the user's input.
        - For standard_serving:
          - The `size` field MUST represent the most precise measurement available, in order of preference: weight (g, oz), volume (ml, tbsp), then discrete units (cookies, pieces).
          - The `alt_size` field MAY be used for a secondary, less precise measurement if available.
          - The `nutrition` object and its required fields (`calories`, `protein`, 'carbs', `fat`) MUST always be returned.
        - For consumed:
          - Parse the user's text into a structured `size` object.
          - CRITICAL: If the user specifies a number of 'servings', you MUST resolve this. Multiply that number by the `standard_serving.size` and return the result.
        - For servings:
          - Set `calculable` to `true` ONLY if `consumed.size.unit` is logically compatible with a unit in `standard_serving`.
          - If `calculable` is `false`, provide a reasonable estimate in the `guess` field.
          - If `calculable` is `true`, OMIT the `guess` field entirely.
        - Confidence Scoring:
          - Your confidence score MUST be an integer between 1 (lowest) and 10 (highest), reflecting your certainty about the food item match and the `calculable` flag.
        """
        
        start_time = time.time()
        request_data = {"contents": [{"parts": [{"text": prompt}]}]}
        response_data = {}
        error_msg = None
        
        try:
            response = self.model.generate_content(prompt)
            
            if not response.candidates:
                print("--- MODEL RESPONSE ERROR: NO CANDIDATES ---")
                print(response)
                print("-------------------------------------------")
                raise ValueError("The model returned no candidates. This may be due to a safety block or an issue with the prompt. See details above.")

            candidate = response.candidates[0]
            if not candidate.content.parts:
                error_details = f"Finish Reason: {candidate.finish_reason.name if candidate.finish_reason else 'N/A'}. " \
                              f"Safety Ratings: {[str(rating) for rating in candidate.safety_ratings]}"
                raise ValueError(f"The model returned a candidate with no content parts. Details: {error_details}")

            response_part = candidate.content.parts[0]
            
            if not response_part.function_call or response_part.function_call.name != "log_food_data":
                raise ValueError("Model did not call the expected function.")
            
            raw_args = response_part.function_call.args
            
            converted_items = self._convert_proto_map_to_dict(raw_args.get('items', []))

            validate(instance=converted_items, schema=self.schema)
            
            response_data = {'items': converted_items}
            return converted_items
            
        except (ValidationError, ValueError) as e:
            error_msg = f"API response validation failed: {e}"
            # We still print for debugging, but now we raise a specific exception
            print(error_msg)
            raise SchemaValidationError(error_msg) from e
        finally:
            duration = time.time() - start_time
            # Note: error_msg will only be set for handled exceptions now.
            # Unhandled exceptions will propagate before this is set.
            self._write_trace(description, request_data, response_data, duration, error_msg)