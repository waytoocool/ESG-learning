# User Dashboard Enhancements - Requirements and Specifications

## Project Overview
**Start Date**: 2025-01-04
**Project Type**: User Dashboard Enhancement
**Objective**: Modernize user data entry experience with modal-based collection, dimensional data support, and enhanced UX

## High-Level Requirements

### 1. Modal Dialog for Data Collection
- Replace inline table editing with comprehensive modal dialog
- Support both raw and computed field display
- Include file upload capabilities for evidence/attachments
- Show historical data for context

### 2. Dimensional Data Collection
- Display all dimension combinations as separate input fields
- Automatically calculate and display totals
- Support framework-defined dimensions (no dynamic add/remove)
- Validate against defined dimension values

### 3. Entity Management
- Display current entity name prominently
- Add entity switcher for users with multi-entity access
- Maintain entity context across sessions

### 4. Computation Context Modals
- Show formulas and calculation methods for computed fields
- Display dependencies and their current values
- Provide calculation breakdown for transparency

### 5. Historical Data Display
- Show previous submissions in the dialog
- Display trends and changes over time
- Separate views for raw vs computed fields

## Technical Requirements

### Architecture
- **Parallel Implementation**: New code completely separate from existing (`_v2` folders)
- **URL Separation**: Old (`/user/dashboard`) vs New (`/user/v2/dashboard`)
- **Feature Toggle**: Users can switch between interfaces
- **Data Model**: Enhanced JSON storage in existing `dimension_values` column

### Technology Stack
- **Backend**: Flask, SQLAlchemy, Python 3.x
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Database**: SQLite (existing schema enhanced)
- **File Storage**: Local file system

## Success Criteria
- ✓ All dimensional combinations can be entered
- ✓ Totals calculate correctly
- ✓ Entity switching works seamlessly
- ✓ Historical data displays properly
- ✓ Computed fields show formulas clearly
- ✓ Performance: Modal load < 500ms, save < 2s
- ✓ User satisfaction: Reduced entry time by 30%

## Project Phases
1. **Phase 0**: Parallel Implementation Setup (Week 1)
2. **Phase 1**: Core Modal Infrastructure (Week 2-3)
3. **Phase 2**: Dimensional Data Support (Week 3-4)
4. **Phase 3**: Computation Context (Week 4-5)
5. **Phase 4**: Advanced Features (Week 5-6)

## Related Documents
- [Main Implementation Plan](../../USER_DASHBOARD_ENHANCEMENTS_PLAN.md)
- Phase-specific requirements in respective phase folders
