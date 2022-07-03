from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Класс шаблона страници об авторе"""

    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Класс шаблона страницы о применённых технологиях программирования"""

    template_name = 'about/tech.html'
