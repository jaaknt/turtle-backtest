# Amend ranking calculation in DarvasBox implementation

## Task
1. Amend darvas_box.py 
   - Add additional ranking function with signature:
       ```python
       def _ranking_period_high(self) -> int:
       ```
       returning integer between 0-20
   - Add implementation _ranking_period_high
     return 20 if last close is highest close during last 365 days
     return gradually smaller number if last close was highest during 0 days
   - Add _ranking_period_high result to ranking calculation by adding to existing result

## Analysis & Implementation Plan

### Current State Analysis
- The `DarvasBoxStrategy` class has a `ranking` method that returns 0-80 from four components:
  - Price ranking (0-20)
  - EMA200 1-month ranking (0-20)
  - EMA200 3-month ranking (0-20)
  - EMA200 6-month ranking (0-20)
- Need to add a fifth component for period high ranking (0-20)
- New total possible score will be 0-100

### Implementation Details

#### Method: `_ranking_period_high`
- Find the longest period (up to 365 days) where the current close is the highest close
- Return 20 if current close is highest in the full 365-day period
- Scale linearly down as the period gets shorter
- Return close to 0 if current close is only highest in the last few days
- Handle edge cases: insufficient data, NaN values

#### Logic Flow
1. Check if we have at least 365 days of data
2. Find the maximum close in the last 365 days
3. If current close equals this maximum, find how many days back this high extends
4. Calculate score based on the length of the period where current close is highest
5. Scale: 365 days = 20 points, 1 day = ~0 points

#### Ranking Method Update
- Add the new period high component to the existing ranking calculation
- Update total possible score from 80 to 100
- Update docstring to reflect new scoring system

### Todo List
1. Implement `_ranking_period_high` method with period high logic
2. Update `ranking` method to include new period high component
3. Update docstring for `ranking` method to reflect new scoring system (0-100)
4. Run tests to ensure implementation works correctly