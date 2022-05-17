from django.core.paginator import Paginator
from django.conf import settings


def get_page_content(posts, request):
    paginator = Paginator(posts, settings.MAX_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
