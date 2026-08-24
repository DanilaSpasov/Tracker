from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from habits.models import Habit
from habits.paginators import HabitsPaginator
from habits.serializers import HabitSerializer


class HabitsViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    pagination_class = HabitsPaginator
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user).order_by("id")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PublicHabitsListAPIView(generics.ListAPIView):
    queryset = Habit.objects.filter(is_public=True).order_by("id")
    serializer_class = HabitSerializer
    pagination_class = HabitsPaginator
    permission_classes = (AllowAny,)
