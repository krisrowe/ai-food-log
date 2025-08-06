"""
Google Sheets API Client for Food Database
"""

import os
from datetime import datetime
from typing import Optional, Tuple, List
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from .core import FoodData, FoodDatabase, ConsumptionEntry


class SheetsClient(FoodDatabase):
    """Real Google Sheets API client implementation"""
    
    def __init__(self, sheets_id: str = None, credentials_path: str = None):
        self.sheets_id = sheets_id or os.getenv('GOOGLE_SHEETS_ID')
        if not self.sheets_id:
            raise ValueError("GOOGLE_SHEETS_ID environment variable or sheets_id parameter is required")
        
        creds_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS must point to a valid service account key file")
        
        credentials = Credentials.from_service_account_file(
            creds_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=credentials)
        
        # Sheet tab names
        self.FOODS_TAB = "Foods"
        self.LOG_TAB = "Food Log"
        
        # Initialize sheets if they don't exist
        self._initialize_sheets()
    
    def _initialize_sheets(self):
        """Initialize sheet tabs with headers if they don't exist"""
        try:
            # Check if Foods tab exists and has headers
            foods_data = self._get_sheet_data(self.FOODS_TAB)
            if not foods_data:
                foods_headers = [
                    'food_id', 'food_name', 'serving_size', 'serving_size_grams',
                    'calories_per_serving', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g',
                    'sugar_g', 'sodium_mg', 'potassium_mg', 'calcium_mg', 'iron_mg',
                    'vitamin_c_mg', 'confidence', 'source_notes', 'created_date'
                ]
                self._append_to_sheet(self.FOODS_TAB, [foods_headers])
            
            # Check if Food Log tab exists and has headers
            log_data = self._get_sheet_data(self.LOG_TAB)
            if not log_data:
                log_headers = [
                    'log_id', 'date', 'time', 'food_id', 'food_name', 'description',
                    'servings', 'actual_grams', 'calories', 'protein_g', 'carbs_g',
                    'fat_g', 'fiber_g'
                ]
                self._append_to_sheet(self.LOG_TAB, [log_headers])
                
        except Exception as e:
            print(f"Warning: Could not initialize sheets: {e}")
    
    def _get_sheet_data(self, tab_name: str) -> List[List]:
        """Get all data from a specific sheet tab"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_id,
                range=f"{tab_name}!A:Z"
            ).execute()
            return result.get('values', [])
        except Exception as e:
            print(f"Error reading sheet {tab_name}: {e}")
            return []
    
    def _append_to_sheet(self, tab_name: str, values: List[List]):
        """Append rows to a specific sheet tab"""
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheets_id,
                range=f"{tab_name}!A:Z",
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
        except Exception as e:
            print(f"Error appending to sheet {tab_name}: {e}")
    
    def find_food(self, food_name: str) -> Optional[Tuple[str, FoodData]]:
        """Find existing food by name, return (food_id, food_data) if found"""
        foods_data = self._get_sheet_data(self.FOODS_TAB)
        if not foods_data or len(foods_data) < 2:  # Need at least headers + 1 row
            return None
        
        headers = foods_data[0]
        
        for row in foods_data[1:]:  # Skip header row
            if row and len(row) > 1:
                existing_name = row[1].lower().strip()  # food_name is column 1
                if existing_name == food_name.lower().strip():
                    # Convert row to FoodData
                    food_data = self._row_to_food_data(headers, row)
                    if food_data:
                        return row[0], food_data  # food_id is column 0
        
        return None
    
    def _row_to_food_data(self, headers: List[str], row: List[str]) -> Optional[FoodData]:
        """Convert sheet row to FoodData object"""
        try:
            # Create dict from headers and row
            data = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    data[header] = row[i]
            
            return FoodData(
                food_name=data.get('food_name', ''),
                serving_size=data.get('serving_size', ''),
                serving_size_grams=float(data.get('serving_size_grams', 100)),
                calories_per_serving=float(data.get('calories_per_serving', 0)),
                protein_g=float(data.get('protein_g', 0)),
                carbs_g=float(data.get('carbs_g', 0)),
                fat_g=float(data.get('fat_g', 0)),
                fiber_g=float(data.get('fiber_g', 0)),
                sugar_g=float(data.get('sugar_g', 0)),
                sodium_mg=float(data.get('sodium_mg', 0)),
                potassium_mg=float(data.get('potassium_mg', 0)),
                calcium_mg=float(data.get('calcium_mg', 0)),
                iron_mg=float(data.get('iron_mg', 0)),
                vitamin_c_mg=float(data.get('vitamin_c_mg', 0)),
                confidence=data.get('confidence', 'medium'),
                source_notes=data.get('source_notes', '')
            )
        except (ValueError, KeyError) as e:
            print(f"Error converting row to FoodData: {e}")
            return None
    
    def save_food(self, food_data: FoodData) -> str:
        """Save new food to database, return food_id"""
        foods_data = self._get_sheet_data(self.FOODS_TAB)
        food_id = f"food_{len(foods_data)}"  # Simple ID generation
        
        row_data = [
            food_id,
            food_data.food_name,
            food_data.serving_size,
            food_data.serving_size_grams,
            food_data.calories_per_serving,
            food_data.protein_g,
            food_data.carbs_g,
            food_data.fat_g,
            food_data.fiber_g,
            food_data.sugar_g,
            food_data.sodium_mg,
            food_data.potassium_mg,
            food_data.calcium_mg,
            food_data.iron_mg,
            food_data.vitamin_c_mg,
            food_data.confidence,
            food_data.source_notes,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        self._append_to_sheet(self.FOODS_TAB, [row_data])
        return food_id
    
    def log_consumption(self, entry: ConsumptionEntry) -> None:
        """Log consumption entry to database"""
        row_data = [
            entry.log_id,
            entry.date,
            entry.time,
            entry.food_id,
            entry.food_name,
            entry.description,
            entry.nutrition.servings,
            entry.nutrition.actual_grams,
            entry.nutrition.calories,
            entry.nutrition.protein_g,
            entry.nutrition.carbs_g,
            entry.nutrition.fat_g,
            entry.nutrition.fiber_g
        ]
        
        self._append_to_sheet(self.LOG_TAB, [row_data])
