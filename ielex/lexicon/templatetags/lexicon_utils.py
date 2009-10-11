from django import template

register = template.Library()

@register.filter
def in_list(value, a_list):
    return value in a_list
