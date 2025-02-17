import pandas as pd
import numpy as np
from typing import List, Dict

class DataValidator:
    def __init__(self, operations_df=None, cash_flow_df=None, debt_df=None):
        self.operations_df = operations_df
        self.cash_flow_df = cash_flow_df
        self.debt_df = debt_df
        self.validation_results = []

    def validate_all(self) -> List[Dict]:
        """Run all validation checks"""
        if all(df is None or df.empty for df in [self.operations_df, self.cash_flow_df, self.debt_df]):
            self.validation_results.append({
                'type': 'error',
                'message': 'No data available for validation'
            })
            return self.validation_results

        # Validate year-over-year changes
        if self.operations_df is not None and not self.operations_df.empty:
            self.check_year_over_year()

        # Validate cash flow data
        if self.cash_flow_df is not None and not self.cash_flow_df.empty:
            self.check_cash_flow_consistency()

        # Validate debt obligations
        if self.debt_df is not None and not self.debt_df.empty:
            self.check_debt_obligations()

        return self.validation_results

    def check_year_over_year(self) -> None:
        """Validate year-over-year changes with improved tolerance for rounding differences"""
        if not {'value_2022', 'value_2021', 'change_pct'}.issubset(self.operations_df.columns):
            return

        for _, row in self.operations_df.iterrows():
            if pd.notnull(row['value_2022']) and pd.notnull(row['value_2021']) and pd.notnull(row['change_pct']):
                if row['value_2021'] != 0:
                    calc_change = ((row['value_2022'] - row['value_2021']) / row['value_2021'] * 100)
                    calc_change = round(calc_change, 1)
                    reported_change = float(row['change_pct'])

                    # Use a more lenient tolerance for comparison (0.5% difference)
                    if not np.isclose(calc_change, reported_change, rtol=0.005, atol=0.5):
                        self.validation_results.append({
                            'type': 'yoy_change_mismatch',
                            'category': row.get('category', 'Unknown'),
                            'calculated': calc_change,
                            'reported': reported_change
                        })

    def check_cash_flow_consistency(self) -> None:
        """Validate cash flow statement consistency"""
        if not {'category', 'value_2022', 'value_2021'}.issubset(self.cash_flow_df.columns):
            return

        for year in ['2022', '2021']:
            col = f'value_{year}'
            operating = self.cash_flow_df[
                self.cash_flow_df['category'].str.contains('operating', case=False, na=False)
            ][col].sum()

            investing = self.cash_flow_df[
                self.cash_flow_df['category'].str.contains('investing', case=False, na=False)
            ][col].sum()

            before_financing = self.cash_flow_df[
                self.cash_flow_df['category'].str.contains('before financing', case=False, na=False)
            ][col].iloc[0] if any(self.cash_flow_df['category'].str.contains('before financing', case=False, na=False)) else None

            if before_financing is not None:
                calc_total = operating + investing
                if not np.isclose(calc_total, before_financing, rtol=0.01):
                    self.validation_results.append({
                        'type': 'cash_flow_mismatch',
                        'year': year,
                        'calculated': round(calc_total, 2),
                        'reported': round(before_financing, 2)
                    })

    def check_debt_obligations(self) -> None:
        """Validate debt obligations data"""
        if 'total' not in self.debt_df.columns:
            return

        years = [col for col in self.debt_df.columns 
                if col not in ['category', 'total'] and col.isdigit()]

        for _, row in self.debt_df.iterrows():
            yearly_sum = sum(row.get(year, 0) for year in years)
            if not np.isclose(yearly_sum, row['total'], rtol=0.01):
                self.validation_results.append({
                    'type': 'debt_total_mismatch',
                    'category': row.get('category', 'Unknown'),
                    'calculated': round(yearly_sum, 2),
                    'reported': round(row['total'], 2)
                })