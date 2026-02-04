"""
Project helper utilities
"""
from datetime import datetime as dt
from bs4 import BeautifulSoup


def strip_html_tags(html_string):
    """
    Strip HTML tags and return plain text
    
    Args:
        html_string: HTML string
        
    Returns:
        Plain text string
    """
    if not html_string:
        return ""
    soup = BeautifulSoup(html_string, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def handle_date_parsing(date_str):
    """
    Parse date string from frontend format
    
    Args:
        date_str: Date string in format "%Y-%m-%dT%H:%M:%S.%fZ"
        
    Returns:
        Date object or None
    """
    if not date_str:
        return None
    
    try:
        return dt.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
    except (ValueError, TypeError):
        return None


def parse_keywords(keywords_str):
    """
    Parse keywords string into list
    
    Args:
        keywords_str: Keywords string (e.g., '["keyword1", "keyword2"]')
        
    Returns:
        Comma-separated string
    """
    if not keywords_str:
        return ""
    
    # Remove brackets and quotes
    keywords_str = keywords_str.strip("[]").replace('"', "")
    keywords_list = [k.strip() for k in keywords_str.split(",")]
    
    return ",".join(keywords_list)
