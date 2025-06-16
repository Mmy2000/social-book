from django.shortcuts import render
from rest_framework.views import APIView
from accounts.serializers import FriendSerializer
from core.responses import CustomResponse
from rest_framework.permissions import IsAuthenticated
from datetime import date
from events.serializers import EventSerializer
from group.models import Group
from group.serializers import GroupSerializer
from posts.models import Post
from posts.serializers import PostSerializer
from rest_framework import status
from core.pagination import CustomPagination
from events.models import Event


class MemoriesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        today = date.today()
        user = request.user
        params = request.query_params.get("params")

        # Fetch posts with same day/month from previous years
        if params == "posts":
            posts = Post.objects.filter(
                created_by=user,
                created_at__day=today.day,
                created_at__month=today.month,
            ).exclude(
                created_at__year=today.year
            )  # exclude this year
            paginator = self.pagination_class()
            paginated_posts = paginator.paginate_queryset(posts, request)
            serializer = PostSerializer(paginated_posts, many=True)
        elif params == "events":
            events = Event.objects.filter(
                creator=user, start_time__day=today.day, start_time__month=today.month
            ).exclude(
                start_time__year=today.year
            )  # exclude this year
            paginator = self.pagination_class()
            paginated_events = paginator.paginate_queryset(events, request)
            serializer = EventSerializer(paginated_events, many=True)
        elif params == "groups":
            groups = Group.objects.filter(
                created_by=user,
                created_at__day=today.day,
                created_at__month=today.month,
            ).exclude(
                created_at__year=today.year
            )  # exclude this year
            paginator = self.pagination_class()
            paginated_groups = paginator.paginate_queryset(groups, request)
            serializer = GroupSerializer(paginated_groups, many=True)
        elif params == "friends":
            friends = user.friends.filter(
                date_joined__day=today.day, date_joined__month=today.month
            ).exclude(
                date_joined__year=today.year
            )  # exclude this year
            paginator = self.pagination_class()
            paginated_friends = paginator.paginate_queryset(friends, request)
            serializer = FriendSerializer(paginated_friends, many=True)
        else:
            return CustomResponse(
                data=[],
                status=status.HTTP_400_BAD_REQUEST,
                message="Please provide a valid parameter: posts, events, groups, or friends",
            )

        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message="Memories fetched successfully",
        )
