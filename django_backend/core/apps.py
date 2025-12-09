from django.apps import AppConfig
import core.utils.django_utils as ikDjangoUtils

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        if ikDjangoUtils.isRunDjangoServer():
            import core.signals
