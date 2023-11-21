"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
#from baton.autodiscover import admin as baton_admin

from django.urls import path
from django.urls.conf import include, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

import os
from administration import views
import store
schema_view = get_schema_view(
    openapi.Info(
        title=f"Local Retail Management API [{os.environ.get('PYTHON_ENV','local')}]",
        default_version="v2",
        description="REST implementation of Django authentication system.",
        contact=openapi.Contact(email="eduardo.be@samsung.com"),
        license=openapi.License(name="BSD License"),
    ),
    url=os.environ.get("SWAGGER_BASE_URL", ""),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    #path('', baton_admin.site.urls),
    path('healthcheck', views.healthcheck),
    path('admin/', admin.site.urls),
    path('stores/', include('store.urls')),
    path('products/', include('product.urls')),
    path('administration/', include('administration.urls')),
    path('reports/', include('reports.urls')),

    path(r'swagger/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    #path('test', Test.as_view()),
    path('api/v1/', include('djoser.urls')),
    path('api/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),



    #path('admin/', admin.site.urls),
    #path('baton/', include('baton.urls')),

]
