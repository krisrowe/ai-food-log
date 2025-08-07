"""
Google Sheets API Client for Food Database
"""

import os
from typing import Optional, List, Dict
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from .models import MealAnalysis

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
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheets_id).execute()
            sheets = [s['properties']['title'] for s in sheet_metadata.get('sheets', '')]

            if self.FOODS_TAB not in sheets:
                self._create_sheet(self.FOODS_TAB, ['food_id', 'food_name', 'serving_size', 'serving_unit', 'calories', 'protein_g', 'carbs_g', 'fat_g'])

            if self.LOG_TAB not in sheets:
                self._create_sheet(self.LOG_TAB, ['log_id', 'timestamp', 'food_id', 'food_name', 'user_consumed_amount', 'user_consumed_unit', 'number_of_servings', 'calories', 'protein_g', 'carbs_g', 'fat_g'])

        except Exception as e:
            print(f"Warning: Could not initialize sheets: {e}")

    def _create_sheet(self, title, headers):
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': title,
                        'gridProperties': {
                            'rowCount': 1,
                            'columnCount': len(headers)
                        }
                    }
                }
            }]
        }
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.sheets_id, body=body).execute()
        self._append_to_sheet(title, [headers])

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

    def find_food(self, food_name: str) -> Optional[Dict]:
        """Find a food by name in the Foods tab"""
        foods_data = self._get_sheet_data(self.FOODS_TAB)
        if not foods_data or len(foods_data) < 2: # Headers + data
            return None
        
        for row in foods_data[1:]:
            if len(row) > 1 and row[1].lower() == food_name.lower():
                return {
                    'food_id': row[0],
                    'food_name': row[1],
                    'serving_size': row[2],
                    'serving_unit': row[3]
                }
        return None

    def add_foods(self, food_rows: List[List]):
        """Add new foods to the Foods tab"""
        foods_data = self._get_sheet_data(self.FOODS_TAB)
        start_id = len(foods_data)
        
        for i, row in enumerate(food_rows):
            row.insert(0, f"F{start_id + i}")

        self._append_to_sheet(self.FOODS_TAB, food_rows)

    def log_meal(self, log_rows: List[List]):
        """Log a meal to the Food Log tab."""
        if log_rows:
            self._append_to_sheet(self.LOG_TAB, log_rows)
