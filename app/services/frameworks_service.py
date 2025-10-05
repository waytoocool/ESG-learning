from ..extensions import db
from ..models import Framework, FrameworkDataField, DataPointAssignment, Topic, Company, ESGData, FieldDimension, FieldVariableMapping
from sqlalchemy import func
from datetime import datetime, timedelta
import uuid

def get_global_provider_company_id():
    """
    Get the company ID that provides global frameworks.
    
    Returns:
        int: The company ID of the global provider, or None if not set
    """
    return Company.get_global_provider_id()

def is_global_framework(framework_id, company_id=None):
    """
    Check if a framework belongs to the global provider company.
    
    Args:
        framework_id (str): The framework ID to check
        company_id (int, optional): Company ID for context (not used in logic but kept for API consistency)
        
    Returns:
        bool: True if the framework is global, False otherwise
    """
    global_provider_id = get_global_provider_company_id()
    if not global_provider_id:
        return False
    
    framework = Framework.query.filter_by(framework_id=framework_id).first()
    if not framework:
        return False
    
    return framework.company_id == global_provider_id

def separate_frameworks_by_type(company_id):
    """
    Separate frameworks into global and company-specific categories for a given company.
    
    Args:
        company_id (int): The company ID to get frameworks for
        
    Returns:
        dict: Dictionary with 'global' and 'company' framework lists
    """
    global_provider_id = get_global_provider_company_id()
    
    # Get company-specific frameworks
    company_frameworks = Framework.query.filter_by(company_id=company_id).all()
    
    # Get global frameworks (if global provider exists and is different from current company)
    global_frameworks = []
    if global_provider_id and global_provider_id != company_id:
        global_frameworks = Framework.query.filter_by(company_id=global_provider_id).all()
    
    return {
        'global': global_frameworks,
        'company': company_frameworks
    }

def create_initial_framework(company_id, name, description):
    """
    Creates an initial framework entry in the database with just the name and description.
    
    Args:
        company_id (int): The ID of the company creating the framework.
        name (str): The name of the framework.
        description (str): The description of the framework.
        
    Returns:
        str: The framework_id of the newly created framework.
    """
    try:
        framework_id = str(uuid.uuid4())
        new_framework = Framework(
            framework_id=framework_id,
            company_id=company_id,
            framework_name=name,
            description=description
        )
        db.session.add(new_framework)
        db.session.commit()
        return framework_id
    except Exception as e:
        db.session.rollback()
        raise e

def get_framework_type_info(framework_id, company_id):
    """
    Get type information for a framework (global vs company-specific).
    
    Args:
        framework_id (str): The framework ID
        company_id (int): The requesting company ID
        
    Returns:
        dict: Framework type information including is_global and is_editable flags
    """
    global_provider_id = get_global_provider_company_id()
    framework = Framework.query.filter_by(framework_id=framework_id).first()
    
    if not framework:
        return {
            'is_global': False,
            'is_editable': False,
            'framework_exists': False
        }
    
    is_global = framework.company_id == global_provider_id
    is_editable = framework.company_id == company_id  # Only editable if owned by current company
    
    return {
        'is_global': is_global,
        'is_editable': is_editable,
        'framework_exists': True,
        'owner_company_id': framework.company_id
    }

