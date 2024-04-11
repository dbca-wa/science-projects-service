from django import template

register = template.Library()


@register.filter
def filter_by_role(team_members, role):
    return [item for item in team_members if item.get("role") == role]


@register.filter
def get_scientists(team_members):
    excluded_roles = ["academicsuper", "student"]
    return [item for item in team_members if item.get("role") not in excluded_roles]


# def filter_by_role(team_members, role):
#     return [item for item in team_members if item.role == role]
