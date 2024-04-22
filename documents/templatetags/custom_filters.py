from django import template
import re
from bs4 import BeautifulSoup

register = template.Library()


@register.filter
def filter_by_role(team_members, role):
    return [item for item in team_members if item.get("role") == role]


# Pass a list of area_types e.g. ["dbcaregion", "ibra"]
@register.filter
def filter_by_area(areas, area_types):
    return [item for item in areas if item.get("area_type") in area_types]


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


@register.filter
def remove_empty_p(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for p_tag in soup.find_all("p"):
        if p_tag.text.strip() == "&nbsp;":
            p_tag.extract()

    return "".join(soup.stripped_strings)
