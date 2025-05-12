from django_filters import FilterSet, ModelChoiceFilter
from .models import Article, Category


class ArticleFilter(FilterSet):
    category = ModelChoiceFilter(
        field_name='category',
        queryset=Category.objects.all(),
        label='Category',
        empty_label='Все категории',
    )


    class Meta:
        model = Article
        fields = {
            'title': ['icontains'],
        }