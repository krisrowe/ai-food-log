"""
Google Sheets API Client for Food Database
"""

import os
from datetime import datetime
from typing import Optional, Tuple, List
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
# Legacy imports removed - using new food_logger_service architecture


class SheetsClient:
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
    
    def log_meal_analysis(self, analysis_data: dict) -> bool:
        """Log meal analysis to Google Sheets (placeholder)"""
        # TODO: Implement Google Sheets integration for new architecture
        print("📝 Google Sheets logging not yet implemented")
        return False
