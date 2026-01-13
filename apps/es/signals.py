from django.db.backends.signals import connection_created
from django.db.backends.postgresql.base import DatabaseWrapper
from django.dispatch import receiver
from core.utils.run_once import run_once


KEY = f"{__name__}.init_on_first_db_connection"


@receiver(connection_created, sender=DatabaseWrapper, dispatch_uid=KEY)
def initial_connection_to_db(sender, **kwargs):
    def init():
        from .core.setting import init_settings
        init_settings()
        # init notification
        from core.inbox import inbox_manager
        from core.core.lang import Boolean2
        from openfire.core.openfire import openfire 
        from .core.es_notification import add_notification_func
        def wci_inbox_message(sender_id, receiver_ids, category_str, record_status, summary, prms_dict) -> Boolean2:
            inbox_manager.send(sender_id, receiver_ids, category_str, summary, prms_dict)
            # send spark
            if not isinstance(receiver_ids, list):
                receiver_ids = [receiver_ids]
            openfire.send_message(message=summary, receiver_ids=receiver_ids,
                                  message_type='info',
                                  message_from='ES', message_title='ES Notification')
            return Boolean2.TRUE('success')
        add_notification_func(wci_inbox_message)

    run_once(
        key=KEY,
        func=init,
        only_runserver=True,
    )