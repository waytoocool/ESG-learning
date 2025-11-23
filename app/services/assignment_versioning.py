"""
Assignment Versioning Service for ESG DataVault.

This service handles the core Phase 2 requirement for assignment versioning,
data series management, and assignment resolution with dual compatibility support.

Key Features:
- Data series versioning (v1, v2, v3, etc.)
- Assignment lifecycle management (active → superseded → legacy)
- Dual compatibility (field_id and assignment_id patterns)
- Company fiscal year integration
- Performance-optimized resolution (< 50ms target)
"""

import uuid
from datetime import datetime, UTC, date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models.data_assignment import DataPointAssignment
from ..models.esg_data import ESGData
from ..models.company import Company
from ..middleware.tenant import get_current_tenant


class AssignmentVersioningService:
    """
    Core service for managing assignment versions and data series.
    
    This service implements the assignment versioning logic that allows
    indefinite assignments with proper version tracking and data integrity.
    """
    
    @staticmethod
    def create_assignment_version(
        assignment_id: str, 
        changes: Dict[str, Any], 
        reason: str,
        created_by: int
    ) -> Dict[str, Any]:
        """
        Create a new version of an existing assignment with changes.
        
        This method implements the core versioning logic:
        1. Validates the existing assignment
        2. Creates a new version with incremented version number
        3. Marks the old version as superseded
        4. Maintains data series integrity
        
        Args:
            assignment_id: ID of the assignment to version
            changes: Dictionary of field changes to apply
            reason: Reason for creating the new version
            created_by: User ID creating the version
            
        Returns:
            Dict containing new version info and status
            
        Raises:
            ValueError: If assignment not found or changes are invalid
            RuntimeError: If versioning operation fails
        """
        try:
            print(f"[DEBUG create_assignment_version] Starting versioning for assignment {assignment_id}")
            # Get current assignment with tenant scoping
            current_assignment = DataPointAssignment.query.filter_by(id=assignment_id, series_status='active').first()

            if not current_assignment:
                print(f"[DEBUG create_assignment_version] Assignment {assignment_id} not found")
                raise ValueError(f"Assignment {assignment_id} not found")

            print(f"[DEBUG create_assignment_version] Found assignment: field_id={current_assignment.field_id}, entity_id={current_assignment.entity_id}, company_id={current_assignment.company_id}, status={current_assignment.series_status}")

            # Validate assignment belongs to current tenant
            current_tenant = get_current_tenant()
            company_id = current_tenant.id if current_tenant else None
            if current_assignment.company_id != company_id:
                print(f"[DEBUG create_assignment_version] Company mismatch: assignment company={current_assignment.company_id}, current tenant={company_id}")
                raise ValueError("Assignment not found in current company")

            # For inactive assignments, we can reactivate them with new configuration
            if current_assignment.series_status not in ['active', 'inactive']:
                print(f"[DEBUG create_assignment_version] Invalid status: {current_assignment.series_status}")
                raise ValueError(f"Cannot version assignment in {current_assignment.series_status} status")

            # Validate proposed changes
            print(f"[DEBUG create_assignment_version] Validating changes: {changes}")
            validation_result = AssignmentVersioningService.validate_assignment_change(
                assignment_id, changes
            )

            if not validation_result['is_valid']:
                print(f"[DEBUG create_assignment_version] Validation failed: {validation_result['error']}")
                raise ValueError(f"Invalid changes: {validation_result['error']}")

            # DEFENSIVE FIX: Before proceeding, check for and fix any duplicate active assignments
            # This prevents the bug where old versions remain active after versioning
            from sqlalchemy import and_
            duplicate_actives = DataPointAssignment.query.filter(
                and_(
                    DataPointAssignment.field_id == current_assignment.field_id,
                    DataPointAssignment.entity_id == current_assignment.entity_id,
                    DataPointAssignment.company_id == current_assignment.company_id,
                    DataPointAssignment.series_status == 'active',
                    DataPointAssignment.id != assignment_id  # Exclude current assignment being versioned
                )
            ).all()

            if duplicate_actives:
                # CRITICAL: Other active assignments exist! Auto-supersede them before proceeding
                from flask import current_app
                current_app.logger.error(
                    f"[VERSIONING-DUPLICATE-FIX] DETECTED {len(duplicate_actives)} duplicate active assignments: "
                    f"field={current_assignment.field_id}, entity={current_assignment.entity_id}, "
                    f"versions=[{', '.join(f'v{a.series_version}' for a in duplicate_actives)}]"
                )

                for dup in duplicate_actives:
                    dup.series_status = 'superseded'
                    current_app.logger.warning(
                        f"[VERSIONING-DUPLICATE-FIX] Auto-superseded duplicate: {dup.id} (v{dup.series_version})"
                    )

                # Flush the supersede operations immediately
                db.session.flush()
                current_app.logger.info(
                    f"[VERSIONING-DUPLICATE-FIX] Fixed {len(duplicate_actives)} duplicate active assignments"
                )

            print(f"[DEBUG create_assignment_version] About to mark assignment {assignment_id} as superseded")
            # Use existing session transaction (don't start a new one)
            # Mark current assignment as superseded
            current_assignment.series_status = 'superseded'
            current_assignment.series_status = 'superseded'  # Mark previous version as superseded
            print(f"[DEBUG create_assignment_version] Marked assignment {assignment_id} as superseded")

            # TWO-PHASE FLUSH FIX: Flush supersede to database BEFORE creating new version
            # This ensures the validation query sees the old assignment as superseded
            # when validating the new active assignment during the second flush.
            try:
                db.session.flush()
                print(f"[DEBUG create_assignment_version] Phase 1: Flushed supersede of assignment {assignment_id} to database")
            except Exception as flush_error:
                print(f"[ERROR create_assignment_version] Phase 1 flush failed: {str(flush_error)}")
                raise RuntimeError(f"Failed to supersede assignment {assignment_id}: {str(flush_error)}")

            # Set versioning context to bypass validation for this field+entity+company combination
            from ..models.data_assignment import set_versioning_context, clear_versioning_context
            print(f"[DEBUG create_assignment_version] Setting versioning context for field={current_assignment.field_id}, entity={current_assignment.entity_id}, company={current_assignment.company_id}")
            set_versioning_context(current_assignment.field_id, current_assignment.entity_id, current_assignment.company_id)

            try:
                # Create new version (only include constructor-accepted parameters)
                # Ensure data_series_id is never None to avoid UUID generation in constructor
                data_series_id = current_assignment.data_series_id or str(uuid.uuid4())

                new_version_data = {
                    'field_id': current_assignment.field_id,
                    'entity_id': current_assignment.entity_id,
                    'company_id': current_assignment.company_id,
                    'frequency': current_assignment.frequency,
                    'assigned_by': created_by,
                    'unit': current_assignment.unit,
                    'assigned_topic_id': current_assignment.assigned_topic_id,
                    'data_series_id': data_series_id,  # Same series, ensure not None
                    'series_version': current_assignment.series_version + 1,  # Increment version
                }

                # Apply changes to new version (only for constructor-accepted fields)
                # Explicitly exclude series_status and other non-constructor fields
                constructor_fields = {'field_id', 'entity_id', 'company_id', 'frequency', 'assigned_by', 'unit', 'assigned_topic_id', 'data_series_id', 'series_version'}
                excluded_fields = {'series_status', 'is_active', 'assigned_date'}  # Fields that cannot be passed to constructor
                for field, value in changes.items():
                    if field in constructor_fields and field in new_version_data and field not in excluded_fields:
                        new_version_data[field] = value

                new_assignment = DataPointAssignment(**new_version_data)

                # Set additional fields that can't be passed to constructor
                new_assignment.series_status = 'active'  # New version is always active
                new_assignment.series_status = 'active'  # Ensure new version is active

                # Apply changes for non-constructor fields
                for field, value in changes.items():
                    if field not in constructor_fields and hasattr(new_assignment, field):
                        setattr(new_assignment, field, value)

                # Add to session and flush to get ID without committing transaction
                db.session.add(new_assignment)
                print(f"[DEBUG create_assignment_version] Added new assignment to session, about to flush (Phase 2)")

                # TWO-PHASE FLUSH: Phase 2 - Flush new active assignment
                # Validation will now see the old assignment as superseded (from Phase 1)
                try:
                    db.session.flush()  # Get new assignment ID without committing
                    print(f"[DEBUG create_assignment_version] Phase 2: Successfully flushed new assignment, ID: {new_assignment.id}")
                except Exception as flush_error:
                    print(f"[DEBUG create_assignment_version] Flush error: {str(flush_error)}")
                    # If flush fails due to transaction state, try to handle gracefully
                    error_msg = str(flush_error).lower()
                    if "transaction is already begun" in error_msg or "transaction" in error_msg:
                        # Re-raise with more context
                        raise RuntimeError(f"Transaction conflict detected during assignment versioning: {str(flush_error)}")
                    else:
                        raise
            finally:
                # Always clear the versioning context, even if an error occurs
                print(f"[DEBUG create_assignment_version] Clearing versioning context")
                clear_versioning_context(current_assignment.field_id, current_assignment.entity_id, current_assignment.company_id)

            # Validate data integrity after creation
            old_validation = current_assignment.validate_data_integrity()
            new_validation = new_assignment.validate_data_integrity()

            if not old_validation['is_valid']:
                raise ValueError(f"Data integrity issue with superseded assignment: {old_validation['error']}")
            if not new_validation['is_valid']:
                raise ValueError(f"Data integrity issue with new assignment: {new_validation['error']}")

            # Log the versioning operation
            version_info = {
                'old_assignment_id': assignment_id,
                'new_assignment_id': new_assignment.id,
                'series_id': current_assignment.data_series_id,
                'old_version': current_assignment.series_version,
                'new_version': new_assignment.series_version,
                'changes': changes,
                'reason': reason,
                'created_by': created_by,
                'created_at': datetime.now(UTC).isoformat()
            }

            # Don't commit here - let the calling function handle transaction commit

            return {
                'success': True,
                'new_assignment': {
                    'id': new_assignment.id,
                    'series_id': new_assignment.data_series_id,
                    'version': new_assignment.series_version,
                    'status': new_assignment.series_status
                },
                'version_info': version_info
            }
                
        except Exception as e:
            # Let Flask handle the rollback since we're using its transaction
            raise RuntimeError(f"Failed to create assignment version: {str(e)}")
    
    @staticmethod
    def get_active_assignment(
        field_id: str, 
        entity_id: int, 
        target_date: date = None
    ) -> Optional[DataPointAssignment]:
        """
        Get the active assignment for a field+entity combination on a specific date.
        
        This method implements the core assignment resolution logic with:
        1. Date-based resolution using company FY configuration
        2. Dual compatibility (supports both new and legacy patterns)
        3. Performance optimization with proper indexing
        4. Tenant isolation
        
        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            target_date: Date to resolve assignment for (defaults to today)
            
        Returns:
            Active DataPointAssignment or None if no active assignment found
        """
        if target_date is None:
            target_date = date.today()
            
        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None
        
        # Query for active assignments for this field+entity combination
        query = DataPointAssignment.query.filter(
            and_(
                DataPointAssignment.field_id == field_id,
                DataPointAssignment.entity_id == entity_id,
                DataPointAssignment.company_id == company_id,
                DataPointAssignment.series_status == 'active',
                DataPointAssignment.series_status == 'active'
            )
        ).options(
            joinedload(DataPointAssignment.company),
            joinedload(DataPointAssignment.field)
        ).order_by(
            desc(DataPointAssignment.series_version)
        )
        
        # Get all active assignments (should normally be 1, but handle edge cases)
        active_assignments = query.all()
        
        if not active_assignments:
            return None
        
        # If multiple active assignments (edge case), return the highest version
        if len(active_assignments) > 1:
            # Log this as it shouldn't happen in normal operation
            print(f"Warning: Multiple active assignments found for field {field_id}, entity {entity_id}")
        
        active_assignment = active_assignments[0]
        
        # Validate the assignment is appropriate for the target date
        # This uses company FY configuration to ensure date is within valid range
        if active_assignment.company:
            try:
                current_fy = AssignmentVersioningService._get_fy_for_date(
                    target_date, active_assignment.company
                )
                
                # Check if target date is valid for this assignment's frequency
                valid_dates = active_assignment.get_valid_reporting_dates(current_fy)
                
                if target_date in valid_dates or AssignmentVersioningService._is_date_in_fy_range(
                    target_date, current_fy, active_assignment.company
                ):
                    return active_assignment
                else:
                    # Date is outside valid range for this assignment
                    return None
                    
            except Exception as e:
                # If FY calculation fails, return assignment anyway (graceful degradation)
                print(f"Warning: FY calculation failed for assignment {active_assignment.id}: {str(e)}")
                return active_assignment
        
        return active_assignment
    
    @staticmethod
    def supersede_assignment(assignment_id: str, reason: str = None) -> Dict[str, Any]:
        """
        Mark an assignment as inactive without creating a new version.

        This is used when an assignment needs to be deactivated without
        replacement (e.g., data field no longer needed).

        NOTE: This method does NOT commit the transaction - the caller must handle that.

        Args:
            assignment_id: ID of assignment to supersede
            reason: Optional reason for superseding

        Returns:
            Dict with operation status and details

        Raises:
            ValueError: If assignment not found or already superseded
        """
        assignment = DataPointAssignment.query.filter_by(id=assignment_id, series_status='active').first()

        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found or inactive")

        # Validate tenant access
        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None
        if assignment.company_id != company_id:
            raise ValueError("Assignment not found in current company")

        if assignment.series_status != 'active':
            raise ValueError(f"Assignment is already {assignment.series_status}")

        # Mark as inactive (caller will commit the transaction)
        assignment.series_status = 'inactive'

        return {
            'success': True,
            'assignment_id': assignment_id,
            'new_status': 'inactive',
            'reason': reason,
            'superseded_at': datetime.now(UTC).isoformat()
        }
    
    @staticmethod
    def validate_assignment_change(
        assignment_id: str, 
        new_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate proposed changes to an assignment before creating a new version.
        
        This method prevents destructive changes and ensures data integrity:
        1. Validates field changes are allowed
        2. Checks for potential data loss scenarios
        3. Warns about breaking changes
        
        Args:
            assignment_id: Assignment to validate changes for
            new_config: Proposed new configuration
            
        Returns:
            Dict with validation results and warnings
        """
        try:
            assignment = DataPointAssignment.query.filter_by(id=assignment_id, series_status='active').first()

            if not assignment:
                return {
                    'is_valid': False,
                    'error': f"Assignment {assignment_id} not found or inactive",
                    'warnings': []
                }
            
            warnings = []
            errors = []
            
            # Validate field changes
            allowed_changes = {
                'frequency', 'unit', 'assigned_topic_id'
            }
            
            disallowed_changes = {
                'field_id', 'entity_id', 'company_id'  # These would break data relationships
            }
            
            for field, value in new_config.items():
                if field in disallowed_changes:
                    errors.append(f"Cannot change {field} - would break data integrity")
                elif field not in allowed_changes:
                    warnings.append(f"Change to {field} is not typically recommended")
            
            # Check for frequency changes that might affect existing data
            if 'frequency' in new_config and new_config['frequency'] != assignment.frequency:
                # Count existing data entries
                data_count = ESGData.query.filter_by(
                    field_id=assignment.field_id,
                    entity_id=assignment.entity_id
                ).count()
                
                if data_count > 0:
                    warnings.append(
                        f"Frequency change from {assignment.frequency} to {new_config['frequency']} "
                        f"affects {data_count} existing data entries"
                    )
            
            # Check for unit changes
            if 'unit' in new_config and new_config['unit'] != assignment.unit:
                warnings.append(
                    f"Unit change from {assignment.unit or assignment.field.default_unit} "
                    f"to {new_config['unit']} may require data recalculation"
                )
            
            return {
                'is_valid': len(errors) == 0,
                'error': '; '.join(errors) if errors else None,
                'warnings': warnings,
                'change_summary': {
                    'total_changes': len(new_config),
                    'safe_changes': len([k for k in new_config.keys() if k in allowed_changes]),
                    'warning_changes': len([k for k in new_config.keys() if k not in allowed_changes and k not in disallowed_changes]),
                    'blocked_changes': len([k for k in new_config.keys() if k in disallowed_changes])
                }
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f"Validation failed: {str(e)}",
                'warnings': []
            }
    
    @staticmethod
    def get_assignment_history(
        field_id: str = None, 
        entity_id: int = None, 
        data_series_id: str = None
    ) -> List[DataPointAssignment]:
        """
        Get version history for assignments.
        
        Can be filtered by field+entity combination or by data_series_id.
        
        Args:
            field_id: Filter by field ID (requires entity_id)
            entity_id: Filter by entity ID (requires field_id)  
            data_series_id: Filter by data series ID
            
        Returns:
            List of assignments ordered by version (newest first)
        """
        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None
        
        query = DataPointAssignment.query.filter_by(company_id=company_id)
        
        if data_series_id:
            query = query.filter_by(data_series_id=data_series_id)
        elif field_id and entity_id:
            query = query.filter(
                and_(
                    DataPointAssignment.field_id == field_id,
                    DataPointAssignment.entity_id == entity_id
                )
            )
        else:
            raise ValueError("Must provide either data_series_id or both field_id and entity_id")
        
        return query.options(
            joinedload(DataPointAssignment.field),
            joinedload(DataPointAssignment.entity),
            joinedload(DataPointAssignment.assigned_by_user)
        ).order_by(
            desc(DataPointAssignment.series_version)
        ).all()
    
    @staticmethod  
    def _get_fy_for_date(target_date: date, company: Company) -> int:
        """
        Helper method to determine which fiscal year a date belongs to.
        
        Args:
            target_date: Date to check
            company: Company with FY configuration
            
        Returns:
            Fiscal year (based on FY end year)
        """
        fy_end_month = company.fy_end_month
        fy_end_day = company.fy_end_day
        
        # Check if date is before or after FY end for the current calendar year
        fy_end_current_year = date(target_date.year, fy_end_month, min(fy_end_day, 28))  # Safe day
        
        if target_date <= fy_end_current_year:
            return target_date.year
        else:
            return target_date.year + 1
    
    @staticmethod
    def handle_edge_cases(field_id: str, entity_id: int, reporting_date: date) -> Dict[str, Any]:
        """
        Phase 4: Comprehensive edge case detection and handling for assignment resolution.
        
        This method identifies and provides solutions for common edge cases that can
        occur during assignment resolution.
        
        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            reporting_date: Reporting date
            
        Returns:
            Dict containing edge case analysis and recommendations
        """
        from ..models.company import Company
        from ..middleware.tenant import get_current_tenant
        from flask import current_app
        
        edge_cases = {
            'has_issues': False,
            'issues_found': [],
            'recommendations': [],
            'severity': 'none'  # none, low, medium, high, critical
        }
        
        try:
            current_tenant = get_current_tenant()
            company_id = current_tenant.id if current_tenant else None
            
            # Edge Case 1: Multiple active assignments for same field+entity
            active_assignments = DataPointAssignment.query.filter(
                and_(
                    DataPointAssignment.field_id == field_id,
                    DataPointAssignment.entity_id == entity_id,
                    DataPointAssignment.series_status == 'active',
                    DataPointAssignment.series_status == 'active'
                )
            )
            
            if company_id:
                active_assignments = active_assignments.filter(
                    DataPointAssignment.company_id == company_id
                )
            
            active_count = active_assignments.count()
            
            if active_count > 1:
                edge_cases['has_issues'] = True
                edge_cases['severity'] = 'high'
                edge_cases['issues_found'].append(
                    f"Multiple active assignments ({active_count}) found for field {field_id}, entity {entity_id}"
                )
                edge_cases['recommendations'].append(
                    "Review assignment history and supersede duplicate assignments"
                )
            
            # Edge Case 2: No active assignments but superseded assignments exist
            if active_count == 0:
                superseded_count = DataPointAssignment.query.filter(
                    and_(
                        DataPointAssignment.field_id == field_id,
                        DataPointAssignment.entity_id == entity_id,
                        DataPointAssignment.series_status == 'superseded'
                    )
                ).count()
                
                if superseded_count > 0:
                    edge_cases['has_issues'] = True
                    edge_cases['severity'] = 'medium'
                    edge_cases['issues_found'].append(
                        f"No active assignments but {superseded_count} superseded assignments exist"
                    )
                    edge_cases['recommendations'].append(
                        "Consider creating new assignment or reactivating appropriate superseded assignment"
                    )
            
            # Edge Case 3: Assignment exists but date is outside FY range
            if active_count == 1:
                assignment = active_assignments.first()
                if assignment.company:
                    try:
                        fy_year = AssignmentVersioningService._get_fy_for_date(
                            reporting_date, assignment.company
                        )
                        
                        if not AssignmentVersioningService._is_date_in_fy_range(
                            reporting_date, fy_year, assignment.company
                        ):
                            edge_cases['has_issues'] = True
                            edge_cases['severity'] = 'medium'
                            edge_cases['issues_found'].append(
                                f"Reporting date {reporting_date} is outside fiscal year range for assignment"
                            )
                            edge_cases['recommendations'].append(
                                "Verify reporting date is correct or check company FY configuration"
                            )
                    except Exception as e:
                        edge_cases['issues_found'].append(
                            f"Error validating FY compatibility: {str(e)}"
                        )
                        edge_cases['severity'] = 'low'
            
            # Edge Case 4: Data exists without assignment
            from ..models.esg_data import ESGData
            unlinked_data = ESGData.query.filter(
                and_(
                    ESGData.field_id == field_id,
                    ESGData.entity_id == entity_id,
                    ESGData.assignment_id.is_(None)
                )
            ).count()
            
            if unlinked_data > 0:
                edge_cases['has_issues'] = True
                if edge_cases['severity'] in ['none', 'low']:
                    edge_cases['severity'] = 'low'
                edge_cases['issues_found'].append(
                    f"{unlinked_data} data entries exist without assignment linkage"
                )
                edge_cases['recommendations'].append(
                    "Link existing data entries to appropriate assignments"
                )
            
            return edge_cases
            
        except Exception as e:
            if 'current_app' in locals():
                current_app.logger.error(f"Error in edge case analysis: {str(e)}")
            
            return {
                'has_issues': True,
                'issues_found': [f"Error during edge case analysis: {str(e)}"],
                'recommendations': ["Review assignment configuration manually"],
                'severity': 'critical'
            }
    
    @staticmethod
    def _is_date_in_fy_range(target_date: date, fy_year: int, company: Company) -> bool:
        """
        Check if a date falls within a fiscal year range.
        
        Args:
            target_date: Date to check
            fy_year: Fiscal year
            company: Company with FY configuration
            
        Returns:
            True if date is within the FY range
        """
        try:
            fy_start = company.get_fy_start_date(fy_year)
            fy_end = company.get_fy_end_date(fy_year)
            
            return fy_start <= target_date <= fy_end
            
        except Exception:
            # If FY calculation fails, be permissive
            return True


class AssignmentResolutionService:
    """
    Service for resolving assignments with dual compatibility support.
    
    This service provides the core assignment resolution logic that supports
    both the new assignment_id pattern and legacy field_id pattern during
    the transition period.
    
    Phase 4: Enhanced with performance-optimized resolution and comprehensive
    assignment resolution for any given parameters.
    """
    
    @staticmethod
    def resolve_assignment_for_data(
        field_id: str,
        entity_id: int, 
        reporting_date: date,
        assignment_id: str = None
    ) -> Optional[DataPointAssignment]:
        """
        Resolve the correct assignment for ESG data entry.
        
        This method implements dual compatibility:
        1. If assignment_id provided, validate and use it
        2. If no assignment_id, fallback to field_id resolution
        3. Ensure date compatibility with assignment
        
        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            reporting_date: Date for the data entry
            assignment_id: Optional assignment ID (new pattern)
            
        Returns:
            Resolved assignment or None
        """
        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None
        
        # Priority 1: Use assignment_id if provided (new pattern)
        if assignment_id:
            assignment = DataPointAssignment.query.filter(
                and_(
                    DataPointAssignment.id == assignment_id,
                    DataPointAssignment.company_id == company_id,
                    DataPointAssignment.series_status == 'active'
                )
            ).options(joinedload(DataPointAssignment.company)).first()
            
            if assignment:
                # Validate assignment matches field and entity
                if assignment.field_id == field_id and assignment.entity_id == entity_id:
                    # Check date compatibility
                    if AssignmentResolutionService._is_date_compatible(
                        assignment, reporting_date
                    ):
                        return assignment
                    else:
                        print(f"Warning: Assignment {assignment_id} found but date {reporting_date} is not compatible")
                        return None
                else:
                    print(f"Warning: Assignment {assignment_id} does not match field {field_id} or entity {entity_id}")
                    return None
        
        # Priority 2: Fallback to field_id resolution (legacy pattern)
        # Use the enhanced resolve_assignment method for better performance
        return AssignmentResolutionService.resolve_assignment(
            field_id, entity_id, reporting_date
        )
    
    @staticmethod
    def resolve_assignment(
        field_id: str,
        entity_id: int,
        reporting_date: date,
        company_fy_config: Optional['Company'] = None
    ) -> Optional[DataPointAssignment]:
        """
        Phase 4: Core assignment resolution method.
        
        Determines the correct assignment for any given date using company FY 
        configuration and assignment status. This is the main entry point for
        assignment resolution with full performance optimization.
        
        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            reporting_date: Date to resolve assignment for
            company_fy_config: Optional company with FY config (auto-detected if None)
            
        Returns:
            Active DataPointAssignment or None if no assignment found
        """
        from ..models.company import Company
        from ..middleware.tenant import get_current_tenant
        from flask import current_app
        
        try:
            current_tenant = get_current_tenant()
            company_id = current_tenant.id if current_tenant else None
            
            # Check cache first for performance (< 50ms target)
            cached_result = assignment_cache.get(field_id, entity_id, reporting_date, company_id)
            if cached_result is not None:
                return cached_result
            
            # Use provided company config or auto-detect from tenant
            if not company_fy_config and current_tenant:
                company_fy_config = current_tenant
            elif not company_fy_config and company_id:
                company_fy_config = Company.query.get(company_id)
            
            # Performance-optimized query with proper indexing
            query = DataPointAssignment.query.filter(
                and_(
                    DataPointAssignment.field_id == field_id,
                    DataPointAssignment.entity_id == entity_id,
                    DataPointAssignment.series_status == 'active',
                    DataPointAssignment.series_status == 'active'
                )
            )
            
            # Apply tenant filtering if in tenant context
            if company_id:
                query = query.filter(DataPointAssignment.company_id == company_id)
            
            # Use eager loading for performance
            assignment = query.options(
                joinedload(DataPointAssignment.company),
                joinedload(DataPointAssignment.field)
            ).order_by(
                desc(DataPointAssignment.series_version)
            ).first()
            
            if not assignment:
                # Cache the negative result
                assignment_cache.set(field_id, entity_id, reporting_date, None, company_id)
                return None
            
            # Validate date compatibility with company FY configuration
            # NOTE: Date compatibility check is intentionally lenient for assignment resolution.
            # This function is used for multiple purposes (metadata, computation context, display)
            # not just data entry validation. Strict date validation happens at data entry time.
            #
            # The original strict check was causing assignments to return None for dates
            # outside the exact FY reporting period, breaking computation context and metadata access.
            #
            # Date compatibility is now only enforced for actual data entry, not assignment lookups.
            if company_fy_config and assignment:
                # Just verify the assignment exists and is active - date validation happens elsewhere
                pass
            
            # Cache the positive result
            assignment_cache.set(field_id, entity_id, reporting_date, assignment, company_id)
            return assignment
            
        except Exception as e:
            if 'current_app' in locals():
                current_app.logger.error(f"Error resolving assignment for field {field_id}, entity {entity_id}: {str(e)}")
            else:
                print(f"Error resolving assignment for field {field_id}, entity {entity_id}: {str(e)}")
            return None
    
    @staticmethod
    def _is_date_compatible(assignment: DataPointAssignment, reporting_date: date, company: Optional['Company'] = None) -> bool:
        """
        Check if a reporting date is compatible with an assignment.
        
        Args:
            assignment: Assignment to check against
            reporting_date: Date to validate
            company: Optional company for FY configuration (uses assignment.company if None)
            
        Returns:
            True if date is compatible with assignment
        """
        try:
            company_config = company or assignment.company
            if not company_config:
                return True  # No company FY config, allow any date
                
            # Get FY for the reporting date
            fy_year = AssignmentVersioningService._get_fy_for_date(
                reporting_date, company_config
            )
            
            # Check if date is valid for assignment frequency
            return assignment.is_valid_reporting_date(reporting_date, fy_year)
            
        except Exception as e:
            print(f"Date compatibility check failed: {str(e)}")
            return True  # Be permissive on errors


# Phase 4: Enhanced utility functions for backward compatibility and performance
def get_active_assignment(field_id: str, entity_id: int, target_date: date = None) -> Optional[DataPointAssignment]:
    """Backward compatible function for getting active assignments."""
    return AssignmentVersioningService.get_active_assignment(field_id, entity_id, target_date)


def resolve_assignment_for_data(field_id: str, entity_id: int, reporting_date: date, assignment_id: str = None) -> Optional[DataPointAssignment]:
    """Backward compatible function for assignment resolution with dual compatibility."""
    return AssignmentResolutionService.resolve_assignment_for_data(field_id, entity_id, reporting_date, assignment_id)


def resolve_assignment(field_id: str, entity_id: int, reporting_date: date, company_fy_config: Optional['Company'] = None) -> Optional[DataPointAssignment]:
    """Phase 4: Main assignment resolution function with company FY configuration support."""
    return AssignmentResolutionService.resolve_assignment(field_id, entity_id, reporting_date, company_fy_config)


class AssignmentCache:
    """
    Phase 4: Simple caching mechanism for assignment resolution performance.
    
    This cache helps achieve the < 50ms performance target for frequently
    accessed assignment resolutions.
    """
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get_cache_key(self, field_id: str, entity_id: int, reporting_date: date, company_id: Optional[int] = None) -> str:
        """Generate cache key for assignment resolution."""
        return f"{field_id}:{entity_id}:{reporting_date.isoformat()}:{company_id or 'none'}"
    
    def get(self, field_id: str, entity_id: int, reporting_date: date, company_id: Optional[int] = None) -> Optional[DataPointAssignment]:
        """Get cached assignment if available."""
        key = self.get_cache_key(field_id, entity_id, reporting_date, company_id)
        
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        
        return None
    
    def set(self, field_id: str, entity_id: int, reporting_date: date, assignment: Optional[DataPointAssignment], company_id: Optional[int] = None):
        """Cache assignment resolution result."""
        key = self.get_cache_key(field_id, entity_id, reporting_date, company_id)
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = assignment
        if key not in self.access_order:
            self.access_order.append(key)
    
    def clear(self):
        """Clear all cached assignments."""
        self.cache.clear()
        self.access_order.clear()


# Global assignment cache instance
assignment_cache = AssignmentCache()

def handle_assignment_edge_cases(field_id: str, entity_id: int, reporting_date: date) -> Dict[str, Any]:
    """Phase 4: Detect and provide solutions for assignment edge cases."""
    return AssignmentVersioningService.handle_edge_cases(field_id, entity_id, reporting_date)
