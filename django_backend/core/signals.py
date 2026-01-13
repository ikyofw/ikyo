from django.db.backends.signals import connection_created
from django.db.backends.postgresql.base import DatabaseWrapper
from django.dispatch import receiver
from core.utils.run_once import run_once


KEY = f"{__name__}.init_on_first_db_connection"


@receiver(connection_created, sender=DatabaseWrapper, dispatch_uid=KEY)
def initial_connection_to_db(sender, **kwargs):
    def init():        
        from core.init import init_ik
        init_ik()

    run_once(
        key=KEY,
        func=init,
        only_runserver=True,
    )
