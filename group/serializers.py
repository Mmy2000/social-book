from rest_framework import serializers
from .models import Group, GroupMember, GroupInvitation
from django.contrib.auth import get_user_model
from posts.serializers import SampleUserData


class GroupMemberSerializer(serializers.ModelSerializer):
    user = SampleUserData(read_only=True)

    class Meta:
        model = GroupMember
        fields = ["id", "user", "role", "joined_at"]


class GroupSerializer(serializers.ModelSerializer):
    created_by = SampleUserData(read_only=True)
    members_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "created_by",
            "created_at",
            "updated_at",
            "is_private",
            "cover_image",
            "members_count",
            "is_member",
            "user_role",
        ]

    def get_members_count(self, obj):
        return obj.members.count()

    def get_is_member(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.members.filter(id=request.user.id).exists()
        return False

    def get_user_role(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                member = GroupMember.objects.get(group=obj, user=request.user)
                return member.role
            except GroupMember.DoesNotExist:
                return None
        return None


class GroupCreateSerializer(serializers.ModelSerializer):
    cover_image = serializers.ImageField(required=False)

    class Meta:
        model = Group
        fields = ["name", "description", "is_private", "cover_image"]

    def validate_cover_image(self, value):
        if value:
            # Check file size (limit to 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image size should not exceed 5MB")

            # Check file extension
            allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]
            import os

            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    "Unsupported file extension. Allowed extensions are: jpg, jpeg, png, gif"
                )
        return value


class GroupInvitationSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    invited_by = SampleUserData(read_only=True)
    invited_user = SampleUserData(read_only=True)

    class Meta:
        model = GroupInvitation
        fields = ["id", "group", "invited_by", "invited_user", "status", "created_at"]
        read_only_fields = ["status"]


class GroupInvitationCreateSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1, write_only=True
    )

    def validate_user_ids(self, value):
        group = self.context.get("group")
        User = get_user_model()

        # Check if all users exist
        existing_users = User.objects.filter(id__in=value)
        if len(existing_users) != len(value):
            raise serializers.ValidationError("One or more users do not exist")

        # Check if any users are already members
        existing_members = GroupMember.objects.filter(
            group=group, user_id__in=value
        ).values_list("user_id", flat=True)

        if existing_members:
            member_usernames = User.objects.filter(id__in=existing_members).values_list(
                "username", flat=True
            )
            raise serializers.ValidationError(
                f"Users {', '.join(member_usernames)} are already members of this group"
            )

        # Check for existing pending invitations
        pending_invites = GroupInvitation.objects.filter(
            group=group, invited_user_id__in=value, status="pending"
        ).values_list("invited_user_id", flat=True)

        if pending_invites:
            pending_usernames = User.objects.filter(id__in=pending_invites).values_list(
                "username", flat=True
            )
            raise serializers.ValidationError(
                f"Users {', '.join(pending_usernames)} already have pending invitations"
            )

        return value

    def create(self, validated_data):
        group = self.context.get("group")
        invited_by = self.context.get("invited_by")
        user_ids = validated_data.get("user_ids")

        invitations = []
        for user_id in user_ids:
            invitation = GroupInvitation.objects.create(
                group=group, invited_by=invited_by, invited_user_id=user_id
            )
            invitations.append(invitation)

        return invitations
