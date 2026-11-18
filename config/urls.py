from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Define swagger_info at module level so settings.py can import it
swagger_info = openapi.Info(
    title="Money Wallet Ledger API",
    default_version='v1',
    description="ACID-compliant double-entry ledger API with idempotency controls",
)

schema_view = get_schema_view(
   swagger_info,
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('wallets.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]