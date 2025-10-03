from django import template
register = template.Library()

@register.filter
def eur(cents):
    try:
        return f"{(int(cents or 0) / 100):.2f}"
    except Exception:
        return "0.00"