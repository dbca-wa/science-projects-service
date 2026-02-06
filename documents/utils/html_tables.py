"""
HTML table utilities for document templates
"""
import json
from django.template.loader import render_to_string


class HTMLTableTemplates:
    """Utility class for loading and rendering HTML table templates"""
    
    @staticmethod
    def get_staff_time_allocation_template():
        """
        Get default staff time allocation table template
        
        Returns:
            str: HTML table template
        """
        return render_to_string('default_tables/staff_time_allocation.html').strip()
    
    @staticmethod
    def get_internal_budget_template():
        """
        Get default internal budget table template
        
        Returns:
            str: HTML table template
        """
        return render_to_string('default_tables/internal_budget.html').strip()
    
    @staticmethod
    def get_external_budget_template():
        """
        Get default external budget table template
        
        Returns:
            str: HTML table template
        """
        return render_to_string('default_tables/external_budget.html').strip()
    
    @staticmethod
    def get_concept_plan_budget_template():
        """
        Get default concept plan budget table template
        
        Returns:
            str: HTML table template
        """
        return render_to_string('default_tables/concept_plan_budget.html').strip()


# Callable defaults for Django model fields
def default_staff_time_allocation():
    """Callable default for staff_time_allocation field"""
    return HTMLTableTemplates.get_staff_time_allocation_template()


def default_internal_budget():
    """Callable default for internal budget field"""
    return HTMLTableTemplates.get_internal_budget_template()


def default_external_budget():
    """Callable default for external budget field"""
    return HTMLTableTemplates.get_external_budget_template()


def default_concept_plan_budget():
    """Callable default for concept plan budget field"""
    return HTMLTableTemplates.get_concept_plan_budget_template()


def json_to_html_table(json_string):
    """
    Convert JSON table data to HTML table
    
    Args:
        json_string: JSON string representing table data as 2D array
        
    Returns:
        str: HTML table or original string if not valid JSON
        
    Example:
        >>> data = '[["Header1", "Header2"], ["Row1Col1", "Row1Col2"]]'
        >>> html = json_to_html_table(data)
    """
    try:
        data = json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return json_string
    
    if not data or not isinstance(data, list):
        return json_string
    
    # Start building HTML table
    html_table = '<table class="table-light">\n  <colgroup>\n'
    
    # Add column for first column (headers)
    html_table += '    <col style="background-color: rgb(242, 243, 245);">\n'
    
    # Add columns for data columns
    if data and len(data[0]) > 0:
        for _ in range(len(data[0])):
            html_table += "    <col>\n"
    
    html_table += "  </colgroup>\n  <tbody>\n"
    
    # Build table rows
    for i, row in enumerate(data):
        html_table += "    <tr>\n"
        
        for j, cell in enumerate(row):
            # First row or first column gets header styling
            if i == 0 or j == 0:
                html_table += (
                    '      <th class="table-cell-light table-cell-header-light" '
                    'style="border: 1px solid black; width: 175px; vertical-align: top; '
                    'text-align: start; background-color: rgb(242, 243, 245);">\n'
                )
            else:
                html_table += (
                    '      <td class="table-cell-light" '
                    'style="border: 1px solid black; width: 175px; vertical-align: top; '
                    'text-align: start;">\n'
                )
            
            # Add cell content
            html_table += '        <p class="editor-p-light" dir="ltr">\n'
            html_table += f'          <span style="white-space: pre-wrap;">{cell}</span>\n'
            html_table += '        </p>\n'
            
            # Close cell
            tag = "th" if (i == 0 or j == 0) else "td"
            html_table += f"      </{tag}>\n"
        
        html_table += "    </tr>\n"
    
    html_table += "  </tbody>\n</table>"
    
    return html_table


# Convenience functions for backward compatibility
def get_staff_time_allocation_template():
    """Get default staff time allocation table template"""
    return HTMLTableTemplates.get_staff_time_allocation_template()


def get_internal_budget_template():
    """Get default internal budget table template"""
    return HTMLTableTemplates.get_internal_budget_template()


def get_external_budget_template():
    """Get default external budget table template"""
    return HTMLTableTemplates.get_external_budget_template()


def get_concept_plan_budget_template():
    """Get default concept plan budget table template"""
    return HTMLTableTemplates.get_concept_plan_budget_template()
