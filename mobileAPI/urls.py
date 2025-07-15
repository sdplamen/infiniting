from django.urls import path
from mobileAPI.views import generate_token

urlpatterns = [
    path('token/', generate_token, name='api_token_auth'),
]
