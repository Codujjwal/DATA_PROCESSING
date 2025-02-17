import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

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

        # Validate operations data
        if self.operations_df is not None and not self.operations_df.empty:
            self.check_operations_totals()
            self.check_year_over_year()
            self.check_operations_consistency()

        # Validate cash flow data
        if self.cash_flow_df is not None and not self.cash_flow_df.empty:
            self.check_cash_flow_consistency()

        # Validate debt obligations
        if self.debt_df is not None and not self.debt_df.empty:
            self.check_debt_obligations()

        return self.validation_results

    def check_operations_totals(self) -> None:
        """Validate that operation subtotals match their components"""
        if 'section' not in self.operations_df.columns:
            return

        sections = self.operations_df['section'].unique()
        for section in sections:
            section_data = self.operations_df[self.operations_df['section'] == section]
            total_row = section_data[section_data['category'].str.contains('Total', case=False, na=False)]

            if not total_row.empty:
                component_rows = section_data[~section_data['category'].str.contains('Total', case=False, na=False)]

                for year in ['2022', '2021']:
                    col = f'value_{year}'
                    if col in section_data.columns:
                        calc_total = component_rows[col].sum()
                        reported_total = total_row[col].iloc[0]

                        if not np.isclose(calc_total, reported_total, rtol=1e-2):
                            self.validation_results.append({
                                'type': 'total_mismatch',
                                'section': section,
                                'year': year,
                                'calculated': round(calc_total, 2),
                                'reported': round(reported_total, 2)
                            })

    def check_year_over_year(self) -> None:
        """Validate year-over-year changes match reported percentages"""
        if not {'value_2022', 'value_2021', 'change_pct'}.issubset(self.operations_df.columns):
            return

        for _, row in self.operations_df.iterrows():
            if pd.notnull(row['value_2022']) and pd.notnull(row['value_2021']) and pd.notnull(row['change_pct']):
                if row['value_2021'] != 0:
                    calc_change = ((row['value_2022'] - row['value_2021']) / row['value_2021'] * 100)

                    # Round to one decimal place for comparison
                    calc_change = round(calc_change, 1)
                    reported_change = round(row['change_pct'], 1)

                    if not np.isclose(calc_change, reported_change, rtol=1e-1):
                        self.validation_results.append({
                            'type': 'yoy_change_mismatch',
                            'category': row['category'],
                            'section': row.get('section', ''),
                            'calculated': calc_change,
                            'reported': reported_change
                        })

    def check_operations_consistency(self) -> None:
        """Check for data consistency in operations data"""
        for _, row in self.operations_df.iterrows():
            # Check for negative values in metrics that should be positive
            if row['section'] and any(term in str(row['section']) for term in ['RTMs', 'Carloads']):
                for year in ['2022', '2021']:
                    col = f'value_{year}'
                    if col in self.operations_df.columns and row[col] < 0:
                        self.validation_results.append({
                            'type': 'invalid_negative',
                            'category': row['category'],
                            'section': row['section'],
                            'year': year,
                            'value': row[col]
                        })

    def check_cash_flow_consistency(self) -> None:
        """Validate cash flow statement consistency"""
        if not {'category', 'value_2022', 'value_2021'}.issubset(self.cash_flow_df.columns):
            return

        for year in ['2022', '2021']:
            col = f'value_{year}'

            # Get operating and investing cash flows
            operating = self.cash_flow_df[
                self.cash_flow_df['category'].str.contains('operating', case=False, na=False)
            ][col].sum()

            investing = self.cash_flow_df[
                self.cash_flow_df['category'].str.contains('investing', case=False, na=False)
            ][col].sum()

            # Get reported total before financing
            before_financing = self.cash_flow_df[
                self.cash_flow_df['category'].str.contains('before financing', case=False, na=False)
            ][col].iloc[0] if any(self.cash_flow_df['category'].str.contains('before financing', case=False, na=False)) else None

            if before_financing is not None:
                calc_total = operating + investing
                if not np.isclose(calc_total, before_financing, rtol=1e-2):
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

        years = ['2022', '2023', '2024', '2025', '2026', '2027 & thereafter']
        available_years = [year for year in years if year in self.debt_df.columns]

        for _, row in self.debt_df.iterrows():
            # Verify that sum of years equals total
            yearly_sum = sum(row[year] for year in available_years)
            if not np.isclose(yearly_sum, row['total'], rtol=1e-2):
                self.validation_results.append({
                    'type': 'debt_total_mismatch',
                    'category': row['category'],
                    'calculated': round(yearly_sum, 2),
                    'reported': round(row['total'], 2)
                })

            # Check for negative values
            for col in available_years + ['total']:
                if row[col] < 0 and not any(term in row['category'].lower() for term in ['used', 'liability']):
                    self.validation_results.append({
                        'type': 'negative_debt_value',
                        'category': row['category'],
                        'period': col,
                        'value': row[col]
                    })