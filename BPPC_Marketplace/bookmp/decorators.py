from .models import Profile
from django.contrib.auth.models import User
from rest_framework.response import Response

def disable_unverified_email_users(inner_func):
    def wrapped_function(request, *args, **kwargs):
        current_profile = Profile.objects.get(user=request.user)
        if current_profile.is_email_verified:
            return func
        else:
            return Response({
                'detail': 'Email not verified',
                'display_message': 'Please verify your email address first.'
            }, status=403) # 403 because we know who the client is, we just won't show them what they wanna see.
    return wrapped_function