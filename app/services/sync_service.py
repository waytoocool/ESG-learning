"""
Multi-tenant synchronization services for T-8 implementation.

This module contains services for managing cross-tenant synchronization
operations including framework sync, tenant templates, and data migration.
"""

from flask import current_app
from ..extensions import db
from ..models.sync_operation import SyncOperation, FrameworkSyncJob, TenantTemplate, DataMigrationJob
from ..models.framework import Framework, FrameworkDataField, FieldVariableMapping
from ..models.company import Company
from ..models.entity import Entity
from ..models.esg_data import ESGData
from ..models.data_assignment import DataPointAssignment
from ..models.audit_log import AuditLog
from datetime import datetime
import json
import copy
from typing import List, Dict, Optional, Tuple


class FrameworkSyncService:
    """
    Service for synchronizing frameworks across tenants.
    
    This service handles the distribution of framework updates from
    a source tenant to multiple target tenants, including conflict
    detection and resolution.
    """
    
    @staticmethod
    def create_sync_job(framework_id: str, target_company_ids: List[int], 
                       initiated_by: int, source_company_id: Optional[int] = None,
                       sync_options: Optional[Dict] = None, 
                       conflict_resolution: str = 'SKIP') -> str:
        """
        Create a new framework synchronization job.
        
        Args:
            framework_id: ID of the framework to sync
            target_company_ids: List of target company IDs
            initiated_by: User ID who initiated the sync
            source_company_id: Source company ID (None for global frameworks)
            sync_options: Configuration options for sync
            conflict_resolution: How to handle conflicts ('SKIP', 'OVERWRITE', 'MERGE')
            
        Returns:
            str: ID of the created sync operation
        """
        try:
            # Create base sync operation
            sync_operation = SyncOperation(
                operation_type='FRAMEWORK_SYNC',
                initiated_by=initiated_by,
                source_id=framework_id,
                target_ids=target_company_ids,
                parameters={
                    'sync_options': sync_options or {},
                    'conflict_resolution': conflict_resolution
                }
            )
            
            db.session.add(sync_operation)
            db.session.flush()  # Get the ID
            
            # Create specialized framework sync job
            framework_sync_job = FrameworkSyncJob(
                sync_operation_id=sync_operation.id,
                framework_id=framework_id,
                target_company_ids=target_company_ids,
                source_company_id=source_company_id,
                sync_options=sync_options,
                conflict_resolution=conflict_resolution
            )
            
            db.session.add(framework_sync_job)
            
            # Log audit action
            AuditLog.log_action(
                user_id=initiated_by,
                action='CREATE_FRAMEWORK_SYNC_JOB',
                entity_type='FrameworkSyncJob',
                entity_id=framework_sync_job.id,
                payload={
                    'framework_id': framework_id,
                    'target_companies': target_company_ids,
                    'conflict_resolution': conflict_resolution
                }
            )
            
            db.session.commit()
            
            current_app.logger.info(f'Framework sync job created: {sync_operation.id}')
            return sync_operation.id
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating framework sync job: {str(e)}')
            raise
    
    @staticmethod
    def execute_sync_job(sync_operation_id: str) -> bool:
        """
        Execute a framework synchronization job.
        
        Args:
            sync_operation_id: ID of the sync operation to execute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get sync operation and framework sync job
            sync_operation = SyncOperation.query.get(sync_operation_id)
            if not sync_operation:
                raise ValueError(f"Sync operation {sync_operation_id} not found")
            
            framework_sync_job = FrameworkSyncJob.query.filter_by(
                sync_operation_id=sync_operation_id
            ).first()
            
            if not framework_sync_job:
                raise ValueError(f"Framework sync job for operation {sync_operation_id} not found")
            
            # Start the operation
            sync_operation.start_operation()
            db.session.commit()
            
            # Get source framework
            source_framework = Framework.query.get(framework_sync_job.framework_id)
            if not source_framework:
                sync_operation.complete_operation(False, "Source framework not found")
                db.session.commit()
                return False
            
            # Process each target company
            total_targets = len(framework_sync_job.target_company_ids)
            successful_syncs = 0
            
            for i, company_id in enumerate(framework_sync_job.target_company_ids):
                try:
                    # Update progress
                    progress = int((i / total_targets) * 100)
                    sync_operation.update_progress(
                        progress, 
                        f"Processing company {company_id} ({i+1}/{total_targets})"
                    )
                    db.session.commit()
                    
                    # Sync framework to this company
                    success = FrameworkSyncService._sync_framework_to_company(
                        source_framework, company_id, framework_sync_job
                    )
                    
                    if success:
                        successful_syncs += 1
                    
                except Exception as e:
                    current_app.logger.error(f'Error syncing to company {company_id}: {str(e)}')
                    framework_sync_job.add_conflict(
                        company_id, 'SYNC_ERROR', {'error': str(e)}
                    )
            
            # Complete the operation
            success_rate = successful_syncs / total_targets if total_targets > 0 else 0
            overall_success = success_rate >= 0.8  # 80% success rate threshold
            
            if overall_success:
                sync_operation.complete_operation(True)
                sync_operation.add_log_entry(
                    'INFO', 
                    f'Sync completed successfully: {successful_syncs}/{total_targets} targets'
                )
            else:
                sync_operation.complete_operation(
                    False, 
                    f'Sync failed: only {successful_syncs}/{total_targets} targets successful'
                )
            
            db.session.commit()
            return overall_success
            
        except Exception as e:
            if 'sync_operation' in locals():
                sync_operation.complete_operation(False, str(e))
                db.session.commit()
            
            current_app.logger.error(f'Error executing sync job: {str(e)}')
            return False
    
    @staticmethod
    def _sync_framework_to_company(source_framework: Framework, target_company_id: int, 
                                 framework_sync_job: FrameworkSyncJob) -> bool:
        """
        Sync a framework to a specific company.
        
        Args:
            source_framework: The framework to sync
            target_company_id: Target company ID
            framework_sync_job: The sync job configuration
            
        Returns:
            bool: True if successful
        """
        try:
            # Check if framework already exists in target company
            existing_framework = Framework.query.filter_by(
                framework_name=source_framework.framework_name
            ).first()
            
            # Handle conflicts based on resolution strategy
            if existing_framework:
                if framework_sync_job.conflict_resolution == 'SKIP':
                    framework_sync_job.add_conflict(
                        target_company_id, 
                        'FRAMEWORK_EXISTS', 
                        {'framework_name': source_framework.framework_name}
                    )
                    return False
                
                elif framework_sync_job.conflict_resolution == 'OVERWRITE':
                    # Delete existing framework and its fields
                    FrameworkSyncService._delete_framework_safely(existing_framework)
                
                elif framework_sync_job.conflict_resolution == 'MERGE':
                    # Implement merge logic (for now, skip)
                    framework_sync_job.add_conflict(
                        target_company_id, 
                        'MERGE_NOT_IMPLEMENTED', 
                        {'framework_name': source_framework.framework_name}
                    )
                    return False
            
            # Create framework copy
            new_framework = Framework(
                framework_name=source_framework.framework_name,
                description=source_framework.description
            )
            
            db.session.add(new_framework)
            db.session.flush()  # Get the new framework ID
            
            # Copy framework fields
            source_fields = FrameworkDataField.query.filter_by(
                framework_id=source_framework.framework_id
            ).all()
            
            field_id_mapping = {}
            
            for source_field in source_fields:
                new_field = FrameworkDataField(
                    framework_id=new_framework.framework_id,
                    field_name=source_field.field_name,
                    field_type=source_field.field_type,
                    default_unit=source_field.default_unit,
                    is_computed=source_field.is_computed,
                    aggregation_formula=source_field.aggregation_formula,
                    field_order=source_field.field_order,
                    is_required=source_field.is_required,
                    description=source_field.description
                )
                
                db.session.add(new_field)
                db.session.flush()
                
                # Track field ID mapping for computed fields
                field_id_mapping[source_field.field_id] = new_field.field_id
            
            # Copy field variable mappings for computed fields
            source_mappings = FieldVariableMapping.query.filter(
                FieldVariableMapping.computed_field_id.in_(field_id_mapping.keys())
            ).all()
            
            for source_mapping in source_mappings:
                if (source_mapping.computed_field_id in field_id_mapping and 
                    source_mapping.raw_field_id in field_id_mapping):
                    
                    new_mapping = FieldVariableMapping(
                        computed_field_id=field_id_mapping[source_mapping.computed_field_id],
                        raw_field_id=field_id_mapping[source_mapping.raw_field_id],
                        variable_name=source_mapping.variable_name
                    )
                    
                    db.session.add(new_mapping)
            
            # Create data points for the target company
            source_data_points = DataPointAssignment.query.filter_by(
                framework_id=source_framework.framework_id
            ).all()
            
            for source_dp in source_data_points:
                new_data_point = DataPointAssignment(
                    name=source_dp.name,
                    value_type=source_dp.value_type,
                    framework_id=new_framework.framework_id,
                    company_id=target_company_id
                )
                
                db.session.add(new_data_point)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error syncing framework to company {target_company_id}: {str(e)}')
            return False
    
    @staticmethod
    def _delete_framework_safely(framework: Framework):
        """
        Safely delete a framework and its dependencies.
        
        Args:
            framework: Framework to delete
        """
        try:
            # Delete field variable mappings
            field_ids = [field.field_id for field in framework.fields]
            if field_ids:
                FieldVariableMapping.query.filter(
                    FieldVariableMapping.computed_field_id.in_(field_ids)
                ).delete()
                
                FieldVariableMapping.query.filter(
                    FieldVariableMapping.raw_field_id.in_(field_ids)
                ).delete()
            
            # Delete data points
            DataPointAssignment.query.filter_by(framework_id=framework.framework_id).delete()
            
            # Delete framework fields
            FrameworkDataField.query.filter_by(framework_id=framework.framework_id).delete()
            
            # Delete framework
            db.session.delete(framework)
            
        except Exception as e:
            current_app.logger.error(f'Error deleting framework {framework.framework_id}: {str(e)}')
            raise
    
    @staticmethod
    def get_sync_job_status(sync_operation_id: str) -> Optional[Dict]:
        """
        Get the status of a sync job.
        
        Args:
            sync_operation_id: ID of the sync operation
            
        Returns:
            Dict containing job status information
        """
        sync_operation = SyncOperation.query.get(sync_operation_id)
        if not sync_operation:
            return None
        
        framework_sync_job = FrameworkSyncJob.query.filter_by(
            sync_operation_id=sync_operation_id
        ).first()
        
        return {
            'id': sync_operation.id,
            'status': sync_operation.status,
            'progress_percentage': sync_operation.progress_percentage,
            'started_at': sync_operation.started_at.isoformat() if sync_operation.started_at else None,
            'completed_at': sync_operation.completed_at.isoformat() if sync_operation.completed_at else None,
            'duration': sync_operation.get_duration(),
            'error_message': sync_operation.error_message,
            'log_entries': sync_operation.log_data or [],
            'framework_id': framework_sync_job.framework_id if framework_sync_job else None,
            'target_count': len(framework_sync_job.target_company_ids) if framework_sync_job else 0,
            'conflicts': framework_sync_job.conflicts_detected if framework_sync_job else []
        }
    
    @staticmethod
    def get_framework_conflicts(framework_id: str, target_company_ids: List[int]) -> List[Dict]:
        """
        Detect potential conflicts before syncing a framework.
        
        Args:
            framework_id: Source framework ID
            target_company_ids: List of target company IDs
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            source_framework = Framework.query.get(framework_id)
            if not source_framework:
                return [{'type': 'SOURCE_NOT_FOUND', 'details': 'Source framework not found'}]
            
            for company_id in target_company_ids:
                company = Company.query.get(company_id)
                if not company:
                    conflicts.append({
                        'company_id': company_id,
                        'type': 'COMPANY_NOT_FOUND',
                        'details': 'Target company not found'
                    })
                    continue
                
                # Check if framework name already exists
                existing_framework = Framework.query.filter_by(
                    framework_name=source_framework.framework_name
                ).first()
                
                if existing_framework:
                    conflicts.append({
                        'company_id': company_id,
                        'type': 'FRAMEWORK_EXISTS',
                        'details': {
                            'framework_name': source_framework.framework_name,
                            'existing_framework_id': existing_framework.framework_id
                        }
                    })
                
                # Check for data point name conflicts
                source_data_points = DataPointAssignment.query.filter_by(
                    framework_id=source_framework.framework_id
                ).all()
                
                existing_data_points = DataPointAssignment.query.filter_by(
                    company_id=company_id
                ).all()
                
                existing_dp_names = {dp.name for dp in existing_data_points}
                
                for source_dp in source_data_points:
                    if source_dp.name in existing_dp_names:
                        conflicts.append({
                            'company_id': company_id,
                            'type': 'DATA_POINT_EXISTS',
                            'details': {
                                'data_point_name': source_dp.name
                            }
                        })
            
            return conflicts
            
        except Exception as e:
            current_app.logger.error(f'Error detecting conflicts: {str(e)}')
            return [{'type': 'ERROR', 'details': str(e)}]


