from rest_framework import serializers
from .models import Notification
from posts.serializers import PostSerializer, CommentSerializer
from accounts.serializers import FriendSerializer


class NotificationSerializer(serializers.ModelSerializer):
    sender = FriendSerializer(read_only=True)
    post = PostSerializer(read_only=True)
    comment = CommentSerializer(read_only=True)
    notification_message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "notification_type",
            "post",
            "comment",
            "is_read",
            "created_at",
            "notification_message",
            "event",
            "group",
        ]
        read_only_fields = [
            "id",
            "sender",
            "notification_type",
            "post",
            "comment",
            "created_at",
            "notification_message",
            "event",
            "group",
        ]

    def get_notification_message(self, obj):
        """Generate a human-readable message for the notification"""
        sender_name = obj.sender.userprofile.full_name

        if obj.notification_type == "like":
            reaction = "liked"
            if hasattr(obj.post, "likes"):
                like = obj.post.likes.filter(created_by=obj.sender).first()
                if like:
                    reaction = like.get_reaction_type_display()
            return f"{sender_name} reacted with {reaction} to your post"
        elif obj.notification_type == "comment":
            return f"{sender_name} commented on your post"
        elif obj.notification_type == "reply":
            return f"{sender_name} replied to your comment"
        elif obj.notification_type == "comment_like":
            reaction = "liked"
            if hasattr(obj.comment, "likes"):
                like = obj.comment.likes.filter(created_by=obj.sender).first()
                if like:
                    reaction = like.get_reaction_type_display()
            return f"{sender_name} reacted with {reaction} to your comment"
        elif obj.notification_type == "friend_request":
            return f"{sender_name} sent you a friend request"
        elif obj.notification_type == "friend_request_accepted":
            return f"{sender_name} accepted your friend request"
        elif obj.notification_type == "friend_request_rejected":
            return f"{sender_name} rejected your friend request"
        elif obj.notification_type == "friend_request_cancelled":
            return f"{sender_name} cancelled their friend request"
        elif obj.notification_type == "group_invitation":
            return f"{sender_name} invited you to join {obj.group.name}"
        elif obj.notification_type == "group_invitation_accepted":
            return f"{sender_name} accepted your group invitation"
        elif obj.notification_type == "group_invitation_declined":
            return f"{sender_name} declined your group invitation"
        elif obj.notification_type == "group_member_removed":
            return f"{sender_name} removed you from {obj.group.name}"
        elif obj.notification_type == "event_joined":
            return f"{sender_name} joined {obj.event.title}"
        elif obj.notification_type == "event_not_joined":
            return f"{sender_name} left {obj.event.title}"
        elif obj.notification_type == "event_interested":
            return f"{sender_name} is interested in {obj.event.title}"
        elif obj.notification_type == "event_not_interested":
            return f"{sender_name} is not interested in {obj.event.title}"
        return ""
