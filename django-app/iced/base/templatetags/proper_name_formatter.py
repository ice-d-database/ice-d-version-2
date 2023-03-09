from django.template.defaulttags import register


@register.filter
def pn_format(val, format_as):
    return val if not format_as or not val else format(float(val), format_as)
