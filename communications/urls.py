from django.urls import path

from . import views

urlpatterns = [
    path("comments", views.Comments.as_view()),
    path("comments/<int:pk>", views.CommentDetail.as_view()),
    path("direct_messages", views.DirectMessages.as_view()),
    path("direct_messages/<int:pk>", views.DirectMessageDetail.as_view()),
    path("chat_rooms", views.ChatRooms.as_view()),
    path("chat_rooms/<int:pk>", views.ChatRoomDetail.as_view()),
    path("reactions", views.Reactions.as_view()),
    path("reactions/<int:pk>", views.ReactionDetail.as_view()),
]
