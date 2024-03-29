import logging
import threading

import requests
from constance import config
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from sesame.utils import get_query_string, get_user

from apps.handlers import AvailableSources
from apps.home.forms import AuthForm, LoginForm

from ..helpers import get_redis_client, make_invitation_code_key
from .models import UserAccountModel, WaitingListUserAccountModel


def home(request):
    ctx = {
        "login_url": reverse("login_view"),
        "invitation_only": config.INVITATION_ONLY,
    }

    if request.user.is_authenticated:
        token = None
        try:
            token = UserAccountModel.objects.get(user=request.user).token
        except UserAccountModel.DoesNotExist:
            token = _generate_token_for_user(request.user)

        ctx["token"] = token
        ctx["notify_urls"] = []

        for source in AvailableSources:
            kwargs = {
                "user_token": token,
                "room_id": "your_matrix_room_id",
            }

            if source.value:
                kwargs["source"] = source.value

            reverse_notify = reverse("api-1:notify", kwargs=kwargs)

            ctx["notify_urls"].append(
                {
                    "url": request.build_absolute_uri(reverse_notify),
                    "type": source.value or "custom",
                }
            )

    return render(request, "home/index.html", context=ctx)


def _verify_captcha(solution: str) -> bool:
    if not config.FRIENDLY_CAPTCHA_ENABLED:
        return True

    verification = requests.post(
        "https://api.friendlycaptcha.com/api/v1/siteverify",
        json={
            "solution": solution,
            "secret": config.FRIENDLY_CAPTCHA_KEY,
            "sitekey": config.FRIENDLY_CAPTCHA_SITE_KEY,
        },
    )

    if verification.ok:
        try:
            response = verification.json()
            if response.get("success", False):
                return True
            else:
                logging.info(f"Unable to verify captcha: {response}")
                return False
        except Exception:

            return False
    else:
        logging.info(f"Unable to verify captcha, api error: {verification.text}")
        return False


def login_view(request):
    if request.POST:
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            email = login_form.cleaned_data["email"].lower()
            invitation_code = login_form.cleaned_data["invitation_code"]
            captcha_solution = login_form.cleaned_data["captcha_solution"]
            # verify
            if not _verify_captcha(captcha_solution):
                messages.add_message(
                    request, messages.ERROR, "Couldn't verify you're a human."
                )
                return redirect("home")

            user_model = get_user_model()
            requested_user, created = user_model.objects.get_or_create(
                username=email, email=email
            )

            # Generate token for account if created
            try:
                UserAccountModel.objects.get(user=requested_user)
            except UserAccountModel.DoesNotExist:
                _create_user_account(invitation_code, requested_user)

            try:
                WaitingListUserAccountModel.objects.get(user=requested_user)
                messages.add_message(
                    request,
                    messages.INFO,
                    f"You're in the waiting list, you will be notified when your account is enabled.",
                )
            except WaitingListUserAccountModel.DoesNotExist:
                # user exist and not in waiting list. continue login process
                token_qs = get_query_string(requested_user)

                magic_link = request.build_absolute_uri(reverse("login_view"))

                magic_link = f"{magic_link}{token_qs}"

                # TODO: celery
                async_task(send_magic_link, requested_user, magic_link)

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"A link was sent to {email}. Please check your inbox to login.",
                )
        else:
            messages.add_message(
                request, messages.ERROR, "Couldn't verify you're a human."
            )

    elif request.GET:
        auth_form = AuthForm(request.GET)
        if auth_form.is_valid():
            user = get_user(request)
            if user is None:
                messages.add_message(
                    request, messages.ERROR, "Link expired, please login again"
                )

    return redirect("home")


def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, "Logged out.")
    return redirect("home")


def send_magic_link(user, link):
    mail_content = f"""
    Use this magic link to login to Matrix-Webhooks: <a clicktracking=off href="{link}">{link}</a>
    """
    send_mail(
        subject="[Matrix-Webhooks] Login magic link",
        message=mail_content,
        html_message=mail_content,
        from_email=None,
        recipient_list=[user.email],
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


def _create_user_account(invitation_code, requested_user) -> None:
    if not config.INVITATION_ONLY:
        return _generate_token_for_user(requested_user)

    redis_client = get_redis_client()
    invitation_code_key = make_invitation_code_key(invitation_code)
    remaining_invitation = redis_client.get(invitation_code_key)
    if remaining_invitation and int(remaining_invitation) > 0:
        _generate_token_for_user(requested_user)
        redis_client.decr(invitation_code_key)
    else:
        _add_to_waiting_list(requested_user)


def _add_to_waiting_list(user):
    waiting_list_account, _ = WaitingListUserAccountModel.objects.get_or_create(
        user=user
    )
