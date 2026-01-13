from django.apps import AppConfig


class EsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'es'

    def ready(self):
        from . import signals