def add_topics_to_framework(framework_id, company_id, topics_data):
    """
    Adds a list of topics to an existing framework.
    
    Args:
        framework_id (str): The ID of the framework to add topics to.
        company_id (int): The ID of the company owning the framework.
        topics_data (list): A list of dictionaries, each representing a topic.
    """
    try:
        framework = Framework.query.filter_by(framework_id=framework_id, company_id=company_id).first()
        if not framework:
            raise ValueError(f"Framework with ID {framework_id} not found for company {company_id}")

        for topic_data in topics_data:
            new_topic = Topic(
                framework_id=framework_id,
                company_id=company_id,
                name=topic_data.get('name'),
                description=topic_data.get('description'),
                parent_id=topic_data.get('parent_id')
            )
            db.session.add(new_topic)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def add_data_points_to_framework(framework_id, company_id, data_points_data):
    """
    Adds a list of data points (fields) to an existing framework.
    
    Args:
        framework_id (str): The ID of the framework to add data points to.
        company_id (int): The ID of the company owning the framework.
        data_points_data (list): A list of dictionaries, each representing a data point.
    """
    try:
        framework = Framework.query.filter_by(framework_id=framework_id, company_id=company_id).first()
        if not framework:
            raise ValueError(f"Framework with ID {framework_id} not found for company {company_id}")

        for dp in data_points_data:
            let_vt = (dp.get('value_type') or 'NUMBER').upper()
            if let_vt == 'NUMERIC':
                let_vt = 'NUMBER'
            elif let_vt == 'TEXTUAL':
                let_vt = 'TEXT'

            field = FrameworkDataField(
                framework_id=framework_id,
                company_id=company_id,
                field_name=dp.get('name'),
                field_code=dp.get('field_code'),
                description=dp.get('description'),
                value_type=let_vt,
                unit_category=dp.get('unit_category'),
                default_unit=dp.get('default_unit'),
                topic_id=dp.get('topic_id'),
                is_computed=dp.get('is_computed', False),
                formula_expression=dp.get('formula_expression')
            )
            db.session.add(field)
            db.session.flush()  # Ensure field.field_id is available

            # --- Handle dimensions ---
            dims = dp.get('dimensions', [])
            for dim_data in dims:
                dim_id = dim_data.get('dimension_id')
                if not dim_id:
                    continue
                fd_rel = FieldDimension(
                    field_id=field.field_id,
                    dimension_id=dim_id,
                    company_id=company_id,
                    is_required=dim_data.get('is_required', True)
                )
                db.session.add(fd_rel)

            # --- Handle variable mappings for computed fields ---
            if field.is_computed:
                mappings = dp.get('variable_mappings', [])
                for mp in mappings:
                    raw_field_id = mp.get('raw_field_id')
                    var_name = mp.get('variable_name')
                    if not raw_field_id or not var_name:
                        continue
                    fv_map = FieldVariableMapping(
                        computed_field_id=field.field_id,
                        raw_field_id=raw_field_id,
                        variable_name=var_name,
                        coefficient=mp.get('coefficient', 1.0),
                        dimension_filter=mp.get('dimension_filter'),
                        aggregation_type=mp.get('aggregation_type', 'SUM_ALL_DIMENSIONS')
                    )
                    db.session.add(fv_map)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def get_framework_kpis(company_id):
    """
    Retrieves key performance indicators for frameworks.
    """
    total_frameworks = Framework.query.filter_by(company_id=company_id).count()

    active_assignments = DataPointAssignment.query.filter_by(
        company_id=company_id,
        series_status='active'
    ).count()

    # Calculate overall coverage
    frameworks = Framework.query.filter_by(company_id=company_id).all()
    total_coverage_sum = 0
    framework_count_for_coverage = 0

    for framework in frameworks:
        total_fields = FrameworkDataField.query.filter_by(
            framework_id=framework.framework_id,
            company_id=company_id
        ).count()
        
        fields_with_data = 0
        if total_fields > 0:
                fields_with_data = db.session.query(FrameworkDataField)\
                .join(DataPointAssignment, FrameworkDataField.field_id == DataPointAssignment.field_id)\
                .filter(\
                    FrameworkDataField.framework_id == framework.framework_id,\
                    FrameworkDataField.company_id == company_id,\
                    DataPointAssignment.company_id == company_id,\
                    DataPointAssignment.series_status == 'active'\
                ).distinct().count()
            
        coverage_percentage = (fields_with_data / total_fields * 100) if total_fields > 0 else 0
        total_coverage_sum += coverage_percentage
        framework_count_for_coverage += 1
    
    overall_coverage = (total_coverage_sum / framework_count_for_coverage) if framework_count_for_coverage > 0 else 0

    # Get recent activity (latest framework creation or assignment)
    latest_framework = Framework.query.filter_by(company_id=company_id).order_by(Framework.created_at.desc()).first()
    latest_assignment = DataPointAssignment.query.filter_by(company_id=company_id).order_by(DataPointAssignment.assigned_date.desc()).first()

    recent_activity_timestamp = None
    if latest_framework and latest_assignment:
        recent_activity_timestamp = max(latest_framework.created_at, latest_assignment.assigned_date)
    elif latest_framework:
        recent_activity_timestamp = latest_framework.created_at
    elif latest_assignment:
        recent_activity_timestamp = latest_assignment.assigned_date

    return {
        'total_frameworks': total_frameworks,
        'active_assignments': active_assignments,
        'overall_coverage': round(overall_coverage, 1),
        'recent_activity': recent_activity_timestamp.isoformat() if recent_activity_timestamp else None
    }

