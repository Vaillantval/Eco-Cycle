from django import template

register = template.Library()


@register.filter
def replace(value, arg):
    """Usage: {{ value|replace:"old,new" }}"""
    if ',' not in arg:
        return value
    old, new = arg.split(',', 1)
    return str(value).replace(old, new)


@register.filter
def dict_get(d, key):
    """Usage: {{ my_dict|dict_get:key }}"""
    if isinstance(d, dict):
        return d.get(str(key))
    return None
