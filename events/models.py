from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Event(models.Model):
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_events"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to="events/images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    attendees = models.ManyToManyField(
        User, related_name="attending_events", blank=True
    )
    interested_users = models.ManyToManyField(
        User, related_name="interested_events", blank=True
    )
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
