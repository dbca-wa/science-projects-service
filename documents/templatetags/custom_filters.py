from django import template
import re
from bs4 import BeautifulSoup

register = template.Library()


@register.simple_tag(takes_context=True)
def store_page_number(context, project_title, page_number):
    if "page_numbers" not in context:
        context["page_numbers"] = {}
    context["page_numbers"][project_title] = page_number
    return ""


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def replace_backslashes(value):
    return value.replace("\\", "/")


@register.filter
def filter_by_project_kind(reports, kind):
    return [
        item
        for item in reports
        if hasattr(item, "document") and item.document.project.get("kind") in kind
    ]


@register.filter
def filter_by_role(team_members, role):
    return [item for item in team_members if item.get("role") == role]


@register.filter
def is_staff_filter(team_members):
    return [member for member in team_members if member["user"]["is_staff"]]


# Pass a list of area_types e.g. ["dbcaregion", "ibra"]
@register.filter
def filter_by_area(areas, area_types):
    return [item for item in areas if item.get("area_type") in area_types]


@register.filter
def get_scientists(team_members):
    excluded_roles = ["academicsuper", "student"]
    return [item for item in team_members if item.get("role") not in excluded_roles]


@register.filter
def get_student_level_text(value):
    if value == "pd":
        return "Post-Doc"
    elif value == "phd":
        return "PhD"
    elif value == "msc":
        return "MSc"
    elif value == "honours":
        return "BSc Honours"
    elif value == "fourth_year":
        return "Fourth Year"
    elif value == "third_year":
        return "Third Year"
    elif value == "undergrad":
        return "Undergraduate"
    else:
        return value


@register.filter
def abbreviated_name(user_obj):
    # print(user_obj)
    if user_obj["title"]:
        return (
            f"{user_obj['title']} {user_obj['display_first_name'][0]} {user_obj['display_last_name']}"
        )
    return f"{user_obj['display_first_name'][0]} {user_obj['display_last_name']}"


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
