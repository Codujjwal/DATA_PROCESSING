from typing import Union
import re

def convert_currency(value: str) -> float:
    """Convert currency string to float, handling parentheses for negative values"""
    if not value or value.isspace():
        return 0.0
        
    # Remove currency symbols and commas
    value = value.replace('$', '').replace(',', '').strip()
    
    # Handle parenthetical negatives
    if '(' in value and ')' in value:
        value = '-' + value.replace('(', '').replace(')', '')
        
    try:
        return float(value)
    except ValueError:
        return 0.0

def parse_percentage(value: str) -> float:
    """Convert percentage string to float, handling parentheses"""
    if not value or value.isspace():
        return 0.0
        
    # Remove % symbol and spaces
    value = value.replace('%', '').strip()
    
    # Handle parenthetical negatives
    if '(' in value and ')' in value:
        value = '-' + value.replace('(', '').replace(')', '')
        
    try:
        return float(value)
    except ValueError:
        return 0.0
