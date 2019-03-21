import requests

from django.views.generic import TemplateView, ListView


class ListFilesListView(ListView):
    template_name = "index.html"

    def get_queryset(self):
        url = 'http://drupal.inmet.gov.br:8000/listFiles/?format=json'
        response = requests.get(url)
        return response.json()


class ListParametrosListView(ListView):
    template_name = "parametros.html"

    def get_queryset(self):
        url = 'http://drupal.inmet.gov.br:8000/getParametros/' + self.kwargs['param'] + '/?format=json'
        response = requests.get(url)
        return response.json()


class ListDetailListView(ListView):
    template_name = "detail.html"

    def get_queryset(self):
        url = 'http://drupal.inmet.gov.br:8000/getGrib/' + self.kwargs['param'] + '/' + self.kwargs['pk'] + '/?format=json'
        response = requests.get(url)
        return response.json()


class ListSectionsListView(ListView):
    template_name = "sections.html"

    def get_queryset(self):
        url = 'http://drupal.inmet.gov.br:8000/getSections/' + self.kwargs['param'] + '/' + self.kwargs['pk'] + '/?format=json'
        response = requests.get(url)
        return response.json()

    def get_context_data(self, **kwargs):
        context = super(ListSectionsListView, self).get_context_data(**kwargs)
        context['section_0'] = context['object_list']['Section_0']
        context['section_1'] = context['object_list']['Section_1']
        context['section_2'] = context['object_list']['Section_2']
        context['section_3'] = context['object_list']['Section_3']
        context['section_4'] = context['object_list']['Section_4']
        context['section_5'] = context['object_list']['Section_5']
        return context