def get_chart_data(company_id):
    """
    Retrieves data for framework charts (top 5 coverage, global vs company-specific).
    """
    # Get frameworks separated by type
    frameworks_by_type = separate_frameworks_by_type(company_id)
    all_frameworks = frameworks_by_type['global'] + frameworks_by_type['company']

    framework_coverages = []
    for framework in all_frameworks:
        # Use the framework's actual company_id for coverage calculation
        framework_company_id = framework.company_id
        
        total_fields = FrameworkDataField.query.filter_by(
            framework_id=framework.framework_id,
            company_id=framework_company_id
        ).count()
        
        fields_with_data = 0
        if total_fields > 0:
            # For global frameworks, check if current company has assignments
            if framework.company_id != company_id:
                # This is a global framework, check current company's assignments
                fields_with_data = db.session.query(FrameworkDataField)\
                    .join(DataPointAssignment, FrameworkDataField.field_id == DataPointAssignment.field_id)\
                    .filter(\
                        FrameworkDataField.framework_id == framework.framework_id,\
                        FrameworkDataField.company_id == framework_company_id,\
                        DataPointAssignment.company_id == company_id,\
                        DataPointAssignment.series_status == 'active'\
                    ).distinct().count()
            else:
                # This is a company framework, use normal calculation
                fields_with_data = db.session.query(FrameworkDataField)\
                .join(DataPointAssignment, FrameworkDataField.field_id == DataPointAssignment.field_id)\
                .filter(\
                    FrameworkDataField.framework_id == framework.framework_id,\
                        FrameworkDataField.company_id == framework_company_id,\
                    DataPointAssignment.company_id == company_id,\
                    DataPointAssignment.series_status == 'active'\
                ).distinct().count()
        
        coverage_percentage = (fields_with_data / total_fields * 100) if total_fields > 0 else 0
        framework_coverages.append({
            'name': framework.framework_name,
            'coverage': round(coverage_percentage, 1)
        })
    
    top_5_frameworks = sorted(framework_coverages, key=lambda x: x['coverage'], reverse=True)[:5]

    # Global vs Company framework distribution
    global_framework_count = len(frameworks_by_type['global'])
    company_framework_count = len(frameworks_by_type['company'])

    return {
        'top_5_frameworks': top_5_frameworks,
        'framework_type_distribution': {
            'global': global_framework_count,
            'company': company_framework_count
        }
    }

def list_frameworks(company_id, search=None, sort=None, include_global=True):
    """
    Returns a list of frameworks with lightweight data for cards/table.
    Includes pre-computed coverage percentage and framework type information.
    
    Args:
        company_id (int): The company ID requesting frameworks
        search (str, optional): Search term to filter frameworks
        sort (str, optional): Sort order for frameworks
        include_global (bool): Whether to include global frameworks (default: True)
    """
    # Get frameworks separated by type
    frameworks_by_type = separate_frameworks_by_type(company_id)
    
    # Combine frameworks based on include_global flag
    all_frameworks = frameworks_by_type['company']
    if include_global:
        all_frameworks.extend(frameworks_by_type['global'])
    
    # Apply search filter if provided
    if search:
        search_pattern = f"%{search.lower()}%"
        filtered_frameworks = []
        for framework in all_frameworks:
            if (search_pattern.replace('%', '').lower() in framework.framework_name.lower() or
                (framework.description and search_pattern.replace('%', '').lower() in framework.description.lower())):
                filtered_frameworks.append(framework)
        all_frameworks = filtered_frameworks
    
    framework_data = []
    for framework in all_frameworks:
        # Get framework type information
        type_info = get_framework_type_info(framework.framework_id, company_id)
        
        # Calculate coverage (using appropriate company_id for data lookup)
        coverage_data = get_framework_coverage(framework.framework_id, company_id)
        
        framework_data.append({
            'framework_id': framework.framework_id,
            'framework_name': framework.framework_name,
            'description': framework.description,
            'coverage_percentage': coverage_data['coverage_percentage'],
            'total_fields': coverage_data['total_fields'],
            'last_updated': coverage_data['last_updated'],
            'is_global': type_info['is_global'],
            'is_editable': type_info['is_editable'],
            'owner_company_id': type_info['owner_company_id']
        })

    # Apply sorting
    if sort:
        if sort == 'name_asc':
            framework_data.sort(key=lambda x: x['framework_name'].lower())
        elif sort == 'name_desc':
            framework_data.sort(key=lambda x: x['framework_name'].lower(), reverse=True)
        elif sort == 'coverage_asc':
            framework_data.sort(key=lambda x: x['coverage_percentage'])
        elif sort == 'coverage_desc':
            framework_data.sort(key=lambda x: x['coverage_percentage'], reverse=True)
        elif sort == 'type_asc':
            framework_data.sort(key=lambda x: (x['is_global'], x['framework_name'].lower()))
        elif sort == 'type_desc':
            framework_data.sort(key=lambda x: (not x['is_global'], x['framework_name'].lower()))

    return framework_data

