from django import template
import re
from bs4 import BeautifulSoup

register = template.Library()


@register.filter
def filter_by_role(team_members, role):
    return [item for item in team_members if item.get("role") == role]


@register.filter
def get_scientists(team_members):
    excluded_roles = ["academicsuper", "student"]
    return [item for item in team_members if item.get("role") not in excluded_roles]


@register.filter
def escape_special_characters(value):
    special_characters = r"[\^\$\.\*\+\?\{\}\[\]\\\|\(\)]"
    return re.sub(special_characters, r"\\\g<0>", value)


@register.filter
def extract_text_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return "".join(soup.stripped_strings)
