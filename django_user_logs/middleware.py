from django.contrib.sessions.models import Session
from django.conf import settings
from .utils import _update_post_save_info, _update_post_delete_info
from functools import partial
from django.db.models import signals

class UserLoggingMiddleware(object):
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
            ip_address = request.META.get("REMOTE_ADDR", None)

            update_post_save = partial(
                _update_post_save_info,
                user=user,
                session=session,
                ip_address=ip_address
            )

            update_post_delete = partial(
                _update_post_delete_info,
                user=user,
                session=session,
                ip_address=ip_address
            )

            signals.post_save.connect(
                update_post_save,
                dispatch_uid=(
                    self.__class__,
                    request,
                ),
                weak=False,
            )

            signals.post_delete.connect(
                update_post_delete,
                dispatch_uid=(
                    self.__class__,
                    request,
                ),
                weak=False,
            )
