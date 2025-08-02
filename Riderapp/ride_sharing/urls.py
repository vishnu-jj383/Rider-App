from django.urls import path
# from .views import (
#     UserRegisterView, RideCreateView, RideListView, RideDetailView,
#     RideStatusUpdateView, RideLocationUpdateView, RideAcceptView, RideMatchDriverView
# )
from .views import UserRegisterView,RideCreateView, RideListView,RideLocationUpdateView, RideDetailView,RideStatusUpdateView,  RideAcceptView, RideMatchDriverView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('users/register/', UserRegisterView.as_view(), name='user-register'),
    path('rides/', RideCreateView.as_view(), name='ride-create'),
    path('rides/list/', RideListView.as_view(), name='ride-list'),
    path('rides/<int:pk>/', RideDetailView.as_view(), name='ride-detail'),
    path('rides/<int:pk>/update_status/', RideStatusUpdateView.as_view(), name='ride-status-update'),
    # path('rides/update_location/<int:pk>', RideLocationUpdateView.as_view(), name='ride-location-update'),
    path('rides/location/<int:pk>', RideLocationUpdateView.as_view(), name='ride-location-update'),

    path('rides/<int:pk>/accept/', RideAcceptView.as_view(), name='ride-accept'),
    path('rides/match_driver/', RideMatchDriverView.as_view(), name='ride-match-driver'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]