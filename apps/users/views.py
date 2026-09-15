"""HTTP handlers for the user API."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .services import authenticate_user, create_user


def _email_matches_user(email, user):
    return email and email.strip().lower() == user.email.lower()


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


# Public endpoint that verifies credentials and returns JWT credentials.
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

    refresh = RefreshToken.for_user(user)
    return Response({
        'user': UserSerializer(user).data,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


# Protected endpoint that revokes the refresh token.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    email = request.data.get('email')
    refresh_token = request.data.get('refresh')
    if not email or not refresh_token:
        return Response({'detail': 'Email and refresh token are required.'}, status=400)
    if not _email_matches_user(email, request.user):
        return Response({'detail': 'Email does not match the authenticated user.'}, status=403)

    try:
        token = RefreshToken(refresh_token)
        if str(token.get('user_id')) != str(request.user.pk):
            raise TokenError('Refresh token does not belong to the authenticated user.')
        token.blacklist()
    except TokenError:
        return Response({'detail': 'Invalid refresh token.'}, status=400)

    return Response(status=status.HTTP_204_NO_CONTENT)


# Protected endpoint used by the frontend to restore the current user on load.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    email = request.query_params.get('email')
    if not _email_matches_user(email, request.user):
        return Response({'detail': 'Email does not match the authenticated user.'}, status=403)
    return Response(UserSerializer(request.user).data)


