from django.template.defaulttags import register


@register.filter
def get_item(obj, key):
    try:
        return getattr(obj, key)
    except:
        return None


@register.filter
def get_dict_item(obj, key):
    try:
        return obj[str(key)]
    except:
        pass
