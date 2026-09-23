from django import template

register = template.Library()

@register.filter
def get_error_message(error_list):
    try:
        return error_list[0].lower().capitalize()
    except:
        return ""