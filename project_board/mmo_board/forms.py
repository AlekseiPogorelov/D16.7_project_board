from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail
from .models import Article, UserResponse, Category
from string import hexdigits
import random
import string


User = get_user_model()


class ArticleForm(forms.ModelForm):
    title = forms.CharField(min_length=1)
    text = forms.CharField(min_length=1)
    class Meta:
        model = Article
        fields = ['title', 'text', 'category', 'upload']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }


    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        text = cleaned_data.get('text')
        if title == text:
            raise ValidationError({
                'title': 'Должно быть уникальное название'
            })
        return cleaned_data


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='Имя', required=False)
    last_name = forms.CharField(max_length=30, label='Фамилия', required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже зарегистрирован")
        return email

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.is_active = False  # Аккаунт неактивен до подтверждения
        user.confirmation_code = str(random.randint(100000, 999999))
        user.save()

        # Отправка email с кодом
        self.send_confirmation_email(request, user.email, user.confirmation_code)

        return user

    def send_confirmation_email(self, request, email, code):
        subject = 'Код подтверждения регистрации'
        context = {
            'code': code,
            'email': email,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': request.get_host(),
        }

        text_content = f'Ваш код подтверждения: {code}'
        html_content = f'''
        <p>Ваш код подтверждения: <strong>{code}</strong></p>
        <p>Перейдите по <a href="{context['protocol']}://{context['domain']}/accounts/confirm-email/">
        ссылке</a> для завершения регистрации.</p>
        '''

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )


class UserResponseForm(forms.ModelForm):

    class Meta:
        model = UserResponse
        fields = ['text']
