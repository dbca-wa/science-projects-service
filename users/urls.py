from django.urls import path
from . import views

urlpatterns = [
    path("", views.Users.as_view()),
    path("smallsearch", views.SmallInternalUserSearch.as_view()),
    path("<int:pk>", views.UserDetail.as_view()),
    path("<int:pk>/toggleactive", views.ToggleUserActive.as_view()),
    path("me", views.Me.as_view()),
    path("profiles", views.UserProfiles.as_view()),
    path("profiles/<int:pk>", views.UserProfileDetail.as_view()),
    path("work", views.UserWorks.as_view()),
    path("work/<int:pk>", views.UserWorkDetail.as_view()),
    # path("<int:pk>", views.UserProfileView.as_view()),
    path("<int:pk>/admin", views.SwitchAdmin.as_view()),
    path("<int:pk>/pi", views.UpdatePersonalInformation.as_view()),
    path("<int:pk>/profile", views.UpdateProfile.as_view()),
    path("<int:pk>/membership", views.UpdateMembership.as_view()),
    path("check-email-exists", views.CheckEmailExists.as_view()),
    path("check-name-exists", views.CheckNameExists.as_view()),
    # path("profiles", views.UserProfile)
    # path("userworks", views.UserWorks.as_view()),
    # path("userworks/<int:pk>", views.UserWorkDetail.as_view()),
    # path("userprofiles", views.UserProfiles.as_view()),
    # path("userprofiles/<int:pk>", views.UserProfileDetail.as_view()),
    # path("sso-login", views.SSOLogin.as_view()),
    # path("jwt-login", views.JWTLogin.as_view()),
    path("directorate", views.DirectorateUsers.as_view()),
    path("log-in", views.Login.as_view()),
    path("log-out", views.Logout.as_view()),
    path("change-password", views.ChangePassword.as_view()),
]
