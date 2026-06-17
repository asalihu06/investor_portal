from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('investor', 'Investor'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='investor')
    email = models.EmailField(unique=True)  # ← add this
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username