def get_framework_coverage(framework_id, company_id):
    """
    Get coverage statistics for a single framework.
    For global frameworks, checks assignments against the requesting company
    while using the framework's actual company for field definitions.
    """
    # Import here to avoid circular imports
    from ..models.company import Company
    
    framework = Framework.query.filter_by(framework_id=framework_id).first()
    
    if not framework:
        return None  # Return None to indicate framework not found
    
    # Check access permissions - allow if framework belongs to current company or global provider
    global_provider_id = Company.get_global_provider_id()
    if framework.company_id not in (company_id, global_provider_id):
        return None  # Return None to indicate access denied
    
    # Use the framework's actual company_id for field lookups
    framework_company_id = framework.company_id
    
    total_fields = FrameworkDataField.query.filter_by(
        framework_id=framework_id,
        company_id=framework_company_id
    ).count()
    
    fields_with_data = 0
    if total_fields > 0:
        # For coverage calculation, always check assignments against the requesting company
        fields_with_data = db.session.query(FrameworkDataField)\
            .join(DataPointAssignment, FrameworkDataField.field_id == DataPointAssignment.field_id)\
            .filter(
                FrameworkDataField.framework_id == framework_id,
                FrameworkDataField.company_id == framework_company_id,
                DataPointAssignment.company_id == company_id,  # Always use requesting company for assignments
                DataPointAssignment.series_status == 'active'
            ).distinct().count()
    
    coverage_percentage = (fields_with_data / total_fields * 100) if total_fields > 0 else 0
    
    # Get last assignment for this framework by the requesting company
    last_assignment = DataPointAssignment.query\
        .join(FrameworkDataField)\
        .filter(\
            FrameworkDataField.framework_id == framework_id,\
            FrameworkDataField.company_id == framework_company_id,\
            DataPointAssignment.company_id == company_id\
        )\
        .order_by(DataPointAssignment.assigned_date.desc())\
        .first()
    
    last_updated = last_assignment.assigned_date.isoformat() if last_assignment else None
    
    return {
        'coverage_percentage': round(coverage_percentage, 1),
        'fields_with_data': fields_with_data,
        'total_fields': total_fields,
        'last_updated': last_updated
    }

def get_recent_activity(company_id):
    """
    Get recent activity related to frameworks and data points for a given company.
    """
    activities = []

    # Fetch recent framework creations
    recent_frameworks = Framework.query.filter_by(company_id=company_id)\
                            .order_by(Framework.created_at.desc()).limit(5).all()
    for fw in recent_frameworks:
        activities.append({
            'type': 'Framework Created',
            'name': fw.framework_name,
            'date': fw.created_at.isoformat()
        })

    # Fetch recent data point assignments
    recent_assignments = DataPointAssignment.query.filter_by(company_id=company_id)\
                            .order_by(DataPointAssignment.assigned_date.desc()).limit(5).all()
    for assign in recent_assignments:
        field_name = assign.field.field_name if assign.field else 'Unknown Field'
        entity_name = assign.entity.name if assign.entity else 'Unknown Entity'
        activities.append({
            'type': 'Data Point Assigned',
            'name': f'{field_name} to {entity_name}',
            'date': assign.assigned_date.isoformat()
        })

    # Sort activities by date in descending order
    activities.sort(key=lambda x: x['date'], reverse=True)

    return activities[:10] # Limit to top 10 recent activities

