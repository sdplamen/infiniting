from django.apps import AppConfig


class ProfilConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from users.signals import create_profile