class TenantTemplateService:
    """
    Service for managing tenant templates and provisioning.
    
    This service handles creating templates from existing tenants
    and provisioning new tenants from templates.
    """
    
    @staticmethod
    def create_template_from_tenant(company_id: int, template_name: str, 
                                  created_by: int, description: Optional[str] = None,
                                  industry: Optional[str] = None, 
                                  is_public: bool = False) -> str:
        """
        Create a template from an existing tenant.
        
        Args:
            company_id: Source company ID
            template_name: Name for the new template
            created_by: User ID who created the template
            description: Template description
            industry: Industry category
            is_public: Whether template is public
            
        Returns:
            str: ID of the created template
        """
        try:
            # Get source company
            source_company = Company.query.get(company_id)
            if not source_company:
                raise ValueError(f"Company {company_id} not found")
            
            # Extract tenant data
            template_data = TenantTemplateService._extract_tenant_data(company_id)
            
            # Create template
            template = TenantTemplate(
                name=template_name,
                template_data=template_data,
                created_by=created_by,
                description=description,
                industry=industry,
                source_company_id=company_id,
                is_public=is_public
            )
            
            db.session.add(template)
            
            # Log audit action
            AuditLog.log_action(
                user_id=created_by,
                action='CREATE_TENANT_TEMPLATE',
                entity_type='TenantTemplate',
                entity_id=template.id,
                payload={
                    'template_name': template_name,
                    'source_company_id': company_id,
                    'is_public': is_public
                }
            )
            
            db.session.commit()
            
            current_app.logger.info(f'Tenant template created: {template.id}')
            return template.id
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating tenant template: {str(e)}')
            raise
    
    @staticmethod
    def _extract_tenant_data(company_id: int) -> Dict:
        """
        Extract data from a tenant for template creation.
        
        Args:
            company_id: Company ID to extract data from
            
        Returns:
            Dict containing tenant data
        """
        try:
            template_data = {
                'frameworks': [],
                'data_points': [],
                'entities': [],
                'assignments': [],
                'settings': {}
            }
            
            # Extract frameworks (only those with data points for this company)
            data_points = DataPointAssignment.query.filter_by(company_id=company_id).all()
            framework_ids = list(set(dp.framework_id for dp in data_points))
            
            for framework_id in framework_ids:
                framework = Framework.query.get(framework_id)
                if framework:
                    framework_data = {
                        'framework_name': framework.framework_name,
                        'description': framework.description,
                        'fields': []
                    }
                    
                    # Extract framework fields
                    fields = FrameworkDataField.query.filter_by(
                        framework_id=framework_id
                    ).all()
                    
                    for field in fields:
                        field_data = {
                            'field_name': field.field_name,
                            'field_type': field.field_type,
                            'unit': field.default_unit,
                            'is_computed': field.is_computed,
                            'aggregation_formula': field.aggregation_formula,
                            'field_order': field.field_order,
                            'is_required': field.is_required,
                            'description': field.description
                        }
                        framework_data['fields'].append(field_data)
                    
                    template_data['frameworks'].append(framework_data)
            
            # Extract data points
            for dp in data_points:
                dp_data = {
                    'name': dp.name,
                    'value_type': dp.value_type,
                    'unit': dp.effective_unit,
                    'framework_name': dp.framework.framework_name if dp.framework else None
                }
                template_data['data_points'].append(dp_data)
            
            # Extract entities
            entities = Entity.query.filter_by(company_id=company_id).all()
            for entity in entities:
                entity_data = {
                    'name': entity.name,
                    'entity_type': entity.entity_type,
                    'parent_id': None  # Will be resolved during provisioning
                }
                template_data['entities'].append(entity_data)
            
            # Extract data point assignments
            assignments = DataPointAssignment.query.filter_by(company_id=company_id).all()
            for assignment in assignments:
                assignment_data = {
                    'data_point_name': assignment.data_point.name if assignment.data_point else None,
                    'entity_name': assignment.entity.name if assignment.entity else None,
                    'frequency': assignment.frequency
                }
                template_data['assignments'].append(assignment_data)
            
            return template_data
            
        except Exception as e:
            current_app.logger.error(f'Error extracting tenant data: {str(e)}')
            raise
    
    @staticmethod
    def provision_tenant_from_template(template_id: str, new_company_name: str, 
                                     new_company_slug: str, initiated_by: int) -> str:
        """
        Provision a new tenant from a template.
        
        Args:
            template_id: Template ID to use
            new_company_name: Name for the new company
            new_company_slug: Slug for the new company
            initiated_by: User ID who initiated provisioning
            
        Returns:
            str: ID of the created sync operation
        """
        try:
            # Get template
            template = TenantTemplate.query.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Validate template data
            is_valid, error_message = template.validate_template_data()
            if not is_valid:
                raise ValueError(f"Invalid template data: {error_message}")
            
            # Create sync operation
            sync_operation = SyncOperation(
                operation_type='TENANT_CLONE',
                initiated_by=initiated_by,
                source_id=template_id,
                parameters={
                    'new_company_name': new_company_name,
                    'new_company_slug': new_company_slug
                }
            )
            
            db.session.add(sync_operation)
            db.session.flush()
            
            # Log audit action
            AuditLog.log_action(
                user_id=initiated_by,
                action='START_TENANT_PROVISIONING',
                entity_type='SyncOperation',
                entity_id=sync_operation.id,
                payload={
                    'template_id': template_id,
                    'new_company_name': new_company_name,
                    'new_company_slug': new_company_slug
                }
            )
            
            db.session.commit()
            
            # Increment template usage
            template.increment_usage()
            db.session.commit()
            
            current_app.logger.info(f'Tenant provisioning started: {sync_operation.id}')
            return sync_operation.id
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error starting tenant provisioning: {str(e)}')
            raise 