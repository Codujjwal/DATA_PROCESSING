from financial_parser import FinancialDataParser, DataValidator, DataCleaner
import pandas as pd

def main():
    # Initialize components
    parser = FinancialDataParser()
    cleaner = DataCleaner()

    print("\nStarting financial data processing...")

    # Read input file
    try:
        with open('financial_data.txt', 'r') as file:
            content = file.read()
        print("Successfully read input file")
    except FileNotFoundError:
        print("Error: Input file 'financial_data.txt' not found")
        return

    # Parse the data
    try:
        operations_df, cash_flow_df, debt_df = parser.parse_financial_statement(content)

        # Print operations data info
        if not operations_df.empty:
            print("\nOperations Data Shape:", operations_df.shape)
            print("Columns:", list(operations_df.columns))
            print("\nFirst few rows of operations data:")
            print(operations_df.head())

        # Print cash flow data info
        if not cash_flow_df.empty:
            print("\nCash Flow Data Shape:", cash_flow_df.shape)
            print("Columns:", list(cash_flow_df.columns))
            print("\nCash flow data:")
            print(cash_flow_df)

        # Print debt obligations info
        if not debt_df.empty:
            print("\nDebt Obligations Data Shape:", debt_df.shape)
            print("Columns:", list(debt_df.columns))
            print("\nFirst few rows of debt obligations:")
            print(debt_df.head())

    except Exception as e:
        print(f"Error parsing data: {str(e)}")
        return

    # Clean the data
    try:
        if not operations_df.empty:
            operations_df = cleaner.clean_data(operations_df)
            print("\nOperations data cleaning complete")

        if not cash_flow_df.empty:
            cash_flow_df = cleaner.clean_data(cash_flow_df)
            print("Cash flow data cleaning complete")

        if not debt_df.empty:
            debt_df = cleaner.clean_data(debt_df)
            print("Debt obligations data cleaning complete")

    except Exception as e:
        print(f"Error cleaning data: {str(e)}")
        return

    # Validate all data sections
    validator = DataValidator(operations_df, cash_flow_df, debt_df)
    validation_results = validator.validate_all()

    print("\nValidation Results:")
    if not validation_results:
        print("No validation issues found")
    else:
        for result in validation_results:
            if result['type'] == 'error':
                print(f"Error: {result['message']}")
            elif result['type'] == 'total_mismatch':
                print(f"Total mismatch in {result['category']} for {result['year']}:")
                print(f"  Calculated: {result['calculated']:.2f}")
                print(f"  Reported: {result['reported']:.2f}")
            elif result['type'] == 'yoy_change_mismatch':
                print(f"Year-over-year change mismatch for {result['category']}:")
                print(f"  Calculated: {result['calculated']}%")
                print(f"  Reported: {result['reported']}%")
            elif result['type'] == 'cash_flow_mismatch':
                print("Cash flow total mismatch:")
                print(f"  Calculated: {result['calculated']:.2f}")
                print(f"  Reported: {result['reported']:.2f}")
            elif result['type'] == 'debt_total_mismatch':
                print(f"Debt obligations total mismatch for {result['category']}:")
                print(f"  Calculated: {result['calculated']:.2f}")
                print(f"  Reported: {result['reported']:.2f}")
            elif result['type'] == 'negative_debt_value':
                print(f"Negative debt value found in category: {result['category']}")

    # Save processed data
    try:
        if not operations_df.empty:
            operations_df.to_csv('processed_operations_data.csv', index=False)
            print("\nOperations data saved to 'processed_operations_data.csv'")

        if not cash_flow_df.empty:
            cash_flow_df.to_csv('processed_cash_flow_data.csv', index=False)
            print("Cash flow data saved to 'processed_cash_flow_data.csv'")

        if not debt_df.empty:
            debt_df.to_csv('processed_debt_obligations_data.csv', index=False)
            print("Debt obligations data saved to 'processed_debt_obligations_data.csv'")

    except Exception as e:
        print(f"Error saving data: {str(e)}")

if __name__ == "__main__":
    main()