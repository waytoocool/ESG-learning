# Field import templates for Phase 4

from typing import Dict, List, Any

class FieldImportTemplate:
    """Utility class for importing standard framework field templates."""
    
    # GRI Standards Template (subset for MVP)
    GRI_STANDARDS_TEMPLATE = {
        "framework_name": "GRI Standards",
        "description": "Global Reporting Initiative Standards for sustainability reporting",
        "topics": [
            {
                "name": "GRI 300 Environmental",
                "description": "Environmental disclosures",
                "children": [
                    {
                        "name": "GRI 302 Energy",
                        "description": "Energy consumption and efficiency disclosures",
                        "fields": [
                            {
                                "field_name": "Energy consumption within the organization",
                                "field_code": "gri_302_1",
                                "unit_category": "energy",
                                "default_unit": "GJ",
                                "value_type": "NUMBER",
                                "description": "Total fuel consumption within the organization from non-renewable sources"
                            },
                            {
                                "field_name": "Energy consumption outside of the organization",
                                "field_code": "gri_302_2",
                                "unit_category": "energy", 
                                "default_unit": "GJ",
                                "value_type": "NUMBER",
                                "description": "Energy consumption outside of the organization"
                            }
                        ]
                    },
                    {
                        "name": "GRI 305 Emissions", 
                        "description": "Greenhouse gas emissions disclosures",
                        "fields": [
                            {
                                "field_name": "Direct (Scope 1) GHG emissions",
                                "field_code": "gri_305_1",
                                "unit_category": "emission",
                                "default_unit": "tCO2e",
                                "value_type": "NUMBER",
                                "description": "Gross direct (Scope 1) GHG emissions in metric tons of CO2 equivalent"
                            },
                            {
                                "field_name": "Energy indirect (Scope 2) GHG emissions",
                                "field_code": "gri_305_2",
                                "unit_category": "emission",
                                "default_unit": "tCO2e", 
                                "value_type": "NUMBER",
                                "description": "Gross location-based energy indirect (Scope 2) GHG emissions"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "GRI 400 Social",
                "description": "Social disclosures",
                "children": [
                    {
                        "name": "GRI 401 Employment",
                        "description": "Employment-related disclosures",
                        "fields": [
                            {
                                "field_name": "New employee hires and employee turnover",
                                "field_code": "gri_401_1",
                                "unit_category": "count",
                                "default_unit": "headcount",
                                "value_type": "NUMBER",
                                "description": "Total number and rates of new employee hires and employee turnover"
                            }
                        ]
                    }
                ]
            }
        ]
    }

    AVAILABLE_TEMPLATES = {
        "gri": GRI_STANDARDS_TEMPLATE
    }

    @classmethod
    def get_available_templates(cls) -> Dict[str, Dict[str, str]]:
        """Get list of available import templates with metadata."""
        return {
            template_key: {
                "name": template_data["framework_name"],
                "description": template_data["description"],
                "field_count": cls._count_fields_in_template(template_data)
            }
            for template_key, template_data in cls.AVAILABLE_TEMPLATES.items()
        }

    @classmethod
    def _count_fields_in_template(cls, template_data: Dict) -> int:
        """Count total number of fields in a template."""
        count = 0
        for topic in template_data.get("topics", []):
            # Count direct fields
            count += len(topic.get("fields", []))
            # Count fields in children topics
            for child in topic.get("children", []):
                count += len(child.get("fields", []))
        return count

    @classmethod
    def get_template(cls, template_key: str) -> Dict[str, Any]:
        """Get a specific template by key."""
        if template_key not in cls.AVAILABLE_TEMPLATES:
            raise ValueError(f"Template '{template_key}' not found. Available: {list(cls.AVAILABLE_TEMPLATES.keys())}")
        
        return cls.AVAILABLE_TEMPLATES[template_key]

    @classmethod
    def preview_template_diff(cls, template_key: str, existing_field_codes: List[str]) -> Dict[str, Any]:
        """Preview what would be imported from a template."""
        template = cls.get_template(template_key)
        
        new_fields = []
        duplicate_fields = []
        
        def process_fields(fields_list, topic_path=""):
            for field in fields_list:
                field_code = field["field_code"]
                field_info = {
                    "field_name": field["field_name"],
                    "field_code": field_code,
                    "topic_path": topic_path,
                    "unit_category": field.get("unit_category"),
                    "default_unit": field.get("default_unit"),
                    "value_type": field.get("value_type", "NUMBER")
                }
                
                if field_code in existing_field_codes:
                    duplicate_fields.append(field_info)
                else:
                    new_fields.append(field_info)
        
        # Process template structure
        for topic in template.get("topics", []):
            topic_path = topic["name"]
            
            # Process direct fields
            if "fields" in topic:
                process_fields(topic["fields"], topic_path)
            
            # Process children topics
            for child in topic.get("children", []):
                child_path = f"{topic_path} > {child['name']}"
                if "fields" in child:
                    process_fields(child["fields"], child_path)
        
        return {
            "template_name": template["framework_name"],
            "template_description": template["description"],
            "new_fields": new_fields,
            "duplicate_fields": duplicate_fields,
            "new_field_count": len(new_fields),
            "duplicate_field_count": len(duplicate_fields),
            "total_template_fields": len(new_fields) + len(duplicate_fields)
        }
