from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import get_user_model, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

import threading

from sesame.utils import get_query_string, get_user

from apps.home.forms import LoginForm, AuthForm
from .models import UserAccountModel

from apps.handlers import AvailableSources


def home(request):
    ctx = {
        'login_url': reverse('login_view')
    }

    if request.user.is_authenticated:
        token = None
        try:
            token = UserAccountModel.objects.get(user=request.user).token
        except UserAccountModel.DoesNotExist:
            token = _generate_token_for_user(request.user)

        ctx['token'] = token
        ctx['notify_urls'] = []

        for source in AvailableSources:
            kwargs = {
                'user_token': token,
                'room_id': 'your_matrix_room_id',
            }

            if source.value:
                kwargs['source'] = source.value

            reverse_notify = reverse('api-1:notify', kwargs=kwargs)

            ctx['notify_urls'].append({
                'url': request.build_absolute_uri(reverse_notify),
                'type': source.value or 'custom'
            })

    return render(request, 'home/index.html', context=ctx)


def login_view(request):

    if request.POST:
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            email = login_form.cleaned_data['email'].lower()
            userModel = get_user_model()
            requested_user, created = userModel.objects.get_or_create(username=email, email=email)

            # Generate token for account if created
            try:
                UserAccountModel.objects.get(user=requested_user)
            except UserAccountModel.DoesNotExist:
                _generate_token_for_user(requested_user)

            token_qs = get_query_string(requested_user)

            magic_link = request.build_absolute_uri(reverse('login_view'))

            magic_link = f'{magic_link}{token_qs}'

            # TODO: celery
            async_task(send_magic_link, requested_user, magic_link)

            messages.add_message(request,
                                 messages.SUCCESS,
                                 f'A link was sent to {email}. Please check your inbox to login.'
                                 )

    elif request.GET:
        auth_form = AuthForm(request.GET)
        if auth_form.is_valid():
            user = get_user(request)
            if user is None:
                messages.add_message(request, messages.ERROR, 'Link expired, please login again')

    return redirect('home')


def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, 'Logged out.')
    return redirect('home')


def send_magic_link(user, link):

    send_mail(
        '[Matrix-Webhooks] Login magic link',
        link,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )


def async_task(task_func, *args, **kwargs):
    task = threading.Thread(target=task_func, daemon=True, args=args, kwargs=kwargs)
    task.start()
    return task


def _generate_token_for_user(user):
    user_account = UserAccountModel(user=user)
    user_account.token = UserAccountModel.generate_token()
    user_account.save()
    return user_account.token
