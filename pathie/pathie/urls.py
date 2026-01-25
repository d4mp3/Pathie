"""
URL configuration for pathie project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from django.shortcuts import redirect
from core.views import (
    LandingPageView,
    LoginView,
    RegisterView,
    LogoutView,
    RegistrationAPIView,
    LoginAPIView,
    LogoutAPIView,
    RatingAPIView,
    RouteListAPIView,
    RouteDetailAPIView,
    RouteOptimizeAPIView,
    RouteAddPointAPIView,
    RoutePointDeleteAPIView,
    TagListView,
)

urlpatterns = [
    # Frontend views
    path("", LandingPageView.as_view(), name="landing_page"),
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Admin
    path("admin/", admin.site.urls),
    # API Authentication endpoints
    path("api/auth/registration/", RegistrationAPIView.as_view(), name="api_registration"),
    path("api/auth/login/", LoginAPIView.as_view(), name="api_login"),
    path("api/auth/logout/", LogoutAPIView.as_view(), name="api_logout"),
    # API Rating endpoint
    path("api/ratings/", RatingAPIView.as_view(), name="api_rating"),
    # API Tags endpoint
    path("api/tags/", TagListView.as_view(), name="api_tag_list"),
    # API Routes endpoints
    path("api/routes/", RouteListAPIView.as_view(), name="api_route_list"),
    path("api/routes/<int:pk>/", RouteDetailAPIView.as_view(), name="api_route_detail"),
    path("api/routes/<int:pk>/optimize/", RouteOptimizeAPIView.as_view(), name="api_route_optimize"),
    path("api/routes/<int:pk>/points/", RouteAddPointAPIView.as_view(), name="api_route_add_point"),
    path("api/routes/<int:pk>/points/<int:point_id>/", RoutePointDeleteAPIView.as_view(), name="api_route_point_delete"),
]
