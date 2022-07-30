from api.views import (CategoryViewSet, CommentViewSet, GenreViewSet,
                       ReviewViewSet, SignInViewSet, SignUpViewSet,
                       TitleViewSet, UserViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"genres", GenreViewSet)
router.register(r"titles", TitleViewSet)
router.register(
    r"titles/(?P<title_id>\d+)/reviews", ReviewViewSet, basename="reviews"
)
router.register(
    r"titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)" r"/comments",
    CommentViewSet,
    basename="comments",
)
router.register(r"users", UserViewSet, basename="users",)
router.register('auth/signup', SignUpViewSet, basename='signup')
router.register('auth/token', SignInViewSet, basename='signin')

urlpatterns = [
    path("v1/", include(router.urls)),
]
