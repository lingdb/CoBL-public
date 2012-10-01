# encoding: utf-8
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re

register = template.Library()

@register.filter
def in_list(value, a_list):
    return value in a_list

@register.filter
def is_truncated(value, length):
    return len(value.split()) > length

@register.filter
def wikilink(value):
    """
    Produce wiki style links to other pages within the database, for use in
    comments fields: {{ a_note|wikilink|truncatewords_html:5 }}
    Note that it's better to use truncatewords_html with this filter, rather
    than plain truncatewords
    """
    WIKILINK_RE = re.compile(r"""
            (?P<lead>\s|^)  # possible leading whitespace
            (?P<wikilink>/  # an initial /
              (\w+/)+       # multiples of any number of identifier chars + /
            )
            """,
            re.VERBOSE)
    def wikilink_sub_callback(match_obj):
        link = match_obj.group("wikilink")
        lead = match_obj.group("lead")
        return '%s<a href="%s">%s</a>' % (lead, escape(link), escape(link))
    return mark_safe(WIKILINK_RE.sub(wikilink_sub_callback, value))

@register.filter
def asint(value):
    """Try to convert the value to an integer"""
    try:
        return int(value)
    except TypeError:
        return value

@register.filter
def starrating(key):
    """Convert the A|B|C|X|L reliability rating to an image"""
    ratings = {"A":u"★★★",
            "B":u"★★",
            "C":u"★",
            "X":"X",
            "L":"L"}
    return ratings[key]
