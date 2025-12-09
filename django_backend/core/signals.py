from django.db.backends.signals import connection_created
from django.db.backends.postgresql.base import DatabaseWrapper
from django.dispatch import receiver


has_init = False

@receiver(connection_created, sender=DatabaseWrapper)
def initial_connection_to_db(sender, **kwargs):
    global has_init
    import core.utils.django_utils as ikDjangoUtils
    if ikDjangoUtils.isRunDjangoServer() and not has_init:
        has_init = True
        from core.init import initIk
        initIk()