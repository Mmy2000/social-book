from django.urls import path
from memories.views import MemoriesAPIView

urlpatterns = [
    path("", MemoriesAPIView.as_view(), name="memories"),
]
