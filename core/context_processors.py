from django.middleware.csrf import get_token

from .models import Notification, UserProfile


def ensure_csrf_cookie(request):
    """Force-set the csrftoken cookie on every page load, even though no
    template renders {% csrf_token %} — every POST in this app goes through
    fetch() with the header read from this cookie instead."""
    get_token(request)
    return {}


def app_context(request):
    ctx = {}
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        ctx["current_profile"] = profile
        ctx["unread_notifications_count"] = Notification.objects.filter(user=request.user, is_read=False).count()
        ctx["recent_notifications"] = Notification.objects.filter(user=request.user)[:6]
    return ctx
