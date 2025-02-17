<<<<<<< HEAD
pip install pandas numpy
```

## Usage

1. Place your financial statement in a text file named `financial_data.txt`
2. Run the parser:
```bash
python main.py
```
3. The processed data will be saved to:
   - `processed_operations_data.csv`
   - `processed_cash_flow_data.csv`
   - `processed_debt_obligations_data.csv`

## Data Format

The parser expects financial statements with these sections:
1. Operations data with year-over-year comparisons
   - Supports both percentage and absolute changes
   - Handles parenthetical notation for negative values
2. Cash flow statements
   - Operating activities
   - Investing activities
   - Before financing activities
3. Debt obligations with yearly breakdowns
   - Total obligations
   - Year-by-year projections

## Validation Features

- Year-over-year change validation with ±0.5% tolerance for rounding differences
- Cash flow consistency checks
- Debt obligations total verification
- Comprehensive error reporting for data inconsistencies

## Error Handling

The parser provides detailed validation results including:
- Year-over-year change mismatches
- Cash flow total inconsistencies
- Debt obligations total mismatches
- Data format and conversion errors

## Dependencies

- Python 3.11+
- pandas
- numpy

## Development

Run tests using:
```bash
python -m unittest tests/test_parser.py -v
=======
# DATA_PROCESSING
>>>>>>> 27c523a965ccb31c0bd4c0c40577cb36c443ec2f
