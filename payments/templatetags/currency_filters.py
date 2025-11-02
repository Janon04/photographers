from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def rwf_currency(value):
    """Format currency as Rwandan Francs"""
    if value is None:
        return "0 RWF"
    
    try:
        # Convert to int for RWF (no decimals)
        amount = int(float(value))
        # Format with commas for thousands
        return f"{amount:,} RWF"
    except (ValueError, TypeError):
        return "0 RWF"

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    if not total or total == 0:
        return 0
    try:
        return round((float(value) / float(total)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0