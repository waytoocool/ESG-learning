"""
Tenant-scoped query mixins for multi-tenant architecture.

This module provides mixins that enforce tenant isolation at the query level,
ensuring that data is properly filtered by company_id for tenant-scoped models.
"""

from flask import g
from ..extensions import db
from sqlalchemy import or_


class TenantScopedQueryMixin:
    """
    Mixin class that provides tenant-scoped query methods for multi-tenant models.
    
    This mixin ensures that all queries are automatically filtered by the current
    tenant's company_id, preventing cross-tenant data access.
    
    Usage:
        class Entity(db.Model, TenantScopedQueryMixin):
            # ... model definition
            
        # In views/services:
        entities = Entity.query_for_tenant(db.session).all()
        entity = Entity.query_for_tenant(db.session).filter_by(id=entity_id).first()
    
    Requirements:
        - Model must have a 'company_id' column
        - Flask's g object must contain 'tenant' attribute (set by tenant middleware)
        - Tenant must be loaded before using these methods
    """
    
    @classmethod
    def query_for_tenant(cls, session):
        """
        Create a query that is automatically filtered by the current tenant.
        
        Args:
            session: SQLAlchemy session object (typically db.session)
            
        Returns:
            Query: SQLAlchemy query object filtered by current tenant's company_id
            
        Raises:
            Exception: If tenant is not loaded in request context
            
        Example:
            # Get all entities for current tenant
            entities = Entity.query_for_tenant(db.session).all()
            
            # Get specific entity with additional filters
            entity = Entity.query_for_tenant(db.session).filter_by(id=1).first()
        """
        if not hasattr(g, 'tenant') or g.tenant is None:
            raise Exception("Tenant not loaded in request context. Ensure tenant middleware is configured.")
        
        return session.query(cls).filter(
            or_(cls.company_id == g.tenant.id, cls.company_id == None)  # noqa: E711
        )
    
    @classmethod
    def get_for_tenant(cls, session, id):
        """
        Get a specific record by ID for the current tenant.
        
        Args:
            session: SQLAlchemy session object
            id: Primary key of the record to retrieve
            
        Returns:
            Model instance or None if not found or not accessible to current tenant
            
        Example:
            entity = Entity.get_for_tenant(db.session, entity_id)
        """
        return cls.query_for_tenant(session).filter_by(id=id).first()
    
    @classmethod
    def count_for_tenant(cls, session):
        """
        Count all records for the current tenant.
        
        Args:
            session: SQLAlchemy session object
            
        Returns:
            int: Number of records accessible to current tenant
            
        Example:
            entity_count = Entity.count_for_tenant(db.session)
        """
        return cls.query_for_tenant(session).count()
    
    @classmethod
    def exists_for_tenant(cls, session, **filters):
        """
        Check if a record exists for the current tenant with given filters.
        
        Args:
            session: SQLAlchemy session object
            **filters: Additional filter criteria
            
        Returns:
            bool: True if record exists and is accessible to current tenant
            
        Example:
            exists = Entity.exists_for_tenant(db.session, name='Test Entity')
        """
        return cls.query_for_tenant(session).filter_by(**filters).first() is not None


class TenantScopedModelMixin:
    """
    Mixin that provides tenant-aware model methods for creating and updating records.
    
    This mixin automatically sets the company_id when creating new records and
    provides validation methods for tenant isolation.
    """
    
    def set_tenant(self, tenant):
        """
        Set the company_id for this model instance.
        
        Args:
            tenant: Company instance representing the tenant
        """
        if hasattr(self, 'company_id'):
            self.company_id = tenant.id
        else:
            raise AttributeError(f"{self.__class__.__name__} does not have a company_id attribute")
    
    def belongs_to_tenant(self, tenant):
        """
        Check if this record belongs to the specified tenant.
        
        Args:
            tenant: Company instance representing the tenant
            
        Returns:
            bool: True if record belongs to tenant
        """
        if not hasattr(self, 'company_id'):
            return False
        return self.company_id == tenant.id
    
    def belongs_to_current_tenant(self):
        """
        Check if this record belongs to the current tenant from Flask's g object.
        
        Returns:
            bool: True if record belongs to current tenant
            
        Raises:
            Exception: If tenant is not loaded in request context
        """
        if not hasattr(g, 'tenant') or g.tenant is None:
            raise Exception("Tenant not loaded in request context")
        return self.belongs_to_tenant(g.tenant)
    
    @classmethod
    def create_for_tenant(cls, session, tenant, **kwargs):
        """
        Create a new record for the specified tenant.
        
        Args:
            session: SQLAlchemy session object
            tenant: Company instance representing the tenant
            **kwargs: Additional attributes for the new record
            
        Returns:
            New model instance with company_id set
            
        Example:
            entity = Entity.create_for_tenant(db.session, g.tenant, 
                                            name='New Entity', 
                                            entity_type='Subsidiary')
        """
        kwargs['company_id'] = tenant.id
        instance = cls(**kwargs)
        session.add(instance)
        return instance
    
    @classmethod
    def create_for_current_tenant(cls, session, **kwargs):
        """
        Create a new record for the current tenant from Flask's g object.
        
        Args:
            session: SQLAlchemy session object
            **kwargs: Additional attributes for the new record
            
        Returns:
            New model instance with company_id set
            
        Raises:
            Exception: If tenant is not loaded in request context
            
        Example:
            entity = Entity.create_for_current_tenant(db.session, 
                                                    name='New Entity', 
                                                    entity_type='Subsidiary')
        """
        if not hasattr(g, 'tenant') or g.tenant is None:
            raise Exception("Tenant not loaded in request context")
        return cls.create_for_tenant(session, g.tenant, **kwargs) 