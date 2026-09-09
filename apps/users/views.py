"""HTTP handlers for the user API."""

from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .services import authenticate_user, create_user


# Public endpoint that accepts registration JSON and returns the new user.
# @api_view also rejects HTTP methods other than POST before this function runs.
@api_view(['POST'])
def register(request):
    # Validate and normalize input before calling business logic.
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # Keep database operations in services.py so this view remains HTTP-focused.
    user = create_user(**serializer.validated_data)
    # Return only safe public fields and use 201 Created for a new resource.
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# Public endpoint that verifies credentials and starts a Django session.
# The client must preserve the returned session cookie for protected requests.
@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # Delegate credential lookup to the service layer.
    user = authenticate_user(request=request, **serializer.validated_data)

    if user is None:
        # One generic error avoids revealing whether an email has an account.
        return Response(
            {'detail': 'Invalid email or password.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Store the authenticated user's ID in the session for later requests.
    auth_login(request, user)
    return Response(UserSerializer(user).data)


# Protected endpoint that ends the current authenticated session.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    # Remove authentication state and return 204 because no response body is needed.
    auth_logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


# Protected endpoint used by the frontend to restore the current user on load.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    # SessionAuthentication and Django middleware populate request.user for us.
    return Response(UserSerializer(request.user).data)


