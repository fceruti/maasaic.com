from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from maasaic.apps.content.forms import CellCreateForm
from maasaic.apps.content.forms import CellOrderForm
from maasaic.apps.content.forms import CellPositionForm
from maasaic.apps.content.forms import CellVisibilityForm
from maasaic.apps.content.forms import PageCreateForm
from maasaic.apps.content.forms import PageUpdateForm
from maasaic.apps.content.forms import SectionCreateForm
from maasaic.apps.content.forms import SectionOrderForm
from maasaic.apps.content.forms import SectionVisibilityForm
from maasaic.apps.content.forms import UserCreateForm
from maasaic.apps.content.forms import UserLoginForm
from maasaic.apps.content.forms import WebsiteConfigForm
from maasaic.apps.content.forms import WebsiteCreateForm
from maasaic.apps.content.models import Cell
from maasaic.apps.content.models import Page
from maasaic.apps.content.models import Section
from maasaic.apps.content.models import Website


# ------------------------------------------------------------------------------
# Websites
# ------------------------------------------------------------------------------
class WebsiteListView(LoginRequiredMixin, ListView):
    template_name = 'frontend/website_list.html'
    context_object_name = 'websites'

    def get_queryset(self):
        return Website.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super(WebsiteListView, self).get_context_data(*args, **kwargs)
        context['website_create_form'] = WebsiteCreateForm()
        return context


class WebsiteCreateView(LoginRequiredMixin, FormView):
    template_name = 'frontend/website_create.html'
    form_class = WebsiteCreateForm

    def form_valid(self, form):
        website = form.save(commit=False)
        website.user = self.request.user
        website.save()
        msg = 'The site %s has been created. Keep it weird.' % website.domain
        messages.success(self.request, msg)
        url = reverse('website_detail', args=[website.subdomain])
        return HttpResponseRedirect(url)


class WebsiteDetailBase(LoginRequiredMixin, View):
    current_tab = None

    @cached_property
    def website(self):
        return get_object_or_404(Website,
                                 subdomain=self.kwargs['subdomain'],
                                 user=self.request.user)

    def get_object(self):
        return self.website

    def get_context_data(self, *args, **kwargs):
        context = super(WebsiteDetailBase, self).get_context_data(*args, **kwargs)
        context['website'] = self.website
        context['current_tab'] = self.current_tab
        return context


class WebsiteDetailView(RedirectView, WebsiteDetailBase):
    model = Website
    slug_field = 'subdomain'
    slug_url_kwarg = 'subdomain'

    def get_redirect_url(self, *args, **kwargs):
        return reverse('page_list', args=[self.website.subdomain])


class WebsiteConfigView(WebsiteDetailBase, UpdateView):
    template_name = 'frontend/website_detail_config.html'
    form_class = WebsiteConfigForm
    model = Website
    slug_field = 'subdomain'
    slug_url_kwarg = 'subdomain'
    current_tab = 'config'

    def get_success_url(self):
        return reverse('website_detail', args=[self.website.subdomain])


class WebsitePageAttrView(WebsiteDetailBase, UpdateView):
    template_name = 'frontend/website_detail_page_attr.html'
    form_class = WebsiteConfigForm
    model = Website
    slug_field = 'subdomain'
    slug_url_kwarg = 'subdomain'
    current_tab = 'page_attr'


class WebsiteCellAttrView(WebsiteDetailBase, UpdateView):
    template_name = 'frontend/website_detail_cell_attr.html'
    form_class = WebsiteConfigForm
    model = Website
    slug_field = 'subdomain'
    slug_url_kwarg = 'subdomain'
    current_tab = 'cell_attr'


# ------------------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------------------
class PageListView(WebsiteDetailBase, DetailView):
    template_name = 'frontend/page_list.html'
    form_class = WebsiteConfigForm
    model = Website
    slug_field = 'subdomain'
    slug_url_kwarg = 'subdomain'
    current_tab = 'pages'

    def get_context_data(self, **kwargs):
        context = super(PageListView, self).get_context_data(**kwargs)
        context['page_create_form'] = PageCreateForm(website=self.website)
        return context


class PageCreateView(CreateView, WebsiteDetailBase):
    template_name = 'frontend/page_create.html'
    model = Page
    form_class = PageCreateForm
    current_tab = 'pages'

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(PageCreateView, self).get_form_kwargs(*args, **kwargs)
        kw['website'] = self.website
        return kw

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Page created')
        url = reverse('page_list', args=[self.website.subdomain])
        return HttpResponseRedirect(url)


