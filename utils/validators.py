import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    # Saudi phone format
    pattern = r'^(\+966|0)?5[0-9]{8}$'
    return re.match(pattern, phone) is not None

def validate_rating(rating):
    return isinstance(rating, int) and 1 <= rating <= 5