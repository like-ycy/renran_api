from django.utils import timezone as datetime

from article.models import Article


def interval_pub_article():
    """定时发布文章"""
    articles = Article.objects.filter(pub_date__lte=datetime.now())
    for article in articles:
        article.is_pub = True
        article.pub_date = None
        article.save()
        article.push_feed()
        # print("文章《%s》发布成功" % article.title)
