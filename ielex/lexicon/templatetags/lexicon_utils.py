from django import template
from ielex.utilities import int2alpha

register = template.Library()

@register.filter
def in_list(value, a_list):
    return value in a_list
