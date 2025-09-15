# Change strategy_performance.py interface to single period
The goal is to change strategy_performance.py interface so that instead of "periods LIST" parameter
there is max_holding_period parameter (default 1M) so that performance will be calculated always
for one period instead of multiple periods.

## Current Issues
- The script currently accepts a list of periods: `--periods 3d,1W,2W,1M,3M,6M`
- This creates complex multi-period results that may be harder to analyze
- Users need to specify multiple periods even when only interested in one holding period
- Results structure is complex with multiple period comparisons

## Proposed Changes
- Replace `--periods` parameter with `--max-holding-period` 
- Default value: "1M" (1 month)
- Simplify to single period analysis instead of multi-period comparison
- Streamline results output for focused analysis

## Analysis Results
After analyzing the codebase, the following components need modification:

### Current Implementation
1. **scripts/strategy_performance.py**:
   - `--periods` argument accepts comma-separated list (default: "3d,1W,2W,1M,3M,6M")
   - `parse_periods()` function converts string to List[pd.Timedelta]
   - Passes list to StrategyPerformanceService

2. **turtle/service/strategy_performance_service.py**:
   - `DEFAULT_TEST_PERIODS` list with 6 periods
   - Constructor accepts `test_periods: Optional[List[pd.Timedelta]]`
   - All methods iterate over `self.test_periods` list

3. **turtle/performance/strategy_performance.py**:
   - StrategyPerformanceTester expects `test_periods: List[pd.Timedelta]`
   - All analysis methods iterate over multiple periods
   - Results structure handles multiple periods

### Components to Change

#### 1. Script Interface (scripts/strategy_performance.py)
- Remove `--periods` argument and `parse_periods()` function
- Add `--max-holding-period` argument (default: "1M")
- Convert single period string to single pd.Timedelta

#### 2. Service Layer (turtle/service/strategy_performance_service.py)
- Replace `DEFAULT_TEST_PERIODS` list with `DEFAULT_HOLDING_PERIOD`
- Change constructor to accept `max_holding_period: Optional[pd.Timedelta]`
- Update all methods to use single period instead of list iteration

#### 3. Performance Tester (turtle/performance/strategy_performance.py)
- Change constructor to accept `max_holding_period: pd.Timedelta` 
- Update all analysis methods to work with single period
- Simplify results structure (remove period iteration loops)

#### 4. Results Handling
- ~~Update TestSummary and PerformanceResult models for single period~~ (classes removed)
- Simplify output formatting (remove period comparison logic)
- Update CSV/JSON export formats

#### 5. Tests and Documentation
- Update test files to use single period interface
- Update example usage and documentation
- Update CLI help text and usage examples

## Implementation Plan

### Phase 1: Core Interface Changes
1. **Update script argument parsing**
   - Replace `--periods` with `--max-holding-period`
   - Add period parsing for single value
   - Update help text and examples

### Phase 2: Service Layer Updates  
2. **Update StrategyPerformanceService**
   - Change constructor signature
   - Replace period list with single period
   - Update method implementations

3. **Update StrategyPerformanceTester**
   - Change constructor signature  
   - Remove period iteration loops
   - Simplify analysis logic

### Phase 3: Results Structure
4. **Update result models and handling**
   - ~~Simplify TestSummary for single period~~ (class removed)
   - ~~Update PerformanceResult structure~~ (class removed)
   - Simplify output formatting

### Phase 4: Testing and Documentation
5. **Update tests and examples**
   - Modify test files for single period interface
   - Update usage examples and documentation
   - Verify all functionality works correctly

## Benefits
- **Simplified interface**: Single parameter instead of complex list
- **Focused analysis**: Clear results for one holding period
- **Easier to use**: Default 1M period covers most use cases
- **Cleaner output**: No complex multi-period comparisons
- **Better performance**: Less computation for single period

## Migration Notes
- **Breaking change**: Existing scripts using `--periods` will need updating
- **Default behavior**: 1M holding period provides sensible default
- **Backward compatibility**: Old period format parsing can be removed
