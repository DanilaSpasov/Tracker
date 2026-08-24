from rest_framework.pagination import LimitOffsetPagination


class HabitsPaginator(LimitOffsetPagination):
    default_limit = 5