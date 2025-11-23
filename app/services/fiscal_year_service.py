"""
Fiscal Year Service

This service provides utility functions for fiscal year operations after the migration
from assignment-level FY configuration to company-level FY configuration.

Key Features:
- Calculate current fiscal year for a company
- Generate fiscal year lists for dropdowns
- Convert between calendar and fiscal years
- Validate fiscal year dates
"""

from datetime import date, datetime
from typing import List, Tuple, Optional
from app.models import Company

class FiscalYearService:
    """Service for fiscal year operations."""
    
    @staticmethod
    def get_current_fy_year(company: Company) -> int:
        """
        Get the current fiscal year for a company based on today's date.
        
        Args:
            company (Company): The company to get the current FY for
            
        Returns:
            int: The current fiscal year (year containing the FY end date)
        """
        today = date.today()
        
        # Check which FY the current date falls into
        # Try current calendar year first
        current_year_fy_start = company.get_fy_start_date(today.year)
        current_year_fy_end = company.get_fy_end_date(today.year)
        
        if current_year_fy_start <= today <= current_year_fy_end:
            return today.year
        
        # If not in current calendar year's FY, check next year's FY
        next_year_fy_start = company.get_fy_start_date(today.year + 1)
        next_year_fy_end = company.get_fy_end_date(today.year + 1)
        
        if next_year_fy_start <= today <= next_year_fy_end:
            return today.year + 1
        
        # If not in next year's FY, must be in previous year's FY
        return today.year - 1
    
    @staticmethod
    def get_fy_year_list(company: Company, years_back: int = 5, years_forward: int = 2) -> List[Tuple[int, str]]:
        """
        Generate a list of fiscal years for dropdown/selection purposes.
        
        Args:
            company (Company): The company to generate FY list for
            years_back (int): Number of years to include before current FY
            years_forward (int): Number of years to include after current FY
            
        Returns:
            List[Tuple[int, str]]: List of (fy_year, display_string) tuples
        """
        current_fy = FiscalYearService.get_current_fy_year(company)
        fy_list = []
        
        start_fy = current_fy - years_back
        end_fy = current_fy + years_forward
        
        for fy_year in range(start_fy, end_fy + 1):
            display_string = company.get_fy_display(fy_year)
            fy_list.append((fy_year, display_string))
        
        return fy_list
    
    @staticmethod
    def is_date_in_fy(company: Company, check_date: date, fy_year: int) -> bool:
        """
        Check if a specific date falls within a company's fiscal year.
        
        Args:
            company (Company): The company whose FY to check
            check_date (date): The date to check
            fy_year (int): The fiscal year to check against
            
        Returns:
            bool: True if the date is within the fiscal year
        """
        fy_start = company.get_fy_start_date(fy_year)
        fy_end = company.get_fy_end_date(fy_year)
        
        return fy_start <= check_date <= fy_end
    
    @staticmethod
    def get_fy_year_for_date(company: Company, check_date: date) -> int:
        """
        Determine which fiscal year a specific date belongs to.
        
        Args:
            company (Company): The company whose FY calendar to use
            check_date (date): The date to determine FY for
            
        Returns:
            int: The fiscal year that contains the given date
        """
        # Start checking from a reasonable range around the date's calendar year
        for fy_year in range(check_date.year - 1, check_date.year + 2):
            if FiscalYearService.is_date_in_fy(company, check_date, fy_year):
                return fy_year
        
        # If not found in nearby years, calculate more precisely
        # This handles edge cases for unusual fiscal year configurations
        if company.get_fy_start_month() > check_date.month:
            # We're before the FY start month, so this is the next FY
            return check_date.year + 1
        else:
            # We're after or in the FY start month, so this is the current FY
            return check_date.year
    
    @staticmethod
    def get_next_reporting_period_end(company: Company, frequency: str, after_date: Optional[date] = None) -> date:
        """
        Get the next reporting period end date for a company based on frequency.
        
        Args:
            company (Company): The company to get reporting period for
            frequency (str): 'Monthly', 'Quarterly', or 'Annual'
            after_date (date, optional): Date to find next period after (defaults to today)
            
        Returns:
            date: The next reporting period end date
        """
        if after_date is None:
            after_date = date.today()
        
        current_fy = FiscalYearService.get_fy_year_for_date(company, after_date)
        
        # Get all reporting dates for current and next fiscal year
        from app.models import DataPointAssignment
        
        # Create a temporary assignment to use the reporting date logic
        temp_assignment = DataPointAssignment(
            field_id='temp',
            entity_id=1,
            frequency=frequency,
            assigned_by=1,
            company_id=company.id
        )
        temp_assignment.company = company
        
        # Get reporting dates for current FY
        current_fy_dates = temp_assignment.get_valid_reporting_dates(current_fy)
        
        # Find next date after after_date
        future_dates = [d for d in current_fy_dates if d > after_date]
        
        if future_dates:
            return min(future_dates)
        
        # If no future dates in current FY, get first date of next FY
        next_fy_dates = temp_assignment.get_valid_reporting_dates(current_fy + 1)
        return min(next_fy_dates) if next_fy_dates else None
    
    @staticmethod
    def validate_fy_date_range(company: Company, start_date: date, end_date: date) -> Tuple[bool, str]:
        """
        Validate that a date range is valid for a company's fiscal year calendar.
        
        Args:
            company (Company): The company to validate against
            start_date (date): The start date of the range
            end_date (date): The end date of the range
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if start_date > end_date:
            return False, "Start date must be before or equal to end date"
        
        # Check if both dates are in the same fiscal year
        start_fy = FiscalYearService.get_fy_year_for_date(company, start_date)
        end_fy = FiscalYearService.get_fy_year_for_date(company, end_date)
        
        if start_fy != end_fy:
            return False, f"Date range spans multiple fiscal years ({start_fy} to {end_fy})"
        
        return True, ""
    
    @staticmethod
    def get_fy_quarters(company: Company, fy_year: int) -> List[Tuple[date, date]]:
        """
        Get the four quarters for a fiscal year as (start_date, end_date) tuples.
        
        Args:
            company (Company): The company to get quarters for
            fy_year (int): The fiscal year
            
        Returns:
            List[Tuple[date, date]]: List of (quarter_start, quarter_end) tuples
        """
        from dateutil.relativedelta import relativedelta
        
        fy_start = company.get_fy_start_date(fy_year)
        quarters = []
        
        for quarter in range(4):
            quarter_start = fy_start + relativedelta(months=quarter * 3)
            quarter_end = fy_start + relativedelta(months=(quarter + 1) * 3) - relativedelta(days=1)
            
            # Ensure quarter doesn't exceed fiscal year end
            fy_end = company.get_fy_end_date(fy_year)
            if quarter_end > fy_end:
                quarter_end = fy_end
            
            quarters.append((quarter_start, quarter_end))
        
        return quarters

    @staticmethod
    def calculate_due_date(reporting_date: date, company: Company) -> date:
        """
        Calculate the due date for a reporting period based on company settings.

        Args:
            reporting_date (date): The reporting period end date
            company (Company): The company with due_days configuration

        Returns:
            date: The due date (reporting_date + data_due_days)
        """
        from datetime import timedelta

        due_days = getattr(company, 'data_due_days', 10)  # Default to 10 if not set
        return reporting_date + timedelta(days=due_days)

    @staticmethod
    def is_overdue(reporting_date: date, company: Company, today: Optional[date] = None) -> bool:
        """
        Check if a reporting period is overdue based on company settings.

        Args:
            reporting_date (date): The reporting period end date
            company (Company): The company with due_days configuration
            today (date, optional): Date to check against (defaults to today)

        Returns:
            bool: True if the reporting period is overdue
        """
        if today is None:
            today = date.today()

        due_date = FiscalYearService.calculate_due_date(reporting_date, company)
        return today > due_date