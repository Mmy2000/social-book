from django.urls import path
from . import views

app_name = "group"

urlpatterns = [
    path("", views.GroupListCreateView.as_view(), name="group-list-create"),
    path("my/", views.GroupListCreateView.as_view(), name="my-groups"),
    path("created/", views.GroupListCreateView.as_view(), name="created-groups"),
    path("joined/", views.GroupListCreateView.as_view(), name="joined-groups"),
    path("discover/", views.GroupListCreateView.as_view(), name="discover-groups"),
    path("<int:pk>/", views.GroupDetailView.as_view(), name="group-detail"),
    path("<int:pk>/join/", views.GroupMembershipView.as_view(), name="group-join"),
    path("<int:pk>/leave/", views.GroupMembershipView.as_view(), name="group-leave"),
    path("<int:pk>/members/", views.GroupMembersView.as_view(), name="group-members"),
    path("<int:pk>/invite/", views.GroupInviteView.as_view(), name="group-invite"),
    path("invitations/", views.UserInvitationsView.as_view(), name="user-invitations"),
    path(
        "invitations/<int:invitation_id>/respond/",
        views.GroupInvitationResponseView.as_view(),
        name="invitation-response",
    ),
]
