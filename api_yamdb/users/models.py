from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

    ROLES = (
        (USER, "user"),
        (MODERATOR, "moderator"),
        (ADMIN, "admin"),
    )

    username = models.CharField(max_length=150, unique=True)

    email = models.EmailField(max_length=254, unique=True, blank=True)

    bio = models.TextField(
        "Биография",
        blank=True,
    )

    role = models.CharField(
        max_length=9,
        choices=ROLES,
        default=USER,
    )

    confirmation_code = models.CharField(max_length=50, default='0')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email", "username"], name="unique_email_username"
            )
        ]
