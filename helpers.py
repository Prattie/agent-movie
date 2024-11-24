# utils/helpers.py
from typing import List
import re

def parse_seat_selection(seat_input: str) -> List[str]:
    """Parse seat selection input into list of seats"""
    # Handle inputs like "A1, A2" or "A1,A2" or "A1 A2"
    seats = re.split(r'[,\s]+', seat_input.strip())
    return [seat.strip().upper() for seat in seats if seat.strip()]

def validate_seat_format(seats: List[str]) -> bool:
    """Validate seat format (e.g., 'A1', 'B2', etc.)"""
    pattern = re.compile(r'^[A-H][1-9]|10$')
    return all(pattern.match(seat) for seat in seats)

def calculate_total_price(seats: List[str], price_per_seat: float) -> float:
    """Calculate total price for selected seats"""
    return len(seats) * price_per_seat

def format_price(price: float) -> str:
    """Format price with currency symbol"""
    return f"${price:.2f}"
