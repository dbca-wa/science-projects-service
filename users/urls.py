from django.urls import path
from . import views

urlpatterns = [
    path("", views.Users.as_view()),
    path("mypublicprofile", views.MyStaffProfile.as_view()),
    path("smallsearch", views.SmallInternalUserSearch.as_view()),
    path("<int:pk>", views.UserDetail.as_view()),
    path("<int:pk>/itassets", views.ITAssets.as_view()),
    path("<int:pk>/toggleactive", views.ToggleUserActive.as_view()),
    path("<int:pk>/projects", views.UsersProjects.as_view()),
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
    path("<int:pk>/remove_avatar", views.RemoveAvatar.as_view()),
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
    #
    path("staffprofiles", views.StaffProfiles.as_view()),
    path("staffprofiles/<int:pk>", views.StaffProfileDetail.as_view()),
    #
    path("employment_entries/", views.StaffProfileEmploymentEntries.as_view()),
    path(
        "employment_entries/<int:pk>", views.StaffProfileEmploymentEntryDetail.as_view()
    ),
    path("education_entries/", views.StaffProfileEducationEntries.as_view()),
    path(
        "education_entries/<int:pk>", views.StaffProfileEducationEntryDetail.as_view()
    ),
    #
    path("staffprofiles/<int:pk>/hero", views.StaffProfileHeroDetail.as_view()),
    path("staffprofiles/<int:pk>/overview", views.StaffProfileOverviewDetail.as_view()),
    path("staffprofiles/<int:pk>/cv", views.StaffProfileCVDetail.as_view()),
    # path("staffprofiles/<int:pk>/employment", views.StaffProfileHeroDetail.as_view()),
    # path("staffprofiles/<int:pk>/education", views.StaffProfileOverviewDetail.as_view()),
]
