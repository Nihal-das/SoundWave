from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('create-room/', views.create_room, name='create_room'),
    path('room/delete/<int:room_id>/', views.delete_room, name='delete_room'),
    path('room/<int:room_id>/', views.enter_room, name='enter_room'),
    path('request-join/<int:room_id>/', views.request_to_join, name='request_to_join'),
    path('room/<int:room_id>/requests/', views.manage_requests, name='manage_requests'),
    path('request/<int:request_id>/<str:action>/', views.handle_request_action, name='handle_request_action'),
]