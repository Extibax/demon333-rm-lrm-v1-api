from django.urls import path
from locations.views import CountryView

from views.views import ViewsView

from .views import TeamLeaderView, UserPasswordlessEmailView, UserChangePasswordView, UserPasswordlessLink, UserStatusLogView, get_users_logs_by_country, save_photo_user, share_otp, users_by_countries_count, UserPasswordlessToken, active_users, users_visits, visits_table, weekly_active_users, JobPositionView, RoleView, UserChangePasswordV2View, view_report, average_active_time, FilterByView, new_users, UserLastLoginView, DepartmentView, new_visits, ActionLogView, ActionLogPost, get_user_permissions, RoleViewId, cache_layer_1_items, UserChangePasswordEmailView, AuthorizedEmailDomainView, CompanyView, UserViewId, UserView
app_name = "administration"
urlpatterns = [

    path('roles', RoleView.as_view()),
    path('roles/<int:id>', RoleViewId.as_view()),
    path('actionlog/<str:group>', ActionLogView.as_view(),
         name="actionlog_by_group"),
    path('actionlog', ActionLogPost.as_view()),
    path("userStatuslog/<str:group>", UserStatusLogView.as_view()),
    path("users", UserView.as_view()),
    path('savePhoto', save_photo_user),
    path("users/me/permissions", get_user_permissions),
    path("visitsTable", visits_table),
    path('activeUsers', active_users),
    path('usersVisits', users_visits),
    path('newUsers', new_users),
    path('weeklyUsers', weekly_active_users),
    path("usersCountries", users_by_countries_count),
    path("usersLogsCountries", get_users_logs_by_country),
    path('averageActiveTime', average_active_time),
    path('viewReports', view_report),
    path('newVisits', new_visits),
    path("users/lastLogin", UserLastLoginView.as_view()),
    path("users/changePassword", UserChangePasswordView.as_view()),
    path("users/changePassword/<int:id>", UserChangePasswordV2View.as_view()),
    path("users/changePasswordEmail",
         UserChangePasswordEmailView.as_view()),


    path("users/passwordlessEmail",
         UserPasswordlessEmailView.as_view()),
    path("users/passwordlessEmail/otp", UserPasswordlessToken.as_view()),
    path("users/passwordlessEmail/link", UserPasswordlessLink.as_view()),
    path('views', ViewsView.as_view()),
    path('users/<int:id>', UserViewId.as_view()),
    path('countries', CountryView.as_view()),

    # BIDX administration urls
    path('cacheLayerOneItems', cache_layer_1_items),
    path('filterBy', FilterByView.as_view()),
    path('authorizedEmails', AuthorizedEmailDomainView.as_view()),
    path('companies', CompanyView.as_view()),
    path('departments', DepartmentView.as_view()),
    path('jobPositions', JobPositionView.as_view()),
    path('teamLeaders', TeamLeaderView.as_view()),
    path('share', share_otp),
]
