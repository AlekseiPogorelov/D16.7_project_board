from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Article, Subscription

@receiver(post_save, sender=Article)
def send_new_article_notifications(sender, instance, created, **kwargs):
    if created:
        category = instance.category
        subscriptions = Subscription.objects.filter(category=category)
        recipient_emails = [sub.user.email for sub in subscriptions if sub.user.email]

        if recipient_emails:
            subject = f'Новая публикация в категории "{category.get_name_display()}"'
            message = (
                f'Здравствуйте!\n\n'
                f'В категории "{category.get_name_display()}" появилась новая статья:\n\n'
                f'"{instance.title}"\n\n'
                f'Текст: {instance.text[:200]}...\n\n'
                f'Посмотреть статью: {settings.SITE_URL}{instance.get_absolute_url()}\n\n'
                f'Спасибо, что вы с нами!'
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_emails,
                fail_silently=False,
            )