class PageConfigView(WebsiteDetailBase, UpdateView):
    template_name = 'frontend/page_config.html'
    model = Page
    current_tab = 'pages'
    context_object_name = 'page'
    form_class = PageUpdateForm

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(PageConfigView, self).get_form_kwargs(*args, **kwargs)
        kw['website'] = self.website
        return kw

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Page updated')
        url = reverse('page_list', args=[self.website.subdomain])
        return HttpResponseRedirect(url)

    def get_object(self, queryset=None):
        return get_object_or_404(Page,
                                 pk=self.kwargs['pk'],
                                 mode=Page.Mode.LIVE)


class PageUpdateView(DetailView, WebsiteDetailBase):
    template_name = 'frontend/page_update.html'
    model = Page

    def get_context_data(self, **kwargs):
        context = super(PageUpdateView, self).get_context_data(**kwargs)
        context['page_edit_on'] = True
        context['website'] = self.website
        from maasaic.apps.content.views.page import FONTS
        from maasaic.apps.content.views.page import FONTS_URL
        context['FONTS'] = FONTS
        context['FONTS_URL'] = FONTS_URL
        page = self.get_object()
        context['section_create_form'] = SectionCreateForm(page=page)
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Page,
                                 pk=self.kwargs['pk'],
                                 mode=Page.Mode.EDIT)


class PageDeleteView(DeleteView, WebsiteDetailBase):
    model = Page

    def get_object(self, queryset=None):
        return get_object_or_404(Page,
                                 pk=self.kwargs['pk'],
                                 mode=Page.Mode.LIVE)

    def get_success_url(self):
        return reverse('page_list', args=[self.website.subdomain])

    def delete(self, request, *args, **kwargs):
        response = super(PageDeleteView, self)\
            .delete(request, *args, **kwargs)
        messages.success(self.request, 'Your page has been deleted')
        return response


class PagePublishView(WebsiteDetailView):
    pass


# ------------------------------------------------------------------------------
# Page base
# ------------------------------------------------------------------------------
class PageBaseView(WebsiteDetailBase):

    @cached_property
    def page(self):
        return get_object_or_404(Page, pk=self.kwargs['page_pk'])

    def get_success_url(self):
        return reverse('page_update', args=[self.website.subdomain, self.page.pk])


# ------------------------------------------------------------------------------
# Sections
# ------------------------------------------------------------------------------
class SectionCreateView(CreateView):
    form_class = SectionCreateForm
    template_name = 'frontend/section_create.html'

    def get_form_kwargs(self):
        kw = super(SectionCreateView, self).get_form_kwargs()
        kw['page'] = None
        return kw

    def form_valid(self, form):
        section = form.save(commit=False)
        max_order = Section.objects.filter(page=section.page)\
            .aggregate(Max('order'))['order__max']
        section.order = max_order + 1
        section.save()
        url = reverse('page_update', args=[section.page.website.subdomain,
                                           section.page.pk])
        return HttpResponseRedirect(url)


class SectionOrderUpdateView(UpdateView):
    form_class = SectionOrderForm
    http_method_names = ['post']
    model = Section

    def get_success_url(self):
        section = self.get_object()
        return reverse('page_update', args=[section.page.website.subdomain,
                                            section.page.pk])

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())


class SectionVisibilityUpdateView(UpdateView):
    form_class = SectionVisibilityForm
    http_method_names = ['post']

    def get_object(self, queryset=None):
        section = get_object_or_404(Section, pk=self.kwargs['section_pk'])
        return section

    def get_success_url(self):
        section = self.get_object()
        url = section.page.absolute_path + '?edit=on'
        return url

    def form_valid(self, form):
        form.save(commit=True)
        return HttpResponseRedirect(redirect_to=self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return HttpResponseRedirect(redirect_to=self.get_success_url())


# ------------------------------------------------------------------------------
# Cells
# ------------------------------------------------------------------------------
class CellCreateView(CreateView, PageBaseView):
    model = Cell
    form_class = CellCreateForm

    def form_valid(self, form):
        cell = form.save(commit=True)
        url = reverse('page_update', args=[cell.section.page.website.subdomain,
                                           cell.section.page.pk])

        return HttpResponseRedirect(url)


class BaseCellUpdateView(UpdateView, PageBaseView):
    http_method_names = ['post']
    model = Cell

    def get_success_url(self):
        cell = self.get_object()
        return reverse('page_update', args=[cell.section.page.website.subdomain,
                                            cell.section.page.pk])

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())


class CellPositionUpdateView(BaseCellUpdateView):
    form_class = CellPositionForm


class CellVisibilityUpdateView(BaseCellUpdateView):
    form_class = CellVisibilityForm


class CellOrderUpdateView(BaseCellUpdateView):
    form_class = CellOrderForm


class CellDeleteView(DeleteView):
    model = Cell

    def get_success_url(self):
        cell = self.get_object()
        return reverse('page_update', args=[cell.section.page.website.subdomain,
                                            cell.section.page.pk])
