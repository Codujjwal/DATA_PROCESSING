import unittest
import pandas as pd
import numpy as np
from financial_parser import FinancialDataParser, DataValidator, DataCleaner

class TestFinancialParser(unittest.TestCase):
    def setUp(self):
        self.parser = FinancialDataParser()
        self.sample_data = """
        Three months ended March 31
        2022    2021    % Change
        Revenues ($ millions)
        Petroleum and chemicals    756     661     14  %
        Metals and minerals       406     368     10  %

        Net cash provided by operating activities    $   570     $   952    
        Net cash used in investing activities    (101)       (413)   
        Net cash provided before financing activities     469         539    

        Debt obligations
        Total       2022        2023        2024
        Interest on debt    9,056     328     483     476
        """

    def test_parse_financial_statement(self):
        operations_df, cash_flow_df, debt_df = self.parser.parse_financial_statement(self.sample_data)

        # Test operations data
        self.assertIsInstance(operations_df, pd.DataFrame)
        self.assertTrue('value_2022' in operations_df.columns)
        self.assertTrue('value_2021' in operations_df.columns)
        self.assertEqual(len(operations_df), 2)  # Two operation entries

        # Test cash flow data
        self.assertIsInstance(cash_flow_df, pd.DataFrame)
        self.assertEqual(len(cash_flow_df), 3)  # Three cash flow entries
        self.assertTrue(all(col in cash_flow_df.columns for col in ['category', 'value_2022', 'value_2021']))

        # Test debt obligations data
        self.assertIsInstance(debt_df, pd.DataFrame)
        self.assertTrue(all(year in debt_df.columns for year in ['2022', '2023', '2024']))
        self.assertEqual(len(debt_df), 1)  # One debt obligation entry

    def test_cash_flow_parsing(self):
        _, cash_flow_df, _ = self.parser.parse_financial_statement(self.sample_data)
        self.assertEqual(cash_flow_df['value_2022'].iloc[0], 570.0)  # Operating activities
        self.assertEqual(cash_flow_df['value_2022'].iloc[1], -101.0)  # Investing activities
        self.assertEqual(cash_flow_df['value_2022'].iloc[2], 469.0)  # Before financing

    def test_debt_obligations_parsing(self):
        _, _, debt_df = self.parser.parse_financial_statement(self.sample_data)
        self.assertEqual(debt_df['total'].iloc[0], 9056.0)
        self.assertEqual(debt_df['2022'].iloc[0], 328.0)
        self.assertEqual(debt_df['2023'].iloc[0], 483.0)
        self.assertEqual(debt_df['2024'].iloc[0], 476.0)

    def test_operations_parsing(self):
        operations_df, _, _ = self.parser.parse_financial_statement(self.sample_data)
        self.assertEqual(operations_df['value_2022'].iloc[0], 756.0)
        self.assertEqual(operations_df['value_2021'].iloc[0], 661.0)
        self.assertEqual(operations_df['change_pct'].iloc[0], 14.0)

class TestDataValidator(unittest.TestCase):
    def setUp(self):
        # Create sample DataFrames for validation
        self.operations_df = pd.DataFrame({
            'section': ['Revenues', 'Revenues', 'Revenues'],
            'category': ['Item 1', 'Item 2', 'Total'],
            'value_2022': [100, 200, 300],
            'value_2021': [90, 180, 270],
            'change_pct': [11.11, 11.11, 11.11]
        })

        self.cash_flow_df = pd.DataFrame({
            'category': ['Operating', 'Investing', 'Before Financing'],
            'value_2022': [100, -50, 50],
            'value_2021': [90, -40, 50]
        })

        self.validator = DataValidator(self.operations_df, self.cash_flow_df)

    def test_validate_all(self):
        results = self.validator.validate_all()
        self.assertIsInstance(results, list)
        # Validate that there are no errors in our test data
        self.assertEqual(len([r for r in results if r['type'] == 'error']), 0)

class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = DataCleaner()
        self.sample_df = pd.DataFrame({
            'value_2022': ['1,234', '(567)', '$890'],
            'value_2021': ['1,000', '500', '750'],
            'change_pct': ['23.4%', '(13.4%)', '18.7%']
        })

    def test_clean_data(self):
        cleaned_df = self.cleaner.clean_data(self.sample_df)
        self.assertEqual(cleaned_df['value_2022'].iloc[0], 1234.0)
        self.assertEqual(cleaned_df['value_2022'].iloc[1], -567.0)
        self.assertEqual(cleaned_df['value_2022'].iloc[2], 890.0)
        self.assertEqual(cleaned_df['change_pct'].iloc[0], 23.4)
        self.assertEqual(cleaned_df['change_pct'].iloc[1], -13.4)

    def test_handle_missing_values(self):
        df_with_missing = self.sample_df.copy()
        df_with_missing.loc[0, 'change_pct'] = None
        cleaned_df = self.cleaner.clean_data(df_with_missing)
        self.assertEqual(cleaned_df['change_pct'].iloc[0], 0.0)

if __name__ == '__main__':
    unittest.main()