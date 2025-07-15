from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from mobileAPI.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()

class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            token_type, token_key = auth_header.split()
        except ValueError:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')

        if token_type.lower() != 'token':
            raise AuthenticationFailed('Invalid token type. Expected "Token".')

        try:
            token = Token.objects.select_related('user').get(key=token_key)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted.')

        return (token.user, token)
