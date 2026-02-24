from django import template

register = template.Library()


@register.filter
def display_name(conversa, membro):
    return conversa.get_display_name(for_membro=membro)
