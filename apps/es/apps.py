from django.apps import AppConfig


class EsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'es'

    def ready(self):
        import core.utils.django_utils as ikDjangoUtils
        if ikDjangoUtils.isRunDjangoServer():
            import es.signals