# Amend ranking calculation in DarvasBox implementation

## Task
1. Amend darvas_box.py 
   - Add additional ranking function with signature:
       ```python
       def _ranking_ema200_3month(self) -> int:
       ```
     returning integer between 0-20
     Add implementation of _ranking_ema200_3month 
     return 20 if last self.df ema200 is 20% higher than ema200 3 months ago
     return gradually smaller number if difference is less than -5%
   - Add additional ranking function with signature:
       ```python
       def _ranking_ema200_6month(self) -> int:
       ```
     returning integer between 0-20
     Add implementation of _ranking_ema200_6month 
     return 20 if last self.df ema200 is 30% higher than ema200 6 months ago
     return gradually smaller number if difference is less than -10%
   - Add _ranking_ema200_3month + _ranking_ema200_6month to ranking calculation

## Analysis & Implementation Plan

### Current State Analysis
- The `DarvasBoxStrategy` class already has a `_ranking_ema200_1month` method that compares EMA200 performance vs 20 trading days ago
- Current `ranking` method combines price ranking (0-20) and 1-month EMA200 ranking (0-20) for total possible score of 40
- Need to add two new EMA200 ranking methods and incorporate them into the total ranking

### Implementation Details

#### Method 1: `_ranking_ema200_3month`
- Compare current EMA200 vs 3 months ago (approximately 65 trading days)
- Return 20 if EMA200 is 20% higher than 3 months ago
- Scale linearly down to 0 if difference is -5% or worse
- Handle edge cases: insufficient data, NaN values, zero/negative past values

#### Method 2: `_ranking_ema200_6month`
- Compare current EMA200 vs 6 months ago (approximately 130 trading days)
- Return 20 if EMA200 is 30% higher than 6 months ago
- Scale linearly down to 0 if difference is -10% or worse
- Handle edge cases: insufficient data, NaN values, zero/negative past values

#### Ranking Method Update
- Update the `ranking` method to include all three EMA200 components
- New total possible score: 20 (price) + 20 (1-month) + 20 (3-month) + 20 (6-month) = 80
- Update docstring to reflect new scoring system

### Todo List
1. Implement `_ranking_ema200_3month` method
2. Implement `_ranking_ema200_6month` method
3. Update `ranking` method to include new components
4. Update docstring for `ranking` method
5. Run tests to ensure implementation works correctly
