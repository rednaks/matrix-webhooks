from collections import OrderedDict

CONSTANCE_CONFIG = {
    "MATRIX_HOMESERVER": ("", "Matrix Home Server url (or e2e proxy url)", str),
    "MATRIX_BOT_USERNAME": ("", "Bot username, eg: @webhook:matrix-webhooks.com", str),
    "MATRIX_BOT_TOKEN": ("", "Bot token", str),
    "API_RATE_LIMIT": (1, "API Ratelimit, requests/seconds", int),
    "INVITATION_ONLY": (False, "Invitation only signups", bool),
    "INVITATION_CODE": ("", "Code Signup", str),
    "INVITATIONS": (0, "Number of invitations", int),
    "FRIENDLY_CAPTCHA_KEY": (
        "",
        "Friendly Captcha Secret Key",
        str,
    ),
    "FRIENDLY_CAPTCHA_SITE_KEY": ("", "Friendly Captcha Site Key", str),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict(
    {
        "Bot Settings": {
            "fields": ("MATRIX_HOMESERVER", "MATRIX_BOT_USERNAME", "MATRIX_BOT_TOKEN"),
        },
        "Site Settings": {
            "fields": (
                "API_RATE_LIMIT",
                "INVITATION_ONLY",
                "INVITATION_CODE",
                "INVITATIONS",
            ),
        },
        "Captcha Settings": {
            "fields": ("FRIENDLY_CAPTCHA_KEY", "FRIENDLY_CPATCH_SITE_KEY")
        },
    }
)
