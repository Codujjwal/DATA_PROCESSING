import pandas as pd
import numpy as np
from typing import Union
from multiprocessing import Pool, cpu_count
from functools import partial

class DataCleaner:
    def __init__(self):
        self.cleaning_log = []
        self.num_processes = max(1, cpu_count() - 1)  # Leave one core free

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all cleaning operations to the DataFrame"""
        if df.empty:
            return df

        df = self._remove_empty_rows(df)
        df = self._standardize_numbers(df)
        df = self._handle_missing_values(df)

        return df

    def _remove_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows with all empty values"""
        return df.dropna(how='all')

    def _standardize_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize numerical formats"""
        # Process all columns that might contain numeric values
        for col in df.columns:
            if any(term in col.lower() for term in ['value', 'total', '202', 'pct', 'percent']):
                if df[col].dtype in ['object', 'string']:
                    # Choose appropriate cleaning function based on column type
                    if 'pct' in col.lower() or 'percent' in col.lower():
                        df[col] = df[col].apply(self._clean_percentage)
                    else:
                        df[col] = df[col].apply(self._clean_numeric)

                # Convert to numeric, coercing errors to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')

                # Round to reasonable precision (6 decimal places)
                df[col] = df[col].round(6)

        return df

    def _clean_numeric(self, value: Union[str, float, int]) -> float:
        """Clean individual numeric values"""
        if pd.isna(value):
            return np.nan

        if isinstance(value, (int, float)):
            return float(value)

        # Remove currency symbols and other non-numeric characters
        value = str(value).replace('$', '').replace(',', '')
        value = value.strip()

        # Handle parentheses for negative numbers
        if '(' in value and ')' in value:
            value = '-' + value.replace('(', '').replace(')', '')

        try:
            return float(value)
        except ValueError:
            return np.nan

    def _clean_percentage(self, value: Union[str, float, int]) -> float:
        """Clean percentage values"""
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        # Remove % symbol and clean
        value = str(value).replace('%', '').strip()

        # Handle parentheses for negative percentages
        if '(' in value and ')' in value:
            value = '-' + value.replace('(', '').replace(')', '')

        try:
            return float(value)
        except ValueError:
            return 0.0

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values appropriately"""
        # Fill missing percentages with 0
        percentage_cols = [col for col in df.columns if 'percent' in col.lower() or 'pct' in col.lower()]
        for col in percentage_cols:
            df[col] = df[col].fillna(0)

        # Log missing values
        missing_values = df.isnull().sum()
        if missing_values.any():
            self.cleaning_log.append({
                'action': 'handle_missing_values',
                'missing_counts': missing_values.to_dict()
            })

        return df

    def get_cleaning_log(self) -> list:
        """Return the cleaning operation log"""
        return self.cleaning_log