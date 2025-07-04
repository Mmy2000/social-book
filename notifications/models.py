from django.db import models
from django.conf import settings
from group.models import Group
from posts.models import Post, Comment, Like, CommentLike
from django.utils.timesince import timesince
from events.models import Event


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("like", "Like"),
        ("comment", "Comment"),
        ("reply", "Reply"),
        ("comment_like", "Comment Like"),
        ("friend_request", "Friend Request"),
        ("friend_request_accepted", "Friend Request Accepted"),
        ("friend_request_rejected", "Friend Request Rejected"),
        ("friend_request_cancelled", "Friend Request Cancelled"),
        ("group_invitation", "Group Invitation"),
        ("group_invitation_accepted", "Group Invitation Accepted"),
        ("group_invitation_declined", "Group Invitation Declined"),
        ("group_member_removed", "Group Member Removed"),
        ("event_joined", "Event Joined"),
        ("event_not_joined", "Event Not Joined"),
        ("event_interested", "Event Interested"),
        ("event_not_interested", "Event Not Interested"),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications_received",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications_sent",
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender.username} {self.notification_type} on {self.created_at}"
