from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def render_breadcrumbs(context):
    items = context.get('breadcrumbs_items', [])
    if not items:
        return ''

    parts = []
    for i, item in enumerate(items):
        name = item.get('name', '')
        url = item.get('url')
        if i == len(items) - 1 or not url:
            parts.append(f'<li class="breadcrumb-item active" aria-current="page">{name}</li>')
        else:
            parts.append(f'<li class="breadcrumb-item"><a href="{url}">{name}</a></li>')

    html = f'<nav aria-label="breadcrumb"><ol class="breadcrumb">{"".join(parts)}</ol></nav>'
    return mark_safe(html)