def get_single_framework_details(framework_id, company_id):
    """
    Retrieves detailed information for a single framework, including its data fields and type information.
    """
    # Import here to avoid circular imports
    from ..models.company import Company
    
    framework = Framework.query.filter_by(framework_id=framework_id).first()

    if not framework:
        return None
    
    # Check access permissions - allow if framework belongs to current company or global provider
    global_provider_id = Company.get_global_provider_id()
    if framework.company_id not in (company_id, global_provider_id):
        return None  # Return None to indicate access denied

    # Get framework type information
    type_info = get_framework_type_info(framework_id, company_id)

    # Get all data fields for this framework (use framework's actual company_id)
    framework_company_id = framework.company_id
    data_fields = FrameworkDataField.query.filter_by(
        framework_id=framework_id,
        company_id=framework_company_id
    ).all()

    # Prepare data fields for response
    fields_data = []
    for field in data_fields:
        fields_data.append({
            'field_id': field.field_id,
            'field_name': field.field_name,
            'field_code': field.field_code,
            'description': field.description,
            'unit_category': field.unit_category,
            'default_unit': field.default_unit,
            'value_type': field.value_type,
            'is_computed': field.is_computed,
            'formula_expression': field.formula_expression,
            'topic_id': field.topic_id,
            'topic_name': field.topic.name if field.topic else None,
        })

    return {
        'framework_id': framework.framework_id,
        'framework_name': framework.framework_name,
        'description': framework.description,
        'created_at': framework.created_at.isoformat(),
        'updated_at': framework.updated_at.isoformat(),
        'total_fields': len(data_fields),
        'computed_fields': sum(1 for f in data_fields if f.is_computed),
        'data_points': fields_data,
        'is_global': type_info['is_global'],
        'is_editable': type_info['is_editable'],
        'owner_company_id': type_info['owner_company_id']
    }

def get_framework_details_with_data_status(framework_id, company_id):
    """
    Get detailed framework information including field data status for the details modal.
    For global frameworks, checks assignments against the requesting company
    while using the framework's actual company for field definitions.
    """
    # Import here to avoid circular imports
    from ..models.company import Company
    from ..models import Topic
    from sqlalchemy import func
    
    framework = Framework.query.filter_by(framework_id=framework_id).first()

    if not framework:
        return None
    
    # Check access permissions - allow if framework belongs to current company or global provider
    global_provider_id = Company.get_global_provider_id()
    if framework.company_id not in (company_id, global_provider_id):
        return None  # Return None to indicate access denied

    owner_company_id = framework.company_id

    # Get all fields with their data status
    fields_query = db.session.query(
        FrameworkDataField,
        Topic.name.label('topic_name'),
        func.count(DataPointAssignment.id).label('data_count'),
        func.max(DataPointAssignment.assigned_date).label('last_update')
    )\
    .outerjoin(Topic, FrameworkDataField.topic_id == Topic.topic_id)\
    .outerjoin(DataPointAssignment, 
               (FrameworkDataField.field_id == DataPointAssignment.field_id) &
               (DataPointAssignment.company_id == company_id))\
    .filter(
        FrameworkDataField.framework_id == framework_id,
        FrameworkDataField.company_id == owner_company_id
    )\
    .group_by(FrameworkDataField.field_id, Topic.name)\
    .all()
    
    # Get latest values for each field
    latest_values = {}
    for field_data in fields_query:
        field = field_data[0]
        if field_data.data_count > 0:
            latest_assignment = DataPointAssignment.query\
                .filter_by(
                    field_id=field.field_id,
                    company_id=company_id
                )\
                .order_by(DataPointAssignment.assigned_date.desc())\
                .first()
            
            if latest_assignment:
                latest_values[field.field_id] = None  # Placeholder until ESGData join implemented
    
    # Format field data
    data_points = []
    computed_fields_count = 0
    
    for field_data in fields_query:
        field = field_data[0]
        topic_name = field_data[1]
        data_count = field_data.data_count
        
        if field.is_computed:
            computed_fields_count += 1
        
        data_points.append({
            'field_id': field.field_id,
            'field_name': field.field_name,
            'field_code': field.field_code,
            'value_type': field.value_type,
            'default_unit': field.default_unit,
            'topic_name': topic_name,
            'has_data': data_count > 0,
            'data_count': data_count,
            'last_value': latest_values.get(field.field_id),
            'is_computed': field.is_computed
        })
    
    return {
        'success': True,
        'framework_id': framework.framework_id,
        'framework_name': framework.framework_name,
        'description': framework.description,
        'total_fields': len(data_points),
        'computed_fields': computed_fields_count,
        'data_points': data_points
    }

