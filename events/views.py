from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from core.responses import CustomResponse
from rest_framework import status, permissions

from notifications.models import Notification
from posts.serializers import SampleUserData
from .models import Event
from .serializers import EventSerializer
from core.pagination import CustomPagination
from django.db.models import Q
# Create your views here.


class EventListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    def get(self, request):
        filter_type = request.query_params.get("filter", "all")
        if filter_type == "my":
            events = Event.objects.filter(creator=request.user).order_by("-start_time")
        elif filter_type == "joined":
            events = Event.objects.filter(attendees=request.user).order_by("-start_time")
        elif filter_type == "interested":
            events = Event.objects.filter(interested_users=request.user).order_by("-start_time")
        elif filter_type == "discover":
            events = Event.objects.exclude(creator=request.user).exclude(attendees=request.user).order_by("-start_time")
        else:
            events = Event.objects.all().order_by("-start_time")
        paginator = self.pagination_class()
        paginated_events = paginator.paginate_queryset(events, request)
        serializer = EventSerializer(paginated_events, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            message="Events fetched successfully",
            status=status.HTTP_200_OK,
            pagination=paginator.get_pagination_meta(),
        )

    def post(self, request):
        serializer = EventSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return CustomResponse(
                data=serializer.data,
                message="Event created successfully",
                status=status.HTTP_201_CREATED,
            )
        return CustomResponse(
            data=serializer.errors, message="Event creation failed", status=status.HTTP_400_BAD_REQUEST
        )

class EventDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Event, pk=pk)

    def get(self, request, pk):
        event = self.get_object(pk)
        serializer = EventSerializer(event, context={"request": request})
        return CustomResponse(data=serializer.data, message="Event fetched successfully", status=status.HTTP_200_OK)

    def put(self, request, pk):
        event = self.get_object(pk)
        if event.creator != request.user:
            return CustomResponse(message="Permission denied.", status=status.HTTP_403_FORBIDDEN)
        serializer = EventSerializer(event, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return CustomResponse(data=serializer.data, message="Event updated successfully", status=status.HTTP_200_OK)
        return CustomResponse(data=serializer.errors, message="Event update failed", status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(pk)
        if event.creator != request.user:
            return CustomResponse(message="Permission denied.", status=status.HTTP_403_FORBIDDEN)
        event.delete()
        return CustomResponse(message="Event deleted successfully", status=status.HTTP_200_OK)


class JoinEventAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if request.user in event.attendees.all():
            event.attendees.remove(request.user)
            Notification.objects.create(
                recipient=event.creator,
                sender=request.user,
                notification_type="event_not_joined",
                event=event,
            )
            return CustomResponse(message="You have left the event.", status=status.HTTP_200_OK)
        else:
            event.attendees.add(request.user)
            Notification.objects.create(
                recipient=event.creator,
                sender=request.user,
                notification_type="event_joined",
                event=event,
            )
            return CustomResponse(
                message="You have joined the event.", status=status.HTTP_200_OK
        )

class InterestedEventAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if request.user in event.interested_users.all():
            event.interested_users.remove(request.user)
            Notification.objects.create(
                recipient=event.creator,
                sender=request.user,
                notification_type="event_not_interested",
                event=event,
            )
            return CustomResponse(
                message="You are not interested in the event.", status=status.HTTP_200_OK
            )
        else:
            event.interested_users.add(request.user)
            Notification.objects.create(
                recipient=event.creator,
                sender=request.user,
                notification_type="event_interested",
                event=event,
            )
        return CustomResponse(
            message="You are interested in the event.", status=status.HTTP_200_OK
        )


class EventAttendeesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        attendees = event.attendees.all()
        paginator = self.pagination_class()
        paginated_attendees = paginator.paginate_queryset(attendees, request)
        serializer = SampleUserData(paginated_attendees, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            message="Event attendees fetched successfully",
            status=status.HTTP_200_OK,
            pagination=paginator.get_pagination_meta(),
        )

class EventInterestedUsersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        interested_users = event.interested_users.all()
        paginator = self.pagination_class()
        paginated_interested_users = paginator.paginate_queryset(interested_users, request)
        serializer = SampleUserData(paginated_interested_users, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            message="Event interested users fetched successfully",
            status=status.HTTP_200_OK,
            pagination=paginator.get_pagination_meta(),
        )