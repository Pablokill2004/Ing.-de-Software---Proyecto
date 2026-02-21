from rest_framework import generics, mixins, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Comment, Tag
from .permissions import IsAuthorOrReadOnly
from .renderers import ArticleJSONRenderer, CommentJSONRenderer
from .serializers import ArticleSerializer, CommentSerializer, TagSerializer


def get_article_by_slug(slug):
    """
    Centralized article lookup — eliminates duplicated try/except blocks
    that were scattered across 5 view methods (DRY principle).

    Applies the Extract Method refactoring pattern: identical lookup logic
    is consolidated into a single, reusable function.
    """
    try:
        return Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        raise NotFound('An article with this slug does not exist.')


class ArticleViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):

    lookup_field = 'slug'
    queryset = Article.objects.select_related('author', 'author__user')
    permission_classes = (IsAuthenticatedOrReadOnly,)
    renderer_classes = (ArticleJSONRenderer,)
    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = self.queryset

        author = self.request.query_params.get('author', None)
        if author is not None:
            queryset = queryset.filter(author__user__username=author)

        tag = self.request.query_params.get('tag', None)
        if tag is not None:
            queryset = queryset.filter(tags__tag=tag)

        favorited_by = self.request.query_params.get('favorited', None)
        if favorited_by is not None:
            queryset = queryset.filter(
                favorited_by__user__username=favorited_by
            )

        return queryset

    def create(self, request):
        serializer_context = {
            'author': request.user.profile,
            'request': request
        }
        serializer_data = request.data.get('article', {})

        serializer = self.serializer_class(
            data=serializer_data, context=serializer_context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        serializer_context = {'request': request}
        page = self.paginate_queryset(self.get_queryset())

        serializer = self.serializer_class(
            page,
            context=serializer_context,
            many=True
        )

        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, slug):
        serializer_context = {'request': request}
        serializer_instance = get_article_by_slug(slug)

        serializer = self.serializer_class(
            serializer_instance,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, slug):
        serializer_context = {'request': request}
        serializer_instance = get_article_by_slug(slug)

        # Security fix: enforce ownership check (OWASP A01 — Broken Access Control).
        # Only the article's author may update it.
        self.check_object_permissions(request, serializer_instance)

        serializer_data = request.data.get('article', {})

        serializer = self.serializer_class(
            serializer_instance,
            context=serializer_context,
            data=serializer_data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_permissions(self):
        """
        Apply IsAuthorOrReadOnly for update operations so that
        check_object_permissions enforces ownership.
        """
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAuthenticatedOrReadOnly(), IsAuthorOrReadOnly()]
        return super().get_permissions()


class CommentsListCreateAPIView(generics.ListCreateAPIView):
    lookup_field = 'article__slug'
    lookup_url_kwarg = 'article_slug'
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Comment.objects.select_related(
        'article', 'article__author', 'article__author__user',
        'author', 'author__user'
    )
    renderer_classes = (CommentJSONRenderer,)
    serializer_class = CommentSerializer

    def filter_queryset(self, queryset):
        filters = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
        return queryset.filter(**filters)

    def create(self, request, article_slug=None):
        data = request.data.get('comment', {})
        context = {'author': request.user.profile}
        context['article'] = get_article_by_slug(article_slug)

        serializer = self.serializer_class(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentsDestroyAPIView(generics.DestroyAPIView):
    lookup_url_kwarg = 'comment_pk'
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    queryset = Comment.objects.all()

    def destroy(self, request, article_slug=None, comment_pk=None):
        try:
            comment = Comment.objects.get(pk=comment_pk)
        except Comment.DoesNotExist:
            raise NotFound('A comment with this ID does not exist.')

        # Security fix: enforce ownership check (OWASP A01).
        # Only the comment's author may delete it.
        self.check_object_permissions(request, comment)

        comment.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ArticlesFavoriteAPIView(APIView):
    """
    Handles favorite and unfavorite actions for articles.

    Refactored to use a shared _toggle_favorite helper, eliminating the
    near-duplicate post/delete methods (DRY principle).
    """
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ArticleJSONRenderer,)
    serializer_class = ArticleSerializer

    def _toggle_favorite(self, request, article_slug, action, success_status):
        """
        Shared helper that eliminates duplication between post() and delete().
        The only differences between favorite/unfavorite are the profile method
        called and the HTTP status code returned.
        """
        profile = request.user.profile
        serializer_context = {'request': request}
        article = get_article_by_slug(article_slug)

        getattr(profile, action)(article)

        serializer = self.serializer_class(article, context=serializer_context)
        return Response(serializer.data, status=success_status)

    def post(self, request, article_slug=None):
        return self._toggle_favorite(
            request, article_slug, 'favorite', status.HTTP_201_CREATED
        )

    def delete(self, request, article_slug=None):
        return self._toggle_favorite(
            request, article_slug, 'unfavorite', status.HTTP_200_OK
        )


class TagListAPIView(generics.ListAPIView):
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer

    def list(self, request):
        serializer_data = self.get_queryset()
        serializer = self.serializer_class(serializer_data, many=True)

        return Response({
            'tags': serializer.data
        }, status=status.HTTP_200_OK)


class ArticlesFeedAPIView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Article.objects.all()
    renderer_classes = (ArticleJSONRenderer,)
    serializer_class = ArticleSerializer

    def get_queryset(self):
        return Article.objects.filter(
            author__in=self.request.user.profile.follows.all()
        )

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer_context = {'request': request}
        serializer = self.serializer_class(
            page, context=serializer_context, many=True
        )

        return self.get_paginated_response(serializer.data)
