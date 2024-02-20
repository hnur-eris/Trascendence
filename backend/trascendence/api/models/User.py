import django.utils.timezone
from django.db import models
from .SerializableModel import SerializableModel
import uuid


class UserModel(models.Model, SerializableModel):
    id = models.CharField(max_length=36, default=uuid.uuid4, primary_key=True)
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    intraId = models.IntegerField()
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=100, unique=True)
    avatarURI = models.CharField(max_length=200)
    password = models.CharField(max_length=72, blank=True, null=True,)


