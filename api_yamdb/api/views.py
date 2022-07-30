from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, permissions, filters, status

from api.filters import TitlesFilter
from users.models import User
from api.serializers import (
    CategorySerializer,
    GenreSerializer,
    TitleSerializer,
    TitleSerializerReadOnly,
    ReviewSerializer,
    CommentSerializer,
    UserSerializer,
    SignupSerializer,
    SignInSerializer,
)
from reviews.models import Category, Genre, Title, Review
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework_simplejwt.tokens import RefreshToken


class IsAdminModeratorAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.role == User.ADMIN
            or request.user.role == User.MODERATOR
            or obj.author == request.user
        )

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (
                request.user.is_authenticated
                and request.user.role == User.ADMIN
            )
            or (request.user.is_authenticated and request.user.is_superuser)
        )


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and request.user.role == User.ADMIN
        ) or (request.user.is_authenticated and request.user.is_superuser)


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class GenreViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (IsAdminOrReadOnly,)
    search_fields = ("name",)
    lookup_field = "slug"


class TitleViewSet(viewsets.ModelViewSet):
    queryset = (
        Title.objects.all().annotate(Avg("reviews__score")).order_by("name")
    )
    serializer_class = TitleSerializer
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitlesFilter

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return TitleSerializerReadOnly
        return TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminModeratorAuthorOrReadOnly]

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAdminModeratorAuthorOrReadOnly]

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get("review_id"))
        return review.comments.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, id=review_id, title=title_id)
        serializer.save(author=self.request.user, review=review)


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    lookup_field = "username"
    search_fields = ("username",)
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        methods=["patch", "get"],
        permission_classes=(permissions.IsAuthenticated,),
    )
    def me(self, request):
        user = get_object_or_404(User, username=request.user.username)

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        if request.method == "PATCH":
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            if (
                user.USER
                and serializer.validated_data.pop("role", "user") != user.USER
            ):
                return Response(
                    serializer.data, status=status.HTTP_403_FORBIDDEN
                )
            self.perform_update(serializer)
            return Response(serializer.data)


class SignUpViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get("username")
        email = serializer.validated_data.get("email").lower()
        try:
            user = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            if User.objects.filter(username=username).exists():
                return Response(
                    "Пользователь уже существует",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(email=email).exists():
                return Response(
                    "Электронный адрес уже существует",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = User.objects.create_user(username=username, email=email)
        user.is_active = False
        user.save()
        message = default_token_generator.make_token(user)
        email = EmailMessage(
            "Confirmation code",
            message,
            to=[serializer.validated_data.get("email")],
        )
        email.send()
        return Response(serializer.data, status=status.HTTP_200_OK)


class SignInViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = SignInSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        serializer = SignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=serializer.validated_data.get("username")
        )
        confirmation_code = serializer.validated_data.get("confirmation_code")
        if not default_token_generator.check_token(user, confirmation_code):
            return Response(
                "Неверный код подтверждения",
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = True
        user.save()
        token = RefreshToken.for_user(user)
        return Response(
            {"token": str(token.access_token)}, status=status.HTTP_200_OK
        )