def get_framework_for_editing(framework_id, company_id):
    """
    Get framework data for editing. Only allows editing of company-owned frameworks.
    
    Args:
        framework_id (str): The framework ID to edit
        company_id (int): The requesting company ID
        
    Returns:
        dict: Framework data with fields and topics, or None if not accessible
    """
    # Check if framework exists and is editable by this company
    framework = Framework.query.filter_by(
        framework_id=framework_id,
        company_id=company_id  # Only allow editing own frameworks
    ).first()
    
    if not framework:
        return None
    
    # Get framework fields
    fields = get_data_points_for_framework(framework_id, company_id)
    
    # Get framework topics
    topics = get_topics_for_framework(framework_id, company_id)
    
    # Convert to dictionary format expected by wizard
    framework_data = {
        'framework_id': framework.framework_id,
        'framework_name': framework.framework_name,
        'description': framework.description,
        'created_at': framework.created_at.isoformat() if framework.created_at else None,
        'fields': fields,
        'topics': topics
    }
    
    return framework_data

def get_topics_for_framework(framework_id, company_id):
    """
    Retrieves all topics associated with a given framework.
    """
    topics = Topic.query.filter_by(
        framework_id=framework_id,
        company_id=company_id
    ).all()
    
    return [{
        'topic_id': topic.topic_id,
        'name': topic.name,
        'description': topic.description,
        'parent_id': topic.parent_id,
        'level': topic.level
    } for topic in topics]

def get_data_points_for_framework(framework_id, company_id):
    """
    Retrieves all data points (fields) associated with a given framework.
    Enhanced to include dimensions and variable mappings for complete edit support.
    """
    data_fields = FrameworkDataField.query.filter_by(
        framework_id=framework_id,
        company_id=company_id
    ).all()

    result = []
    for field in data_fields:
        # Get dimensions for this field
        dimensions = []
        for fd in field.field_dimensions:
            dimensions.append({
                'dimension_id': fd.dimension_id,
                'name': fd.dimension.name,
                'description': fd.dimension.description,
                'is_required': fd.is_required
            })
        
        # Get variable mappings for computed fields (eager-load raw_field)
        variable_mappings = []
        if field.is_computed:
            from sqlalchemy.orm import joinedload
            from ..models.framework import FieldVariableMapping

            mappings = (
                FieldVariableMapping.query.options(joinedload(FieldVariableMapping.raw_field))
                .filter_by(computed_field_id=field.field_id)
                .all()
            )

            for mapping in mappings:
                raw_f = mapping.raw_field  # eager-loaded object
                variable_mappings.append({
                    'mapping_id': mapping.mapping_id,
                    'variable_name': mapping.variable_name,
                    'raw_field_id': mapping.raw_field_id,
                    'framework_id': raw_f.framework_id if raw_f else None,
                    'coefficient': mapping.coefficient,
                    'dimension_filter': mapping.dimension_filter,
                    'aggregation_type': mapping.aggregation_type,
                    'raw_field_name': raw_f.field_name if raw_f else None,
                    'raw_field_code': raw_f.field_code if raw_f else None
                })

        field_data = {
            'field_id': field.field_id,
            'field_name': field.field_name,
            'field_code': field.field_code,
            'description': field.description,
            'unit_category': field.unit_category,
            'default_unit': field.default_unit,
            'value_type': field.value_type,
            'is_computed': field.is_computed,
            'formula_expression': field.formula_expression,
            'topic_id': field.topic_id,
            'topic_name': field.topic.name if field.topic else None,
            'dimensions': dimensions,
            'variable_mappings': variable_mappings
        }
        result.append(field_data)
    
    return result

def update_framework(framework_id, company_id, name, description):
    """
    Update an existing framework's basic information (name, description).
    Only allows updating company-owned frameworks.
    
    Args:
        framework_id (str): The framework ID to update
        company_id (int): The requesting company ID
        name (str): Updated framework name
        description (str): Updated framework description
        
    Returns:
        Framework: Updated framework object, or None if not accessible
    """
    from ..models import Framework
    from ..extensions import db
    
    # Check if framework exists and is editable by this company
    framework = Framework.query.filter_by(
        framework_id=framework_id,
        company_id=company_id  # Only allow updating own frameworks
    ).first()
    
    if not framework:
        return None
    
    try:
        # Update framework basic info
        framework.framework_name = name
        framework.description = description
        
        db.session.commit()
        return framework
        
    except Exception as e:
        db.session.rollback()
        raise e

