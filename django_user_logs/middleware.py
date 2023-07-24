from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from .models import UserLog
from django.dispatch import receiver
from django.db.models.signals import post_save
from functools import partial


class UserLoggingMiddleware(object):
    ip_address = None

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return response

    def process_request(self, request):
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            if hasattr(request, "user") and request.user.is_authenticated:
                user = request.user
            else:
                user = None

            session = request.session.session_key
            self.ip_address = request.META.get("REMOTE_ADDR", None)
            update_post_save_info = partial(
                self._update_post_save_info,
                user,
                session,
            )
            update_post_delete_info = partial(
                self._update_post_delete_info,
                user,
                session,
            )
            signals.post_save.connect(
                update_post_save_info,
                dispatch_uid=(
                    self.__class__,
                    request,
                ),
                weak=False,
            )
            signals.post_delete.connect(
                update_post_delete_info,
                dispatch_uid=(
                    self.__class__,
                    request,
                ),
                weak=False,
            )

    def _save_to_log(self, instance, action, user):
        print("----------------------------------")
        # pass
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
                ip=self.ip_address,
            )
            if UserLog.objects.all().count():
                last_log = UserLog.objects.latest("id")
                if not last_log.__eq__(userlog):
                    userlog.save()
            else:
                userlog.save()

    def _update_post_save_info(
            self,
            user,
            session,
            sender,
            instance,
            **kwargs):
        if sender in [UserLog, LogEntry, Session]:
            return None
        if kwargs["created"]:
            self._save_to_log(instance, UserLog.ACTION_TYPE_CREATE, user)
        else:
            self._save_to_log(instance, UserLog.ACTION_TYPE_UPDATE, user)

    def _update_post_delete_info(
            self,
            user,
            session,
            sender,
            instance,
            **kwargs):
        if sender in [UserLog, LogEntry, Session]:
            return None
        self._save_to_log(instance, UserLog.ACTION_TYPE_DELETE, user)
