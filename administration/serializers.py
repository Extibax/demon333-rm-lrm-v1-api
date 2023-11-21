from django.db.models import fields
from rest_framework import serializers
from locations.models import Country
from product.serializers import DivisionSerializer

from store.serializers import AccountSerializer, PointOfSaleSerializer
from views.serializer import ViewSerializer


from .models import FilterBy, Role, User, ViewSharingAcc, ViewsLog, AuthorizedEmailDomain, Company, Department, JobPosition, TeamLeader
from locations.serializers import CountrySerializer
from views.serializer import ViewSerializer
# https://djoser.readthedocs.io/en/latest/settings.html#serializers
from djoser.serializers import UserCreateSerializer as BaseUserRegistrationSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer


class UserDeleteSerializer(serializers.Serializer):
    def validate_current_password(self):
        # verify if user have access to delete users
        return True


class UserRegistrationSerializer(BaseUserRegistrationSerializer):

    class Meta(BaseUserRegistrationSerializer.Meta):

        fields = ('email', 'password', "first_name",
                  "last_name", "avatar", "date_joined", "is_active", "is_staff", "is_dev", "roles")


class RoleNameNormalizer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("role_name",)


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = (
            "id",
            "role_name"
        )


class RoleSerializer(serializers.ModelSerializer):
    countries = CountrySerializer(many=True)
    accounts = AccountSerializer(many=True)
    point_of_sales = PointOfSaleSerializer(many=True)
    divisions = DivisionSerializer(many=True)
    views = ViewSerializer(many=True)

    class Meta:
        model = Role
        fields = (
            "id",
            "role_name",
            "status",
            "countries",
            "point_of_sales",
            "accounts",
            "views",
            "divisions"
        )


class UserBasicSerializer(BaseUserSerializer):
    #roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ("email",)
        ref_name = "UserBasicSerializer"


class CountryUserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("name", "id")


class UserSerializer(BaseUserSerializer):
    #roles = RoleSerializer(many=True, read_only=True)
    country = CountryUserBasicSerializer()

    class Meta(BaseUserSerializer.Meta):
        fields = ('id', 'email', "first_name", "last_name", "full_name", "avatar",
                  "country", "last_login", "roles", "company", 'inactivity_status', "jobposition", 'department_name')
        ref_name = "UserSerializer"


class SimpleUserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ('id', "full_name")


class TeamLeaderSerializer(serializers.ModelSerializer):
    team_leader = serializers.IntegerField(source="team_leader.id")

    class Meta:
        model = TeamLeader
        fields = ("team_leader",)


class UsersSerializer(BaseUserSerializer):
    teammember = TeamLeaderSerializer()

    class Meta(BaseUserSerializer.Meta):
        fields = ('id', 'email', "first_name", "last_name", "full_name", "avatar", "country",
                  "date_joined", "last_login", "roles", "is_active", "is_staff", "is_dev", "personal_phone", "work_phone", 'inactivity_status', "teammember", "company", "department", "job_position")
        ref_name = "UsersSerializer"


class ViewLogsSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer()
    view = ViewSerializer()
    country = CountrySerializer()

    class Meta:
        model = ViewsLog
        fields = (
            "id",
            "user",
            "date",
            "view",
            "country",
            "last_login",
            "roles",
            "divisions",
            "accounts",
        )


class ViewMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewsLog
        fields = (
            "id",
            'date',
            'user',
        )


class UserMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            'date_joined',
            'email',
        )


class FilterBySerializer(serializers.ModelSerializer):
    filter = serializers.CharField(source="filter.name")
    value = serializers.IntegerField(source="value.value")

    class Meta:
        model = FilterBy
        fields = (
            "id",
            "filter",
            "value",
            "view_log",
        )


class Authorized_EmailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorizedEmailDomain
        fields = (
            "id",
            "value",
        )


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            "id",
            "value",
        )


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = (
            "id",
            "value",
        )


class JobPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosition
        fields = (
            "id",
            "value",
        )


class TeamLeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamLeader
        fields = (
            "id",
            "team_member",
            "team_leader"
        )


class ViewSharingAccSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewSharingAcc
        fields = (
            "id",
            "user",
            'view'
        )
