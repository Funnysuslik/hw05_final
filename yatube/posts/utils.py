from django.core.paginator import Paginator

from . import constants


def paginate(request, model):
    """Разбивка вывода экземпляров модели на страницы"""
    paginator = Paginator(model, constants.MAX_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
