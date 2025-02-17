import pandas as pd
import re
from typing import Tuple
from .utils import convert_currency, parse_percentage

class FinancialDataParser:
    def parse_financial_statement(self, content: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Parse financial statement into structured DataFrames"""
        # Split content into sections
        sections = self._split_into_sections(content)

        # Parse each section
        operations_df = self._parse_operations_section(sections.get('operations', ''))
        cash_flow_df = self._parse_cash_flow_section(sections.get('cash_flow', ''))
        debt_df = self._parse_debt_obligations_section(sections.get('debt_obligations', ''))

        return operations_df, cash_flow_df, debt_df

    def _split_into_sections(self, content: str) -> dict:
        """Split content into major sections"""
        lines = content.split('\n')
        sections = {'operations': [], 'cash_flow': [], 'debt_obligations': []}
        current_section = 'operations'

        for line in lines:
            if 'Net cash' in line:
                current_section = 'cash_flow'
            elif 'Debt obligations' in line or 'Total contractual obligations' in line:
                current_section = 'debt_obligations'
            sections[current_section].append(line)

        return {k: '\n'.join(v) for k, v in sections.items()}

    def _parse_operations_section(self, content: str) -> pd.DataFrame:
        """Parse operations section"""
        lines = content.split('\n')
        data = []
        header_found = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if not header_found and ('Three months ended' in line or 'In millions' in line):
                header_found = True
                continue

            parts = [p.strip() for p in re.split(r'\t|\s{2,}', line) if p.strip()]
            if len(parts) >= 3 and not parts[0].startswith('20'):  # Skip year headers
                try:
                    category = parts[0]
                    value_2022 = convert_currency(parts[1])
                    value_2021 = convert_currency(parts[2])
                    change_pct = parse_percentage(parts[3]) if len(parts) > 3 else None

                    data.append({
                        'category': category,
                        'value_2022': value_2022,
                        'value_2021': value_2021,
                        'change_pct': change_pct
                    })
                except (ValueError, IndexError):
                    continue

        return pd.DataFrame(data) if data else pd.DataFrame()

    def _parse_cash_flow_section(self, content: str) -> pd.DataFrame:
        """Parse cash flow section"""
        lines = content.split('\n')
        data = []

        for line in lines:
            line = line.strip()
            if not line or 'Three months ended' in line or 'In millions' in line:
                continue

            try:
                category_match = re.match(r'^(.*?)(?=\$|\d|\()', line)
                if not category_match:
                    continue

                category = category_match.group(1).strip()
                values = re.findall(r'\$?\s*-?\(?\d[\d,]*\)?', line)

                if len(values) >= 2:
                    data.append({
                        'category': category,
                        'value_2022': convert_currency(values[0]),
                        'value_2021': convert_currency(values[1])
                    })
            except (ValueError, IndexError):
                continue

        return pd.DataFrame(data) if data else pd.DataFrame()

    def _parse_debt_obligations_section(self, content: str) -> pd.DataFrame:
        """Parse debt obligations section"""
        lines = content.split('\n')
        data = []
        header_found = False
        years = ['total', '2022', '2023', '2024', '2025', '2026', '2027 & thereafter']

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if 'Total' in line and not header_found:
                header_found = True
                continue

            if line.startswith('Debt obligations') or line.startswith('Total contractual obligations'):
                continue

            parts = [p.strip() for p in re.split(r'\t|\s{2,}', line) if p.strip()]
            if len(parts) >= 2 and not any(year in parts[0].lower() for year in years):
                try:
                    category = parts[0]
                    values = [convert_currency(p) for p in parts[1:] if p]
                    if len(values) >= 2:  # At least total and one year
                        row_data = {'category': category}
                        row_data['total'] = values[0]
                        for i, year in enumerate(years[1:]):  # Skip 'total' in years list
                            if i + 1 < len(values):
                                row_data[year] = values[i + 1]
                        data.append(row_data)
                except (ValueError, IndexError):
                    continue

        return pd.DataFrame(data) if data else pd.DataFrame()