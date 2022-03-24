import logging

from constance.signals import config_updated
from django.dispatch import receiver

from apps.helpers import get_redis_client, make_invitation_code_key


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    logging.info("Signal to update constance")
    logging.info(f"key:{key}, old: {old_value}, new: {new_value}, kw: {kwargs}")
    if key == 'INVITATION_CODE' and new_value != old_value:
        logging.info(f"updated value from {old_value} to {new_value}")
        redis_client = get_redis_client()
        redis_key = make_invitation_code_key(new_value)
        redis_client.incr(redis_key, sender.INVITATIONS)
