from django.template.defaulttags import register


@register.filter
def replace(str, what, to):
    return str.replace(what, to)


@register.filter
def replace_snake(str):
    return str.replace("_", " ")
