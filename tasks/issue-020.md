# Document different scripts in docs/scripts.md file
The goal is to document existing scripts
- create new file docs/scripts.md file 
- document these scripts in this file
  - @scripts/daily_eod_update.py
  - @scripts/strategy_runner.py
  - @scripts/strategy_performance.py
- add reference to this file in @README.md and remove duplication from @README.md and @service.md

## Plan
Based on analysis of current documentation state:

**Current State:**
- service.md contains a comprehensive "Scripts" section (lines 108-237) with documentation for all three scripts
- README.md currently references service.md#scripts for script documentation
- Need to separate script documentation from service documentation

**Required Changes:**
1. **Create docs/scripts.md** - New dedicated file for script documentation using existing content from service.md
2. **Remove Scripts section** - Delete Scripts section from docs/service.md (lines 108-237) to eliminate duplication
3. **Update README.md** - Change references from service.md#scripts to docs/scripts.md
4. **Maintain quality** - Ensure all existing script documentation content is preserved

**Benefits:**
- Clear separation of concerns (services vs scripts)
- Eliminates documentation duplication
- Better organization with dedicated files for each topic

## Todo List
- [x] Analyze current documentation state in service.md and README.md
- [x] Create new docs/scripts.md file with script documentation from service.md
- [x] Remove Scripts section from docs/service.md
- [x] Update README.md to reference docs/scripts.md instead of service.md#scripts
- [ ] Run linting on all changes and fix any errors
