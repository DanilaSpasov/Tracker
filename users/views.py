from rest_framework import generics
from rest_framework.permissions import AllowAny

from users.serializers import UserRegistrationSerializer


class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)
