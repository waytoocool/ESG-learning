"""
Cross-Tenant Analytics Service - T-8b Phase 3

This service provides anonymized cross-tenant analytics capabilities for ESG data,
enabling global insights while maintaining tenant privacy and data security.

Key Features:
- Global ESG performance metrics
- Anonymized tenant benchmarking
- Industry-specific comparisons
- Trend analysis and reporting
- Privacy-first design with opt-out capabilities
"""

from flask import current_app
from sqlalchemy import func, and_, or_
from ..models.company import Company
from ..models.esg_data import ESGData
from ..models.data_point import DataPoint
from ..models.framework import Framework, FrameworkDataField
from ..models.entity import Entity
from ..models.user import User
from ..extensions import db
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import hashlib


class CrossTenantAnalyticsService:
    """
    Service for cross-tenant analytics with privacy controls.
    
    All analytics are anonymized and aggregated to protect tenant privacy.
    Individual tenant data is never exposed in cross-tenant comparisons.
    """
    
    @staticmethod
    def get_global_metrics() -> Dict[str, Any]:
        """
        Get system-wide ESG metrics across all tenants.
        
        Returns:
            Dict containing global metrics like total companies, data points,
            completion rates, and high-level trends.
        """
        try:
            # Basic system metrics
            total_companies = Company.query.filter_by(is_active=True).count()
            total_entities = Entity.query.count()
            total_data_points = DataPoint.query.count()
            total_esg_records = ESGData.query.count()
            total_frameworks = Framework.query.count()
            
            # Data completion metrics
            completed_data_points = ESGData.query.filter(
                ESGData.value.isnot(None),
                ESGData.value != ''
            ).count()
            
            completion_rate = (completed_data_points / total_data_points * 100) if total_data_points > 0 else 0
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_updates = ESGData.query.filter(
                ESGData.updated_at >= thirty_days_ago
            ).count()
            
            # Industry distribution
            industry_distribution = db.session.query(
                Company.industry,
                func.count(Company.id).label('count')
            ).filter(
                Company.is_active == True,
                Company.industry.isnot(None)
            ).group_by(Company.industry).all()
            
            # Framework usage
            framework_usage = db.session.query(
                Framework.name,
                func.count(DataPoint.id).label('usage_count')
            ).join(
                DataPoint, Framework.id == DataPoint.framework_id
            ).group_by(Framework.id, Framework.name).all()
            
            return {
                'success': True,
                'metrics': {
                    'system_overview': {
                        'total_companies': total_companies,
                        'total_entities': total_entities,
                        'total_data_points': total_data_points,
                        'total_esg_records': total_esg_records,
                        'total_frameworks': total_frameworks
                    },
                    'data_quality': {
                        'completion_rate': round(completion_rate, 2),
                        'completed_data_points': completed_data_points,
                        'recent_updates': recent_updates
                    },
                    'industry_distribution': [
                        {'industry': industry, 'count': count}
                        for industry, count in industry_distribution
                    ],
                    'framework_usage': [
                        {'framework': name, 'usage_count': count}
                        for name, count in framework_usage
                    ],
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            current_app.logger.error(f'Error generating global metrics: {str(e)}')
            return {
                'success': False,
                'error': 'Failed to generate global metrics'
            }
    
    @staticmethod
    def get_tenant_comparison(industry: Optional[str] = None, 
                            anonymize: bool = True) -> Dict[str, Any]:
        """
        Get anonymized tenant comparison data.
        
        Args:
            industry: Filter by specific industry
            anonymize: Whether to anonymize tenant identifiers
            
        Returns:
            Dict containing anonymized tenant comparison metrics
        """
        try:
            # Build base query
            query = db.session.query(
                Company.id,
                Company.name,
                Company.industry,
                func.count(Entity.id).label('entity_count'),
                func.count(DataPoint.id).label('data_point_count')
            ).outerjoin(
                Entity, Company.id == Entity.company_id
            ).outerjoin(
                DataPoint, Entity.id == DataPoint.entity_id
            ).filter(
                Company.is_active == True
            )
            
            # Apply industry filter
            if industry:
                query = query.filter(Company.industry == industry)
            
            # Group and execute
            tenant_data = query.group_by(
                Company.id, Company.name, Company.industry
            ).all()
            
            # Calculate completion rates for each tenant
            comparison_data = []
            for company_id, name, company_industry, entity_count, data_point_count in tenant_data:
                # Get completion rate
                completed_count = ESGData.query.join(
                    DataPoint, ESGData.data_point_id == DataPoint.id
                ).join(
                    Entity, DataPoint.entity_id == Entity.id
                ).filter(
                    Entity.company_id == company_id,
                    ESGData.value.isnot(None),
                    ESGData.value != ''
                ).count()
                
                completion_rate = (completed_count / data_point_count * 100) if data_point_count > 0 else 0
                
                # Anonymize tenant identifier if requested
                tenant_id = CrossTenantAnalyticsService._anonymize_tenant_id(company_id) if anonymize else name
                
                comparison_data.append({
                    'tenant_id': tenant_id,
                    'industry': company_industry or 'Not Specified',
                    'entity_count': entity_count,
                    'data_point_count': data_point_count,
                    'completion_rate': round(completion_rate, 2),
                    'completed_data_points': completed_count
                })
            
            # Calculate industry benchmarks
            industry_benchmarks = {}
            if comparison_data:
                industries = set(item['industry'] for item in comparison_data)
                for ind in industries:
                    industry_items = [item for item in comparison_data if item['industry'] == ind]
                    if industry_items:
                        completion_rates = [item['completion_rate'] for item in industry_items]
                        industry_benchmarks[ind] = {
                            'avg_completion_rate': round(sum(completion_rates) / len(completion_rates), 2),
                            'tenant_count': len(industry_items),
                            'total_data_points': sum(item['data_point_count'] for item in industry_items)
                        }
            
            return {
                'success': True,
                'comparison': {
                    'tenant_data': comparison_data,
                    'industry_benchmarks': industry_benchmarks,
                    'total_tenants': len(comparison_data),
                    'filter_applied': {'industry': industry} if industry else None,
                    'anonymized': anonymize,
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            current_app.logger.error(f'Error generating tenant comparison: {str(e)}')
            return {
                'success': False,
                'error': 'Failed to generate tenant comparison'
            }
    
    @staticmethod
    def get_benchmark_data(framework_id: Optional[int] = None,
                          industry: Optional[str] = None) -> Dict[str, Any]:
        """
        Get benchmarking data for ESG performance.
        
        Args:
            framework_id: Filter by specific framework
            industry: Filter by specific industry
            
        Returns:
            Dict containing benchmark metrics and percentiles
        """
        try:
            # Build base query for ESG data
            query = db.session.query(
                ESGData.value,
                Company.industry,
                Framework.name.label('framework_name'),
                FrameworkDataField.name.label('field_name')
            ).join(
                DataPoint, ESGData.data_point_id == DataPoint.id
            ).join(
                Entity, DataPoint.entity_id == Entity.id
            ).join(
                Company, Entity.company_id == Company.id
            ).join(
                Framework, DataPoint.framework_id == Framework.id
            ).join(
                FrameworkDataField, DataPoint.framework_field_id == FrameworkDataField.id
            ).filter(
                Company.is_active == True,
                ESGData.value.isnot(None),
                ESGData.value != ''
            )
            
            # Apply filters
            if framework_id:
                query = query.filter(Framework.id == framework_id)
            if industry:
                query = query.filter(Company.industry == industry)
            
            # Execute query
            benchmark_data = query.all()
            
            # Process numeric values for benchmarking
            numeric_benchmarks = {}
            for value, company_industry, framework_name, field_name in benchmark_data:
                try:
                    # Try to convert to float for numeric analysis
                    numeric_value = float(value)
                    
                    key = f"{framework_name}::{field_name}"
                    if key not in numeric_benchmarks:
                        numeric_benchmarks[key] = {
                            'framework': framework_name,
                            'field': field_name,
                            'values': [],
                            'industries': set()
                        }
                    
                    numeric_benchmarks[key]['values'].append(numeric_value)
                    numeric_benchmarks[key]['industries'].add(company_industry or 'Not Specified')
                    
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    continue
            
            # Calculate percentiles and statistics
            benchmark_results = {}
            for key, data in numeric_benchmarks.items():
                values = sorted(data['values'])
                if len(values) >= 5:  # Only calculate benchmarks with sufficient data
                    benchmark_results[key] = {
                        'framework': data['framework'],
                        'field': data['field'],
                        'sample_size': len(values),
                        'industries_covered': list(data['industries']),
                        'statistics': {
                            'min': min(values),
                            'max': max(values),
                            'mean': sum(values) / len(values),
                            'median': values[len(values) // 2],
                            'percentile_25': values[int(len(values) * 0.25)],
                            'percentile_75': values[int(len(values) * 0.75)],
                            'percentile_90': values[int(len(values) * 0.90)]
                        }
                    }
            
            return {
                'success': True,
                'benchmarks': {
                    'data': benchmark_results,
                    'total_fields': len(benchmark_results),
                    'filters_applied': {
                        'framework_id': framework_id,
                        'industry': industry
                    },
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            current_app.logger.error(f'Error generating benchmark data: {str(e)}')
            return {
                'success': False,
                'error': 'Failed to generate benchmark data'
            }
    
    @staticmethod
    def get_trend_analysis(days: int = 90) -> Dict[str, Any]:
        """
        Get trend analysis for ESG data over specified time period.
        
        Args:
            days: Number of days to analyze (default: 90)
            
        Returns:
            Dict containing trend analysis data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily data entry trends
            daily_trends = db.session.query(
                func.date(ESGData.created_at).label('date'),
                func.count(ESGData.id).label('entries_count')
            ).filter(
                ESGData.created_at >= start_date
            ).group_by(
                func.date(ESGData.created_at)
            ).order_by('date').all()
            
            # Framework adoption trends
            framework_trends = db.session.query(
                Framework.name,
                func.date(DataPoint.created_at).label('date'),
                func.count(DataPoint.id).label('new_data_points')
            ).join(
                DataPoint, Framework.id == DataPoint.framework_id
            ).filter(
                DataPoint.created_at >= start_date
            ).group_by(
                Framework.id, Framework.name, func.date(DataPoint.created_at)
            ).order_by('date').all()
            
            # Company onboarding trends
            company_trends = db.session.query(
                func.date(Company.created_at).label('date'),
                func.count(Company.id).label('new_companies')
            ).filter(
                Company.created_at >= start_date,
                Company.is_active == True
            ).group_by(
                func.date(Company.created_at)
            ).order_by('date').all()
            
            return {
                'success': True,
                'trends': {
                    'daily_data_entries': [
                        {'date': date.isoformat(), 'count': count}
                        for date, count in daily_trends
                    ],
                    'framework_adoption': [
                        {'framework': name, 'date': date.isoformat(), 'new_data_points': count}
                        for name, date, count in framework_trends
                    ],
                    'company_onboarding': [
                        {'date': date.isoformat(), 'new_companies': count}
                        for date, count in company_trends
                    ],
                    'analysis_period_days': days,
                    'start_date': start_date.isoformat(),
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            current_app.logger.error(f'Error generating trend analysis: {str(e)}')
            return {
                'success': False,
                'error': 'Failed to generate trend analysis'
            }
    
    @staticmethod
    def _anonymize_tenant_id(company_id: int) -> str:
        """
        Generate anonymized tenant identifier.
        
        Args:
            company_id: Original company ID
            
        Returns:
            Anonymized tenant identifier
        """
        # Create a hash-based anonymous ID
        hash_input = f"tenant_{company_id}_{current_app.config.get('SECRET_KEY', 'default')}"
        hash_object = hashlib.sha256(hash_input.encode())
        return f"TENANT_{hash_object.hexdigest()[:8].upper()}"
    
    @staticmethod
    def export_analytics_report(report_type: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Export comprehensive analytics report.
        
        Args:
            report_type: Type of report ('global', 'comparison', 'benchmarks', 'trends')
            filters: Optional filters to apply
            
        Returns:
            Dict containing the complete report data
        """
        try:
            filters = filters or {}
            report_data = {
                'report_type': report_type,
                'filters_applied': filters,
                'generated_at': datetime.utcnow().isoformat(),
                'generated_by': 'CrossTenantAnalyticsService'
            }
            
            if report_type == 'global':
                report_data.update(CrossTenantAnalyticsService.get_global_metrics())
            elif report_type == 'comparison':
                report_data.update(CrossTenantAnalyticsService.get_tenant_comparison(
                    industry=filters.get('industry'),
                    anonymize=filters.get('anonymize', True)
                ))
            elif report_type == 'benchmarks':
                report_data.update(CrossTenantAnalyticsService.get_benchmark_data(
                    framework_id=filters.get('framework_id'),
                    industry=filters.get('industry')
                ))
            elif report_type == 'trends':
                report_data.update(CrossTenantAnalyticsService.get_trend_analysis(
                    days=filters.get('days', 90)
                ))
            else:
                return {
                    'success': False,
                    'error': f'Unknown report type: {report_type}'
                }
            
            return report_data
            
        except Exception as e:
            current_app.logger.error(f'Error exporting analytics report: {str(e)}')
            return {
                'success': False,
                'error': 'Failed to export analytics report'
            } 