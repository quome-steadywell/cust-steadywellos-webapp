# Utils package initialization
from datetime import datetime, timedelta

def get_date_bounds(period='week'):
    """
    Get standardized date bounds for consistent date filtering across the application.
    
    Args:
        period (str): Time period to get bounds for: 'day', 'week', 'month'
        
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if period == 'day':
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == 'week':
        # Get the first day of current week (Sunday)
        # Using Sunday as first day of week (0=Sunday, 6=Saturday)
        current_weekday = today.weekday()  # Monday=0, Sunday=6
        days_since_sunday = (current_weekday + 1) % 7  # Convert to Sunday=0 basis
        start_date = today - timedelta(days=days_since_sunday)
        # End date is 7 days later (inclusive of the entire day)
        end_date = start_date + timedelta(days=7)
    elif period == 'month':
        # Get the first day of current month
        start_date = today.replace(day=1)
        # Get the first day of next month
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1)
    else:
        raise ValueError(f"Invalid period: {period}")
    
    return start_date, end_date
