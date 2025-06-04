from django.shortcuts import render
from rest_framework import status, permissions, parsers
from rest_framework.views import APIView
from django.db.models import Q
from .models import Group, GroupMember, GroupInvitation
from .serializers import (
    GroupSerializer,
    GroupMemberSerializer,
    GroupCreateSerializer,
    GroupInvitationSerializer,
    GroupInvitationCreateSerializer,
)
from core.responses import CustomResponse
from notifications.models import Notification

# Create your views here.


class GroupListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get(self, request):
        filter_type = request.query_params.get("filter", "all")

        if filter_type == "my_groups":
            # Get groups where user is either a member or creator
            groups = Group.objects.filter(
                Q(members=request.user) | Q(created_by=request.user)
            ).distinct()
        elif filter_type == "created":
            # Get only groups created by the user
            groups = Group.objects.filter(created_by=request.user)
        elif filter_type == "joined":
            # Get only groups where user is a member
            groups = Group.objects.filter(members=request.user)
        elif filter_type == "discover":
            # Get groups where user is neither a member nor creator
            groups = Group.objects.exclude(
                Q(members=request.user) | Q(created_by=request.user)
            ).distinct()
        else:
            # Get all groups
            groups = Group.objects.all()

        serializer = GroupSerializer(groups, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message="Groups retrieved successfully",
        )

    def post(self, request):
        # Handle both multipart form data and JSON
        serializer = GroupCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                group = serializer.save(created_by=request.user)
                # Make the creator an admin member
                GroupMember.objects.create(user=request.user, group=group, role="admin")
                response_serializer = GroupSerializer(
                    group, context={"request": request}
                )
                return CustomResponse(
                    data=response_serializer.data,
                    status=status.HTTP_201_CREATED,
                    message="Group created successfully",
                )
            except Exception as e:
                return CustomResponse(
                    data=None,
                    status=status.HTTP_400_BAD_REQUEST,
                    message=f"Failed to create group: {str(e)}",
                )
        return CustomResponse(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
            message="Failed to create group",
        )


class GroupDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)
            serializer = GroupSerializer(group, context={"request": request})
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message="Group details retrieved successfully",
            )
        except Group.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Group not found"
            )

    def put(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)
            # Check if user is admin
            if not GroupMember.objects.filter(
                group=group, user=request.user, role="admin"
            ).exists():
                return CustomResponse(
                    status=status.HTTP_403_FORBIDDEN,
                    message="Only group admins can update group details",
                )

            # Handle cover image update
            serializer = GroupCreateSerializer(
                group, data=request.data, partial=True, context={"request": request}
            )

            if serializer.is_valid():
                try:
                    # If a new cover image is provided and there's an existing one, delete the old one
                    if "cover_image" in request.FILES and group.cover_image:
                        import os

                        if os.path.exists(group.cover_image.path):
                            os.remove(group.cover_image.path)

                    # Save the updated group
                    group = serializer.save()
                    response_serializer = GroupSerializer(
                        group, context={"request": request}
                    )
                    return CustomResponse(
                        data=response_serializer.data,
                        status=status.HTTP_200_OK,
                        message="Group updated successfully",
                    )
                except Exception as e:
                    return CustomResponse(
                        data=None,
                        status=status.HTTP_400_BAD_REQUEST,
                        message=f"Failed to update group: {str(e)}",
                    )
            return CustomResponse(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
                message="Failed to update group",
            )
        except Group.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Group not found"
            )

    def delete(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)
            # Check if user is admin
            if not GroupMember.objects.filter(
                group=group, user=request.user, role="admin"
            ).exists():
                return CustomResponse(
                    status=status.HTTP_403_FORBIDDEN,
                    message="Only group admins can delete the group",
                )

            # Delete the cover image file if it exists
            if group.cover_image:
                import os

                if os.path.exists(group.cover_image.path):
                    os.remove(group.cover_image.path)

            group.delete()
            return CustomResponse(
                status=status.HTTP_200_OK, message="Group deleted successfully"
            )
        except Group.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Group not found"
            )


