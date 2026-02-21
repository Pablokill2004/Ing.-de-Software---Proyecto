from django.db import models

from conduit.apps.core.models import TimestampedModel


class Article(TimestampedModel):
    slug = models.SlugField(db_index=True, max_length=255, unique=True)
    title = models.CharField(db_index=True, max_length=255)
    description = models.TextField()
    body = models.TextField()

    author = models.ForeignKey(
        'profiles.Profile',
        on_delete=models.CASCADE,
        related_name='articles'
    )

    tags = models.ManyToManyField(
        'Tag',
        related_name='articles'
    )

    def __str__(self):
        return self.title


class Comment(TimestampedModel):
    body = models.TextField()

    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        'profiles.Profile',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __str__(self):
        return self.body[:50]


class Tag(TimestampedModel):
    tag = models.CharField(max_length=255)
    slug = models.SlugField(db_index=True, unique=True)

    def __str__(self):
        return self.tag
