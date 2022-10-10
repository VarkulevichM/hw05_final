from django.core.paginator import Paginator

COUNT_POST_PER_PAGE = 10


def func_paginator(post_list, request):
    paginator = Paginator(post_list, COUNT_POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = dict(page_obj=page_obj)
    return context