class GroupMembershipView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)
            user = request.user

            # Check if user is already a member
            if GroupMember.objects.filter(group=group, user=user).exists():
                return CustomResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="You are already a member of this group",
                )

            # Create membership
            GroupMember.objects.create(user=user, group=group, role="member")

            serializer = GroupSerializer(group, context={"request": request})
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message="Successfully joined the group",
            )
        except Group.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Group not found"
            )

    def delete(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)
            user = request.user

            try:
                membership = GroupMember.objects.get(group=group, user=user)
                if (
                    membership.role == "admin"
                    and GroupMember.objects.filter(group=group, role="admin").count()
                    == 1
                ):
                    return CustomResponse(
                        status=status.HTTP_400_BAD_REQUEST,
                        message="Cannot leave group - you are the only admin",
                    )
                membership.delete()
                return CustomResponse(
                    status=status.HTTP_200_OK, message="Successfully left the group"
                )
            except GroupMember.DoesNotExist:
                return CustomResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="You are not a member of this group",
                )
        except Group.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Group not found"
            )


class GroupMembersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)
            members = GroupMember.objects.filter(group=group)
            serializer = GroupMemberSerializer(members, many=True)
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message="Group members retrieved successfully",
            )
        except Group.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Group not found"
            )


class GroupInviteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)

            # Check if user is admin or moderator
            if not GroupMember.objects.filter(
                group=group, user=request.user, role__in=["admin", "moderator"]
            ).exists():
                return CustomResponse(
                    status=status.HTTP_403_FORBIDDEN,
                    message="Only group admins and moderators can send invitations",
                )

            serializer = GroupInvitationCreateSerializer(
                data=request.data, context={"group": group}
            )

            if serializer.is_valid():
                invitation = serializer.save(group=group, invited_by=request.user)

                # Create notification for invited user
                Notification.objects.create(
                    recipient=invitation.invited_user,
                    sender=request.user,
                    notification_type="group_invitation",
                    group=group,
                )

                response_serializer = GroupInvitationSerializer(
                    invitation, context={"request": request}
                )
                return CustomResponse(
                    data=response_serializer.data,
                    status=status.HTTP_201_CREATED,
                    message="Invitation sent successfully",
                )

            return CustomResponse(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
                message="Failed to send invitation",
            )

        except Group.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Group not found"
            )


class GroupInvitationResponseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invitation_id):
        try:
            invitation = GroupInvitation.objects.get(
                pk=invitation_id, invited_user=request.user, status="pending"
            )

            action = request.data.get("action")
            if action not in ["accept", "decline"]:
                return CustomResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="Invalid action. Use 'accept' or 'decline'",
                )

            if action == "accept":
                # Create group membership
                GroupMember.objects.create(
                    user=request.user, group=invitation.group, role="member"
                )
                invitation.status = "accepted"

                # Create notification for invitation sender
                Notification.objects.create(
                    recipient=invitation.invited_by,
                    sender=request.user,
                    notification_type="group_invitation_accepted",
                    group=invitation.group,
                )

                message = "Invitation accepted successfully"
            else:
                invitation.status = "declined"

                # Create notification for invitation sender
                Notification.objects.create(
                    recipient=invitation.invited_by,
                    sender=request.user,
                    notification_type="group_invitation_declined",
                    group=invitation.group,
                )

                message = "Invitation declined successfully"

            invitation.save()
            serializer = GroupInvitationSerializer(
                invitation, context={"request": request}
            )
            return CustomResponse(
                data=serializer.data, status=status.HTTP_200_OK, message=message
            )

        except GroupInvitation.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Invitation not found or already processed",
            )


class UserInvitationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invitations = GroupInvitation.objects.filter(
            invited_user=request.user, status="pending"
        )
        serializer = GroupInvitationSerializer(
            invitations, many=True, context={"request": request}
        )
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message="Invitations retrieved successfully",
        )
