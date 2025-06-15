from rest_framework import serializers
from .models import Event
from django.contrib.auth import get_user_model
from posts.serializers import SampleUserData

User = get_user_model()


class EventSerializer(serializers.ModelSerializer):
    creator = SampleUserData(read_only=True)
    attendees = SampleUserData(many=True, read_only=True)
    interested_users = SampleUserData(many=True, read_only=True)
    is_joined = serializers.SerializerMethodField()
    is_interested = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = "__all__"

    def get_is_joined(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user in obj.attendees.all()
        return False
    
    def get_is_interested(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user in obj.interested_users.all()
        return False
    
    def get_is_creator(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user == obj.creator
        return False