from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import Http404

from .models import User, UserResponse
from django.db.models import Exists, OuterRef
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings

from .forms import ArticleForm, UserResponseForm
from .models import Article, Category, Subscription
from datetime import datetime
from .filters import ArticleFilter

class ArticleList(ListView):
    model = Article
    ordering = '-article_time'
    template_name = 'articles.html'
    context_object_name = 'articles'
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = ArticleFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.utcnow()
        context['filterset'] = self.filterset
        return context


class ArticleDetail(LoginRequiredMixin, DetailView):
    model = Article
    template_name = 'article.html'
    context_object_name = 'article'

    def post(self, request, *args, **kwargs):
        article = self.get_object()
        if self.request.method == 'POST':
            form = UserResponseForm(self.request.POST)
            if form.is_valid():
                userresponse = form.save(commit=False)
                userresponse.author = self.request.user
                userresponse.article_id = article.id
                userresponse.save()

                subject = 'Новый отклик на ваше объявление'
                message = (
                    f'Здравствуйте, {article.author.first_name or article.author.email}!\n\n'
                    f'На ваше объявление "{article.title}" оставлен отклик:\n\n'
                    f'"{userresponse.text}"\n\n'
                    f'От пользователя: {request.user.email}\n'
                    f'Посмотреть объявление: {request.build_absolute_uri(article.get_absolute_url())}'
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [article.author.email],
                    fail_silently=False,
                )

                return redirect('article_detail', article.id)
            else:
                context = self.get_context_data(object=article)
                context['form'] = form
                return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserResponseForm()
        return context


class ArticleCreate(LoginRequiredMixin, CreateView):
    form_class = ArticleForm
    model = Article
    template_name = 'article_create.html'
    success_url = reverse_lazy('article_list')


    def form_valid(self, form):
        success_url = reverse_lazy('article_list')
        article = form.save(commit=False)
        article.author = self.request.user
        article.save()
        return super().form_valid(form)


class ArticleUpdate(LoginRequiredMixin, UpdateView):
    form_class = ArticleForm
    model = Article
    template_name = 'article_edit.html'
    context_object_name = 'article'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user:
            raise Http404("Вы не можете редактировать это объявление.")
        return super().dispatch(request, *args, **kwargs)


class ArticleDelete(LoginRequiredMixin, DeleteView):
    model = Article
    template_name = 'article_delete.html'
    success_url = reverse_lazy('article_list')

@login_required
@csrf_protect
def subscriptions(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = Category.objects.get(id=category_id)
        action = request.POST.get('action')

        if action == 'subscribe':
            Subscription.objects.create(user=request.user, category=category)
        elif action == 'unsubscribe':
            Subscription.objects.filter(
                user=request.user,
                category=category,
            ).delete()

    categories_with_subscriptions = Category.objects.annotate(
        user_subscribed=Exists(
            Subscription.objects.filter(
                user=request.user,
                category=OuterRef('pk'),
            )
        )
    ).order_by('name')
    return render(
        request,
        'subscriptions.html',
        {'categories': categories_with_subscriptions},
    )


@login_required
def my_responses(request):
    # Получаем все отклики на объявления текущего пользователя
    articles = Article.objects.filter(author=request.user)
    selected_article_id = request.GET.get('article')
    if selected_article_id:
        selected_article = get_object_or_404(Article, pk=selected_article_id, author=request.user)
        responses = UserResponse.objects.filter(article=selected_article)
    else:
        selected_article = None
        responses = UserResponse.objects.filter(article__in=articles)

    # Обработка удаления отклика
    if request.method == 'POST':
        if 'delete_response' in request.POST:
            resp_id = request.POST.get('response_id')
            resp = get_object_or_404(UserResponse, pk=resp_id, article__author=request.user)
            resp.delete()
            if selected_article_id:
                return redirect(f"{request.path}?article={selected_article_id}")
            else:
                return redirect(request.path)

        if 'accept_response' in request.POST:
            resp_id = request.POST.get('response_id')
            resp = get_object_or_404(UserResponse, pk=resp_id, article__author=request.user)
            resp.status = True
            resp.save()
            send_mail(
                subject='Ваш отклик принят!',
                message=f'Ваш отклик на объявление "{resp.article.title}" был принят!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[resp.author.email],
                fail_silently=False,
            )
            if selected_article_id:
                return redirect(f"{request.path}?article={selected_article_id}")
            else:
                return redirect(request.path)

    return render(request, 'my_responses.html', {
        'article': articles,
        'responses': responses,
        'selected_article': selected_article,
    })


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'article.html'


class ConfirmUserView(TemplateView):
    template_name = 'account/email_confirm.html'

    def get(self, request, *args, **kwargs):
        # Если пользователь уже аутентифицирован, перенаправляем
        if request.user.is_authenticated:
            return redirect('article_list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        code = request.POST.get('code')
        print(f"Подтверждение: email={email}, code={code}")  # отладка

        try:
            user = User.objects.get(email=email, confirmation_code=code)

            if user.is_active:
                messages.info(request, 'Ваш аккаунт уже активирован.')
                return redirect('account_login')

            user.is_active = True
            user.confirmation_code = ''
            user.save()

            messages.success(request, 'Аккаунт успешно активирован! Теперь вы можете войти.')
            return redirect('account_login')

        except User.DoesNotExist:
            messages.error(request, 'Неверный код подтверждения или email.')
            return self.get(request)