def update_data_point(framework_id, field_id, company_id, data_point_data):
    """Update a single data point and its related dimensions/mappings."""
    from ..models import FrameworkDataField, FieldDimension, FieldVariableMapping
    from ..models.dimension import Dimension
    from ..extensions import db

    field = FrameworkDataField.query.filter_by(field_id=field_id, framework_id=framework_id, company_id=company_id).first()
    if not field:
        return None

    try:
        # Core attributes
        field.field_name = data_point_data.get('name', field.field_name)
        field.field_code = data_point_data.get('field_code', field.field_code)
        field.description = data_point_data.get('description', field.description)
        if data_point_data.get('value_type'):
            vt = data_point_data['value_type'].upper()
            if vt == 'NUMERIC':
                vt = 'NUMBER'
            field.value_type = vt
        field.unit_category = data_point_data.get('unit_category', field.unit_category)
        field.default_unit = data_point_data.get('default_unit', field.default_unit)
        field.topic_id = data_point_data.get('topic_id', field.topic_id)
        field.is_computed = data_point_data.get('is_computed', field.is_computed)
        field.formula_expression = data_point_data.get('formula_expression', field.formula_expression)

        # Replace dimensions
        FieldDimension.query.filter_by(field_id=field_id).delete()
        for dim in data_point_data.get('dimensions', []):
            dim_id = dim.get('dimension_id')
            if not dim_id:
                continue
            fd_rel = FieldDimension(field_id=field_id, dimension_id=dim_id, company_id=company_id, is_required=dim.get('is_required', True))
            db.session.add(fd_rel)

        # Replace variable mappings for computed fields
        if field.is_computed:
            FieldVariableMapping.query.filter_by(computed_field_id=field_id).delete()
            for mp in data_point_data.get('variable_mappings', []):
                raw_field_id = mp.get('raw_field_id')
                var_name = mp.get('variable_name')
                if not raw_field_id or not var_name:
                    continue
                fv_map = FieldVariableMapping(
                    computed_field_id=field_id,
                    raw_field_id=raw_field_id,
                    variable_name=var_name,
                    coefficient=mp.get('coefficient', 1.0),
                    dimension_filter=mp.get('dimension_filter'),
                    aggregation_type=mp.get('aggregation_type', 'SUM_ALL_DIMENSIONS')
                )
                db.session.add(fv_map)

        db.session.commit()
        return field
    except Exception as e:
        db.session.rollback()
        raise e

