from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from .models import UserLog
from functools import partial
from django.db.models.signals import post_save, post_delete

def _save_to_log(instance, action, user, ip_address):


    content_type = ContentType.objects.get_for_model(instance)
    if content_type.app_label != "user_log" and user:
        object_id = instance.id if hasattr(instance, "id") else 0
        userlog = UserLog(
            object_id=object_id,
            app_name=content_type.app_label,
            model_name=content_type.model,
            action=action,
            object_instance=serializers.serialize("json", [instance]),
            user=user,
            ip=ip_address,
        )
        if UserLog.objects.all().count():
            last_log = UserLog.objects.latest("id")
            if not last_log.__eq__(userlog):
                userlog.save()
        else:
            userlog.save()

def _update_post_save_info(user, session, sender, instance,ip_address, **kwargs):
    if sender in [UserLog]:
        return None
    if kwargs["created"]:
        _save_to_log(instance, UserLog.ACTION_TYPE_CREATE, user, ip_address)
    else:
        _save_to_log(instance, UserLog.ACTION_TYPE_UPDATE, user, ip_address)

def _update_post_delete_info(user, session, sender, instance,ip_address, **kwargs):
    if sender in [UserLog]:
        return None
    _save_to_log(instance, UserLog.ACTION_TYPE_DELETE, user, ip_address)
