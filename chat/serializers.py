from rest_framework import serializers
from .models import Conversation, ConversationMessage
from accounts.serializers import FriendSerializer


class ConversationMessageSerializer(serializers.ModelSerializer):
    sent_to = FriendSerializer(many=False, read_only=True)
    created_by = FriendSerializer(many=False, read_only=True)

    class Meta:
        model = ConversationMessage
        fields = (
            "id",
            "body",
            "sent_to",
            "is_read",
            "created_by",
            "created_at",
        )


class ConversationListSerializer(serializers.ModelSerializer):
    users = FriendSerializer(many=True, read_only=True)
    messages = ConversationMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "users",
            "messages",
            "modified_at",
        )
        


class ConversationDetailSerializer(serializers.ModelSerializer):
    users = FriendSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "users",
            "modified_at",
        )
