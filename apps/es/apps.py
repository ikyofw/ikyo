from django.apps import AppConfig

class EsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'es'

    def ready(self):
        import core.utils.djangoUtils as ikDjangoUtils
        if ikDjangoUtils.isRunDjangoServer():
            from .core.setting import init_settings
            init_settings()