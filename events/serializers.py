from rest_framework import serializers
from .models import Event
from django.contrib.auth import get_user_model
from posts.serializers import SampleUserData

User = get_user_model()


class EventSerializer(serializers.ModelSerializer):
    creator = SampleUserData(read_only=True)
    attendees = SampleUserData(many=True, read_only=True)
    interested_users = SampleUserData(many=True, read_only=True)

    class Meta:
        model = Event
        fields = "__all__"
