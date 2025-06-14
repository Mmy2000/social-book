from django.urls import path
from .views import EventListCreateAPIView, EventDetailAPIView, JoinEventAPIView, InterestedEventAPIView, EventAttendeesAPIView, EventInterestedUsersAPIView

urlpatterns = [
    path("", EventListCreateAPIView.as_view(), name="event-list-create"),
    path("<int:pk>/", EventDetailAPIView.as_view(), name="event_detail"),
    path("<int:pk>/join/", JoinEventAPIView.as_view(), name="event_join"),
    path("<int:pk>/interested/", InterestedEventAPIView.as_view(), name="event_interested"),
    path("<int:pk>/attendees/", EventAttendeesAPIView.as_view(), name="event_attendees"),
    path("<int:pk>/interested-users/", EventInterestedUsersAPIView.as_view(), name="event_interested_users"),
]