def delete_topic_from_framework(framework_id, topic_id, company_id):
    """Delete a topic belonging to a framework.

    The previous logic strictly matched on ``company_id`` which prevented deletion of
    framework-scoped topics (``company_id`` is NULL) because the filter could never
    match the requesting company.  We now:

    1. Fetch by ``topic_id`` and ``framework_id`` only.
    2. Verify ownership:
       • If the topic has ``company_id`` (custom/company-wide topic) it **must** match
         the caller’s company.
       • If the topic has ``company_id`` == NULL it belongs to the framework; we allow
         deletion as long as the framework itself belongs to the caller’s company.
    """
    try:
        topic = Topic.query.filter_by(topic_id=topic_id, framework_id=framework_id).first()
        if not topic:
            raise ValueError(
                f"Topic with ID {topic_id} not found for framework {framework_id}")

        # Ownership / access check
        if topic.company_id is not None and topic.company_id != company_id:
            raise ValueError("Access denied for deleting this topic")

        db.session.delete(topic)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def delete_data_point_from_framework(framework_id, field_id, company_id):
    """
    Deletes a data point (FrameworkDataField) from a specific framework.
    """
    try:
        field = FrameworkDataField.query.filter_by(field_id=field_id, framework_id=framework_id, company_id=company_id).first()
        if not field:
            raise ValueError(f"Data point with ID {field_id} not found for framework {framework_id} and company {company_id}")
        db.session.delete(field)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def delete_framework(framework_id, company_id):
    """Completely delete a framework and all related data (topics, fields, ESG data, assignments).
    Args:
        framework_id (str): Framework to delete
        company_id (int): Company ownership check (super-admin may pass None to skip)
    Returns:
        bool: True if deleted, False if not found / not allowed
    """
    try:
        # Fetch framework with ownership check (unless company_id is None, meaning super-admin)
        query = Framework.query.filter_by(framework_id=framework_id)
        if company_id is not None:
            query = query.filter_by(company_id=company_id)
        framework = query.first()
        if not framework:
            return False

        # Use raw SQL to avoid Enum parsing issues on malformed data
        # 1. Get field_ids via raw select
        field_id_rows = db.session.execute(
            db.text("""SELECT field_id FROM framework_data_fields WHERE framework_id = :fid"""),
            {"fid": framework_id}
        ).fetchall()
        field_ids = [row[0] for row in field_id_rows]

        if field_ids:
            placeholders = ",".join([":id%d" % i for i,_ in enumerate(field_ids)])
            id_params = {f"id{i}": fid for i, fid in enumerate(field_ids)}

            # Delete assignments
            db.session.execute(db.text(f"DELETE FROM data_point_assignments WHERE field_id IN ({placeholders})"), id_params)
            # Delete ESG data
            db.session.execute(db.text(f"DELETE FROM esg_data WHERE field_id IN ({placeholders})"), id_params)
            # Delete variable mappings
            db.session.execute(db.text(f"DELETE FROM field_variable_mappings WHERE computed_field_id IN ({placeholders}) OR raw_field_id IN ({placeholders})"), id_params)

        # Delete fields, topics, and framework - order matters
        db.session.execute(db.text("DELETE FROM framework_data_fields WHERE framework_id = :fid"), {"fid": framework_id})
        db.session.execute(db.text("DELETE FROM topics WHERE framework_id = :fid"), {"fid": framework_id})
        db.session.execute(db.text("DELETE FROM frameworks WHERE framework_id = :fid"), {"fid": framework_id})
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e

def promote_framework_to_global(framework_id: str, initiated_by_user_id: int):
    """Promote a company-specific framework to the global provider.

    The promotion is implemented as a *move* – the framework and all its
    fields are re-assigned to the global provider company.  This keeps IDs
    intact and avoids complex cross-tenant copying until a more sophisticated
    merge/copy process is required.

    Args:
        framework_id: ID of the framework to promote.
        initiated_by_user_id: The super-admin user performing the action (for
            audit logging).

    Raises:
        ValueError: If no global provider is set, the framework is already
            global, the framework does not exist, or a name clash would occur
            in the global provider tenant.
    """
    from ..models.audit_log import AuditLog  # Local import to avoid circular deps

    # 1. Ensure a global provider exists
    global_provider_id = get_global_provider_company_id()
    if not global_provider_id:
        raise ValueError("No company is designated as the global framework provider.")

    # 2. Fetch the framework
    framework = Framework.query.filter_by(framework_id=framework_id).first()
    if not framework:
        raise ValueError("Framework not found.")

    # 3. If already global, nothing to do
    if framework.company_id == global_provider_id:
        raise ValueError("Framework is already a global framework.")

    # 4. Prevent duplicate names in the global provider scope
    duplicate = Framework.query.filter_by(
        company_id=global_provider_id,
        framework_name=framework.framework_name
    ).first()
    if duplicate:
        raise ValueError("A global framework with the same name already exists. Rename the framework before promotion or delete the existing one.")

    original_company_id = framework.company_id

    # 5. Re-assign ownership of the framework and its related data
    framework.company_id = global_provider_id

    # Update all data fields to belong to the global provider
    FrameworkDataField.query.filter_by(framework_id=framework.framework_id).update({
        'company_id': global_provider_id
    })

    # NOTE: Other dependent records (DataPointAssignment, ESGData, etc.) retain
    # their original company_id because they represent *usage* of the fields
    # within tenant companies.  Only the field definitions move to the global
    # provider.

    # 6. Commit & audit log
    db.session.flush()

    AuditLog.log_action(
        user_id=initiated_by_user_id,
        action='PROMOTE_FRAMEWORK_TO_GLOBAL',
        entity_type='Framework',
        entity_id=framework.framework_id,
        payload={
            'from_company_id': original_company_id,
            'to_company_id': global_provider_id
        }
    )

    db.session.commit()

    return {
        'success': True,
        'framework_id': framework.framework_id,
        'from_company_id': original_company_id,
        'to_company_id': global_provider_id
    }
