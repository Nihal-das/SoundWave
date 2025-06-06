from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import User  # using Django's built-in User
from django.utils import timezone

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, mobile, name, password=None):
        if not mobile:
            raise ValueError("Mobile number is required")
        user = self.model(mobile=mobile, name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, unique=True)

    objects = UserManager()

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name
    

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_rooms')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class RoomJoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
    )
   
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'room')  # can't request multiple times

    def __str__(self):
        return f"{self.user.username} -> {self.room.name} ({self.status})"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"