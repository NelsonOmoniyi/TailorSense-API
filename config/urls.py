"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Public landing page and authenticated home routes.
    path('', include('apps.core.urls')),
    path('api/users/', include('apps.users.urls')),
    # Mobile clients exchange the account username (currently the email) and
    # password for short-lived access and longer-lived refresh JWTs.
    path('api/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    # Mobile clients use the refresh token to obtain a new access token.
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]

