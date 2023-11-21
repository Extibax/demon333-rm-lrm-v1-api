from django.contrib import admin
from administration.models import Company, Department, FilterBy, Filter, JobPosition, TeamLeader, User, Role, Session, UserStatusLog, Value, ViewSharingAcc, ViewsLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name',
                    'date_joined', 'is_active', 'avatar', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name',
                     'date_joined', 'is_active', 'avatar', 'is_staff',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name', 'status')
    search_fields = ('role_name', 'status',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date_started')
    search_fields = ('user', 'date_started',)


@admin.register(ViewsLog)
class ViewsLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date', 'view')
    search_fields = ('user', 'date', 'view',)


@admin.register(Filter)
class FiltersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')


@admin.register(Value)
class ValuesAdmin(admin.ModelAdmin):
    list_display = ('id', 'value',)
    search_fields = ('id', 'value',)


@admin.register(FilterBy)
class FilterByAdmin(admin.ModelAdmin):
    list_display = ('id', 'filter', 'value', "view_log")
    search_fields = ('id', 'filter', 'value', "view_log")


@admin.register(TeamLeader)
class TeamLeaderAdmin(admin.ModelAdmin):
    list_display = ('id', 'team_member', 'team_leader')
    search_fields = ('id', 'team_member', 'team_leader')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('id', 'value')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('id', 'value')


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('id', 'value')


@admin.register(UserStatusLog)
class UserStatusLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'last_login', 'country')
    search_fields = ('id', 'user', 'status', 'last_login', 'country')


@admin.register(ViewSharingAcc)
class ViewSharingAccAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'view')
    search_fields = ('id', 'user', 'view')
