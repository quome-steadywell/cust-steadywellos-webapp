# Date Handling Fixes

## Problem Overview

The application was experiencing inconsistencies in date handling, specifically with weekly assessments counting. Tests were failing because:

1. The dashboard API was reporting different numbers of weekly assessments than the assessments API
2. Date calculations for determining the start and end of a week had issues
3. The test data seeder used slightly different date calculation logic than the main application

## Root Causes Identified

1. **Operator precedence bug**: The expression `today.weekday() + 1 % 7` doesn't work as expected because `%` has higher precedence than `+`. The correct version is `(today.weekday() + 1) % 7`.

2. **Inconsistent date range filtering**: The dashboard API was using `<` (less than) for the end date, while the assessments API was using `<=` (less than or equal to), causing assessments that fell exactly on the end time to be excluded.

3. **Date calculation inconsistencies**: Different parts of the codebase were calculating the start of the week in slightly different ways.

## Fixes Applied

### 1. Fixed operator precedence in date calculations

In multiple locations, updated:
```python
# Before
days_since_sunday = today.weekday() + 1 % 7  # Incorrect due to operator precedence

# After
current_weekday = today.weekday()  # Monday=0, Sunday=6
days_since_sunday = (current_weekday + 1) % 7  # Correct with parentheses
```

### 2. Made date range filters consistent

In the dashboard API:
```python
# Before
assessments_this_week = assessment_query.filter(
    Assessment.assessment_date >= week_start,
    Assessment.assessment_date < week_end
).count()

# After
assessments_this_week = assessment_query.filter(
    Assessment.assessment_date >= week_start,
    Assessment.assessment_date <= week_end
).count()
```

### 3. Standardized week calculation logic

Updated the date seeder to use consistent date calculations:
```python
# Before (in some places)
last_week_sunday = today - timedelta(days=today.weekday() + 8)

# After (standardized)
current_weekday = today.weekday()  # Monday=0, Sunday=6
days_since_sunday = (current_weekday + 1) % 7
this_sunday = today - timedelta(days=days_since_sunday)
last_week_sunday = this_sunday - timedelta(days=7)
```

## Affected Files

1. `/app/utils/__init__.py`: Fixed date bounds calculation
2. `/app/api/dashboard.py`: Fixed assessment filtering
3. `/tests/date_test.py`: Fixed test date calculations
4. `/app/utils/db_seeder.py`: Fixed test data date calculations

## Testing

All date handling tests now pass successfully, showing consistent counts between:
- Dashboard API weekly assessment counts
- Assessment API filtering by date range
- Sunday/Monday boundary handling
- Week transitions

## Recommendations

1. Add unit tests for the `get_date_bounds()` function to verify proper week calculations
2. Use consistent date range conventions throughout the application (recommend inclusive end dates)
3. Consider using Python's calendar module for week calculations to improve readability