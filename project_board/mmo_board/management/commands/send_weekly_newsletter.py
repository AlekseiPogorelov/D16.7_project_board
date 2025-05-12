from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from django.core.mail import send_mail
from django.conf import settings

from mmo_board.models import Subscription, Article


class Command(BaseCommand):
    help = 'Отправка еженедельной рассылки новых публикаций подписчикам'

    def handle(self, *args, **kwargs):
        one_week_ago = now() - timedelta(days=7)
        subscriptions = Subscription.objects.select_related('user', 'category')


        user_categories = {}
        for sub in subscriptions:
            user_categories.setdefault(sub.user, []).append(sub.category)

        for user, categories in user_categories.items():

            articles = Article.objects.filter(
                category__in=categories,
                article_time__gte=one_week_ago
            ).order_by('-article_time')

            if not articles.exists():
                continue


            message_lines = [f'Здравствуйте, {user.first_name or user.email}!\n\n']
            message_lines.append('Новые публикации за последнюю неделю по вашим подпискам:\n')

            for article in articles:
                message_lines.append(f'- {article.title} ({article.article_time.strftime("%Y-%m-%d")}): {article.get_absolute_url()}')

            message = '\n'.join(message_lines)

            send_mail(
                subject='Еженедельная рассылка новых публикаций',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            self.stdout.write(f'Отправлено письмо пользователю {user.email}')