import pandas as pd
import numpy as np
from typing import Dict, List, Union, Tuple
import re
from .utils import convert_currency, parse_percentage

class FinancialDataParser:
    def __init__(self):
        self.data_frame = None
        self.cash_flow_frame = None
        self.debt_obligations_frame = None

    def parse_financial_statement(self, content: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Parse financial statement content into structured DataFrames"""
        sections = self._split_into_sections(content)

        # Parse each section
        operations_df = self._parse_operations_section(sections.get('operations', ''))
        cash_flow_df = self._parse_cash_flow_section(sections.get('cash_flow', ''))
        debt_df = self._parse_debt_obligations_section(sections.get('debt_obligations', ''))

        return operations_df, cash_flow_df, debt_df

    def _split_into_sections(self, content: str) -> Dict[str, str]:
        """Split the content into major sections based on headers"""
        lines = content.split('\n')
        sections = {'operations': [], 'cash_flow': [], 'debt_obligations': []}
        current_section = 'operations'

        for line in lines:
            if 'Net cash' in line:
                current_section = 'cash_flow'
            elif 'Debt obligations' in line:
                current_section = 'debt_obligations'
            sections[current_section].append(line)

        return {k: '\n'.join(v) for k, v in sections.items()}

    def _parse_operations_section(self, content: str) -> pd.DataFrame:
        """Parse the operations metrics section"""
        lines = content.split('\n')
        data = []
        current_section = None

        print("Parsing operations section...")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip header lines
            if any(header in line for header in [
                'Three months ended March 31',
                'Three months ended',
                'Fav (Unfav)',
                'currency',
                'In millions'
            ]) or ('2022' in line and '2021' in line):
                continue

            # Identify section headers
            if any(keyword in line for keyword in ['Revenues', 'RTMs', 'Carloads', 'revenue']):
                current_section = line.strip()
                print(f"Found section: {current_section}")
                continue

            # Skip rows that look like section headers or totals
            if 'Total' in line and any(word in line for word in ['freight', 'revenues', 'RTMs', 'carloads']):
                continue

            # Parse data rows
            parts = [p.strip() for p in re.split(r'\t|\s{2,}', line) if p.strip()]

            if len(parts) >= 3:
                try:
                    category = parts[0]
                    value_2022 = self._parse_value(parts[1])
                    value_2021 = self._parse_value(parts[2])

                    # Only process rows with valid numeric data
                    if value_2022 != 0.0 or value_2021 != 0.0:
                        row_data = {
                            'section': current_section or '',
                            'category': category,
                            'value_2022': value_2022,
                            'value_2021': value_2021
                        }

                        # Parse change percentage if available
                        if len(parts) > 3:
                            change_pct = parse_percentage(''.join(parts[3:]))  # Combine remaining parts for percentage
                            row_data['change_pct'] = change_pct

                        print(f"Parsed operations row: {category}")
                        data.append(row_data)

                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not parse operations line: '{line}' - Error: {str(e)}")
                    continue

        return pd.DataFrame(data) if data else pd.DataFrame()

    def _parse_cash_flow_section(self, content: str) -> pd.DataFrame:
        """Parse the cash flow section"""
        print("Parsing cash flow section...")
        lines = content.split('\n')
        data = []

        for line in lines:
            line = line.strip()
            if not line or any(skip in line for skip in ['Three months ended', 'In millions', 'Adjustment:']):
                continue

            try:
                # Extract category and values
                category_match = re.match(r'^(.*?)(?=\$|\d|\()', line)
                if not category_match:
                    continue

                category = category_match.group(1).strip()
                values = re.findall(r'\$?\s*-?\(?\d[\d,]*\)?', line)

                if len(values) >= 2 and category:
                    value_2022 = convert_currency(values[0])
                    value_2021 = convert_currency(values[1])

                    print(f"Parsed cash flow row: {category}")
                    data.append({
                        'category': category,
                        'value_2022': value_2022,
                        'value_2021': value_2021
                    })
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse cash flow line: '{line}' - Error: {str(e)}")
                continue

        return pd.DataFrame(data) if data else pd.DataFrame()

    def _parse_debt_obligations_section(self, content: str) -> pd.DataFrame:
        """Parse the debt obligations section"""
        print("Parsing debt obligations section...")
        lines = content.split('\n')
        data = []
        years = ['2022', '2023', '2024', '2025', '2026', '2027 & thereafter']

        for line in lines:
            line = line.strip()
            if (not line or 
                'In millions' in line or 
                'Total contractual obligations' in line or
                all(str(year) in line for year in range(2022, 2025))):
                continue

            parts = [p.strip() for p in re.split(r'\t|\s{2,}', line) if p.strip()]

            if len(parts) >= 2 and not parts[0].startswith('20'):  # Skip year headers
                try:
                    category = parts[0]
                    if category == 'Total':
                        continue

                    # Extract the numeric values
                    numeric_values = []
                    for part in parts[1:]:
                        if part and (part.replace(',', '').replace('.', '').isdigit() or 
                                   (part.startswith('(') and part.endswith(')'))):
                            numeric_values.append(convert_currency(part))

                    if len(numeric_values) >= 1:
                        values = {
                            'category': category,
                            'total': numeric_values[0]
                        }

                        # Add values for each year
                        for i, year in enumerate(years):
                            values[year] = numeric_values[i + 1] if i + 1 < len(numeric_values) else 0.0

                        print(f"Parsed debt obligations row: {category}")
                        data.append(values)

                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not parse debt obligations line: '{line}' - Error: {str(e)}")
                    continue

        return pd.DataFrame(data) if data else pd.DataFrame()

    def _parse_value(self, value: str) -> float:
        """Parse numerical values, handling parentheses for negative numbers"""
        if not value or value.isspace():
            return 0.0
        value = value.replace(',', '').strip()
        if '(' in value and ')' in value:
            return -float(value.replace('(', '').replace(')', ''))
        return float(value) if value != '—' else 0.0