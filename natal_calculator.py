"""
Correct Natal Type Calculator based on the 9-year cycle with 108 month blocks.
This replaces the incorrect day-based calculation.
"""

from datetime import datetime

def get_year_order(year: int) -> int:
    """Calculates the unique year order (1-9 cycle) based on the provided year."""
    years = {}
    year_order_counter = 1
    # Range from 1919 to 2030
    for y in range(1919, 2031):
        years[y] = year_order_counter
        if year_order_counter == 9:
            year_order_counter = 0
        year_order_counter += 1
    return years.get(year, -1)

def get_month_row(day: int, month: int, year: int) -> int:
    """Determines the 'row' index based on the specific date within the 13-range table."""
    # Define the date ranges (month/day, month/day)
    table_ranges = [
        {"row": 0, "from": (1, 1), "to": (1, 5)},
        {"row": 1, "from": (1, 6), "to": (2, 3)},
        {"row": 2, "from": (2, 4), "to": (3, 5)},
        {"row": 3, "from": (3, 6), "to": (4, 4)},
        {"row": 4, "from": (4, 5), "to": (5, 5)},
        {"row": 5, "from": (5, 6), "to": (6, 5)},
        {"row": 6, "from": (6, 6), "to": (7, 7)},
        {"row": 7, "from": (7, 8), "to": (8, 7)},
        {"row": 8, "from": (8, 8), "to": (9, 7)},
        {"row": 9, "from": (9, 8), "to": (10, 8)},
        {"row": 10, "from": (10, 9), "to": (11, 7)},
        {"row": 11, "from": (11, 8), "to": (12, 7)},
        {"row": 12, "from": (12, 8), "to": (12, 31)}
    ]

    user_date = datetime(year, month, day)

    for item in table_ranges:
        from_month, from_day = item["from"]
        to_month, to_day = item["to"]

        date_from = datetime(year, from_month, from_day)
        date_to = datetime(year, to_month, to_day)

        if item["row"] == 0:  # Jan 1-5 special case
            if date_from <= user_date <= date_to:
                return 12  # Maps to "month 12" in lookup tables
        else:  # Standard rows
            if date_from <= user_date <= date_to:
                return item["row"]

    return -1

def calculate_natal_type(day: int, month: int, year: int, gender: str) -> str:
    """
    Calculates the natal Affinity Zone (SS, SD, DS, DD) based on birth date and gender.
    Uses the correct 9-year cycle with 108 month blocks.
    """
    # Input validation
    if not (1 <= month <= 12 and 1 <= day <= 31):
        raise ValueError("Invalid month or day.")
    if not (1919 <= year <= 2030):
        raise ValueError("Year out of supported range (1919-2030).")
    if gender not in ["male", "female"]:
        raise ValueError("Gender must be 'male' or 'female'.")

    # Male and Female lookup tables
    male_lookup = {
        1: {"1": "G", "2": "A", "3": "D", "4": "A", "5": "A", "6": "D", "7": "A", "8": "G", "9": "B"},
        2: {"1": "G", "2": "B", "3": "G", "4": "A", "5": "B", "6": "G", "7": "A", "8": "D", "9": "A"},
        3: {"1": "D", "2": "A", "3": "D", "4": "B", "5": "A", "6": "D", "7": "B", "8": "G", "9": "B"},
        4: {"1": "G", "2": "B", "3": "G", "4": "A", "5": "B", "6": "G", "7": "A", "8": "D", "9": "A"},
        5: {"1": "D", "2": "A", "3": "G", "4": "B", "5": "A", "6": "G", "7": "B", "8": "G", "9": "A"},
        6: {"1": "G", "2": "B", "3": "D", "4": "A", "5": "B", "6": "D", "7": "A", "8": "D", "9": "B"},
        7: {"1": "D", "2": "A", "3": "G", "4": "B", "5": "A", "6": "G", "7": "B", "8": "G", "9": "A"},
        8: {"1": "G", "2": "A", "3": "D", "4": "A", "5": "A", "6": "D", "7": "A", "8": "G", "9": "B"},
        9: {"1": "D", "2": "B", "3": "G", "4": "B", "5": "B", "6": "G", "7": "B", "8": "D", "9": "A"},
        10: {"1": "G", "2": "A", "3": "D", "4": "A", "5": "A", "6": "D", "7": "A", "8": "G", "9": "B"},
        11: {"1": "G", "2": "B", "3": "G", "4": "A", "5": "B", "6": "G", "7": "A", "8": "D", "9": "A"},
        12: {"1": "D", "2": "A", "3": "D", "4": "B", "5": "A", "6": "D", "7": "B", "8": "G", "9": "B"}
    }

    female_lookup = {
        1: {"1": "G", "2": "A", "3": "D", "4": "A", "5": "G", "6": "D", "7": "A", "8": "G", "9": "B"},
        2: {"1": "D", "2": "B", "3": "G", "4": "B", "5": "D", "6": "G", "7": "B", "8": "D", "9": "A"},
        3: {"1": "D", "2": "A", "3": "D", "4": "B", "5": "G", "6": "D", "7": "B", "8": "G", "9": "B"},
        4: {"1": "G", "2": "B", "3": "G", "4": "A", "5": "D", "6": "G", "7": "A", "8": "D", "9": "A"},
        5: {"1": "D", "2": "A", "3": "D", "4": "B", "5": "G", "6": "D", "7": "B", "8": "G", "9": "B"},
        6: {"1": "G", "2": "B", "3": "D", "4": "A", "5": "D", "6": "D", "7": "A", "8": "D", "9": "B"},
        7: {"1": "D", "2": "A", "3": "G", "4": "B", "5": "G", "6": "G", "7": "B", "8": "G", "9": "A"},
        8: {"1": "G", "2": "B", "3": "D", "4": "A", "5": "D", "6": "D", "7": "A", "8": "D", "9": "B"},
        9: {"1": "D", "2": "B", "3": "G", "4": "B", "5": "D", "6": "G", "7": "B", "8": "D", "9": "A"},
        10: {"1": "G", "2": "A", "3": "D", "4": "A", "5": "G", "6": "D", "7": "A", "8": "G", "9": "B"},
        11: {"1": "D", "2": "B", "3": "G", "4": "B", "5": "D", "6": "G", "7": "B", "8": "D", "9": "A"},
        12: {"1": "D", "2": "A", "3": "D", "4": "B", "5": "G", "6": "D", "7": "B", "8": "G", "9": "B"}
    }

    # Map letters to affinity zones
    affinity_map = {
        "D": "SS",
        "B": "DS",
        "A": "DD",
        "G": "SD"
    }

    current_year = year
    month_row_index = get_month_row(day, month, current_year)

    # Handle the special Jan 1-5 case
    if month_row_index == 12 and month == 1 and day <= 5:
        current_year -= 1

    year_order = get_year_order(current_year)

    if year_order == -1:
        raise ValueError("Year order could not be determined for the adjusted year.")

    if gender == "male":
        letter_code = male_lookup[month_row_index][str(year_order)]
    else:  # female
        letter_code = female_lookup[month_row_index][str(year_order)]

    return affinity_map.get(letter_code, "UNKNOWN_TYPE")