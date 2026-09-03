from django.urls import include, path
from rest_framework.routers import DefaultRouter

from habits.views import HabitsViewSet, PublicHabitsListAPIView

router = DefaultRouter()
router.register("", HabitsViewSet, basename="habits")

urlpatterns = [
    path(
        "public/",
        PublicHabitsListAPIView.as_view(),
        name="public-habits",
    ),
    path("", include(router.urls)),
]
