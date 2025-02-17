import pandas as pd
import numpy as np
from typing import Union

class DataCleaner:
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the DataFrame by removing empty rows and standardizing numbers"""
        if df.empty:
            return df

        # Remove empty rows
        df = df.dropna(how='all')

        # Clean numeric columns
        value_cols = [col for col in df.columns if any(term in col.lower() for term in ['value', 'total', '202'])]
        for col in value_cols:
            if df[col].dtype == object:
                df[col] = df[col].apply(self._clean_numeric)

        # Clean and fill percentage columns
        pct_cols = [col for col in df.columns if 'pct' in col.lower()]
        for col in pct_cols:
            if df[col].dtype == object:
                df[col] = df[col].apply(self._clean_percentage)
            df[col] = df[col].fillna(0)

        return df

    def _clean_numeric(self, value: Union[str, float, int]) -> float:
        """Clean individual numeric values"""
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        # Remove currency symbols and commas
        value = str(value).replace('$', '').replace(',', '').strip()

        # Handle parentheses for negative values
        if '(' in value and ')' in value:
            value = '-' + value.replace('(', '').replace(')', '')

        try:
            return float(value)
        except ValueError:
            return 0.0

    def _clean_percentage(self, value: Union[str, float, int]) -> float:
        """Clean percentage values"""
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        # Remove % symbol and handle parentheses
        value = str(value).replace('%', '').strip()
        if '(' in value and ')' in value:
            value = '-' + value.replace('(', '').replace(')', '')

        try:
            return float(value)
        except ValueError:
            return 0.0