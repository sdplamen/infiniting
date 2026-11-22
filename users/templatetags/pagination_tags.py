from django import template

register = template.Library()


@register.simple_tag
def elided_pages(page_obj, on_each_side=1, on_ends=1):
    """Page numbers around the current page, with '…' gaps, e.g. 1 … 4 [5] 6 … 12."""
    return page_obj.paginator.get_elided_page_range(
        page_obj.number, on_each_side=on_each_side, on_ends=on_ends
    )


@register.simple_tag(takes_context=True)
def page_url(context, number):
    """'?page=N' that keeps the other query params (e.g. auctions' sort_by)."""
    params = context['request'].GET.copy()
    params['page'] = number
    return '?' + params.urlencode()
