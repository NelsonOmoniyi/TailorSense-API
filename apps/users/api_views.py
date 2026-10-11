"""JSON API views for account registration and session authentication."""

from django.contrib.auth import authenticate, logout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .auth import authenticated_required, get_authenticated_user, login_user
from .serializers import LoginSerializer, RegistrationSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Public endpoint that creates a User plus its required UserProfile.

    The serializer owns all validation (unique email, password rules, phone
    format) and writes the phone onto the profile because Django's built-in
    User has no phone field.
    """
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    # phone lives on UserProfile, not on the built-in User model.
    return Response(
        {'id': user.pk, 'email': user.email, 'fullname': user.first_name, 'phone': user.profile.phone},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Authenticate email/password and establish the browser session.

    Delegates session creation to ``login_user`` so the hash-based identity
    check in ``apps.users.auth`` stays the single source of truth.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        request,
        username=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
    )
    if user is None:
        return Response({'detail': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

    login_user(request, user)

    return Response({'id': user.pk, 'email': user.email, 'fullname': user.first_name}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authenticated_required
def signout(request):
    """Invalidate the current session for a signed-in user."""
    if get_authenticated_user(request) is None:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    logout(request)
    return Response({'detail': 'Signed out.'}, status=status.HTTP_200_OK)