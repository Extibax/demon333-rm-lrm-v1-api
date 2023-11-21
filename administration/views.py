import ast
import base64
import json
import re
import pytz

from administration.fetch import get_action_logs_data, get_user_status_log_data

from locations.models import Country
from product.models import Division
from product.serializers import ProductSerializer
from rest_framework.views import APIView

# from django.http import Http404,HttpResponseBadRequest,HttpResponseNotFound
# from django.core.paginator import Paginator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import Http404, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from drf_yasg.utils import swagger_auto_schema

# from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# from rest_framework import serializers,parsers

from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
from reports.views import sha256
from store.models import Account, PointOfSale
from datetime import datetime, timedelta
from views.models import View
from administration.serializers import UserSerializer
import os
from django.http import HttpRequest
from django.db.models import Q
# MODELS
from .models import AuthorizedEmailDomain, Filter, FilterBy, Role, User, Value, ViewSharingAcc, ViewsLog, PasswordChangeCode, Company, Department, JobPosition, TeamLeader
from .email_templates import email_change_credentials, email_credless_login, welcome_email, email_credless_login_otp, email_credless_login_link
# SERIALIZERS
from .serializers import FilterBySerializer, RoleSerializer, RolesSerializer, UserMetricSerializer, ViewLogsSerializer, ViewMetricSerializer, Authorized_EmailsSerializer, CompanySerializer, DepartmentSerializer, JobPositionSerializer, TeamLeaderSerializer
from api.common.email import send_mail
from administration.models import CacheProcessItem

import pandas as pd
import polars as pl
from api.settings import s3


@api_view(['GET'])
@permission_classes([AllowAny])
def healthcheck(request):
    return Response({"status": "healthy"})


@api_view(['GET'])
@permission_classes([AllowAny])
def cache_layer_1_items(request):
    return Response(CacheProcessItem.get()["Items"])


@api_view(['GET'])
def get_user_permissions(request):

    return Response(RoleSerializer(request.user.roles.all(), many=True).data)


class UserLastLoginView(APIView):
    def post(self, request: HttpRequest) -> Response:
        """
        set last login of logged in user
        """
        request.user.last_login = datetime.now()
        request.user.save()
        return Response(UserSerializer(request.user).data)


@permission_classes([AllowAny])
class UserPasswordlessEmailView(APIView):
    # add serializer
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, default="test@cheil.com", description="(string) user email"),
        }
    ))
    def post(self, request: HttpRequest) -> Response:
        """
        sent email to a user to change password
        """
        user = User.objects.get(email=request.data["email"])
        code = user.generate_otp()

        token = TokenObtainPairSerializer().validate({
            "email": user.email,
            "password": str(code)
        })["access"]

        result = send_mail("Login link", email_credless_login.format(
            token=token, otp=code, environmentValue=os.environ.get('FRONTEND_HOST', 'http://localhost:4200')), user.email)

        if result:
            return Response({
                "detail": "email sent succesfully"
            })
        else:
            Response({
                "detail": "an error occured"
            })


@permission_classes([AllowAny])
class UserPasswordlessToken(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, default="test@cheil.com", description="(string) user email"),
        }
    ))
    def post(self, request: HttpRequest) -> Response:
        """Sent email to user to OTP code"""
        user = User.objects.get(email=request.data["email"])
        code = user.generate_otp()

        TokenObtainPairSerializer().validate({
            "email": user.email,
            "password": str(code)
        })["access"]

        result = send_mail("One time password login", email_credless_login_otp.format(
            otp=code, environmentValue=os.environ.get('FRONTEND_HOST', 'http://localhost:4200')), user.email)

        if result:
            return Response({
                "detail": "email sent succesfully"
            })
        else:
            return Response({
                "detail": "an error occured"
            })


@permission_classes([AllowAny])
class UserPasswordlessLink(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, default="test@cheil.com", description="(string) user email"),
        }
    ))
    def post(self, request: HttpRequest) -> Response:
        """Sent email to user to OTP code"""
        user = User.objects.get(email=request.data["email"])
        code = user.generate_otp()

        token = TokenObtainPairSerializer().validate({
            "email": user.email,
            "password": str(code)
        })["access"]

        result = send_mail("Login link", email_credless_login_link.format(
            token=token, environmentValue=os.environ.get('FRONTEND_HOST', 'http://localhost:4200')), user.email)

        if result:
            return Response({
                "detail": "email sent succesfully"
            })
        else:
            return Response({
                "detail": "an error occured"
            })


class UserView(APIView):
    # add serializer
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, description="user email"),
            "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="user first name"),
            "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="user last name"),
            "roles": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER), description="list of role ids"),
            "avatar": openapi.Schema(type=openapi.TYPE_STRING, description="link avatar"),
            "country": openapi.Schema(type=openapi.TYPE_INTEGER, description="country id"),
            "personal_phone": openapi.Schema(type=openapi.TYPE_STRING, description="user personal telephone"),
            "work_phone": openapi.Schema(type=openapi.TYPE_STRING, description="user work phone"),
            "team_leader": openapi.Schema(type=openapi.TYPE_INTEGER, description="user leader id"),
            "company": openapi.Schema(type=openapi.TYPE_INTEGER, description="company id"),
            "department": openapi.Schema(type=openapi.TYPE_INTEGER, description="department id"),
            "job_position": openapi.Schema(type=openapi.TYPE_INTEGER, description="job_position id")
        }
    ))
    def post(self, request: HttpRequest) -> Response:
        """
        sent email to a user to change password
        """

        email, first_name, last_name, roles, avatar, country, personal_phone, work_phone, company, department, job_position = request.data["email"], request.data[
            "first_name"], request.data["last_name"], request.data["roles"], request.data["avatar"], request.data["country"], request.data["personal_phone"], request.data["work_phone"], request.data["company"], request.data["department"], request.data["job_position"]

        country = Country.objects.get(pk=country)
        company = Company.objects.get(pk=company)

        user = User(email=email,
                    first_name=first_name, last_name=last_name, avatar=avatar, country=country, personal_phone=personal_phone, work_phone=work_phone, company=company)
        if (department != None):
            department = Department.objects.get(pk=department)
            user.department = department
        if (job_position != None):
            job_position = JobPosition.objects.get(pk=job_position)
            user.job_position = job_position

        # verification of existing roles
        [Role.objects.get(pk=x) for x in roles]

        user.save()
        user.roles.add(*roles)

        if (request.data['team_leader'] != None):
            team_leader = User.objects.get(pk=request.data['team_leader'])
            team_leader_create = TeamLeader(
                team_leader=team_leader, team_member=user)
            team_leader_create.save()

        result = send_mail("Password recovery", welcome_email.format(
            user=user.first_name+" "+user.last_name,
            environmentValue=os.environ.get(
                'FRONTEND_HOST', 'http://localhost:4200')
        ), user.email)

        if result:
            return Response({
                "detail": "email sent succesfully"
            })
        else:
            Response({
                "detail": "an error occured"
            })

        # welcome email soon
        # result = send_mail("Reestablecimiento de contraseña", email_change_credentials.format(
        #    password_change_code=code.code
        # ), user.email)

        # if result:
        #    return Response({
        #        "detail": "email sent succesfully"
        #    })
        # else:
        #    Response({
        #        "detail": "an error occured"
        #    })
    def get(self, request: HttpRequest) -> Response:
        """
        get all users
        """
        if ((os.environ.get('PYTHON_ENV') == 'prod')):
            return Response(UserSerializer(User.objects.filter(is_staff=False), many=True).data)
        else:
            return Response(UserSerializer(User.objects.all(), many=True).data)


class UserViewId(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, description="user email"),
            "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="user is active"),
            "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="user first name"),
            "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="new password"),
            "roles": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER), description="list of role ids"),
            "avatar": openapi.Schema(type=openapi.TYPE_STRING, description="link avatar"),
            "country": openapi.Schema(type=openapi.TYPE_INTEGER, description="country id"),
            "personal_phone": openapi.Schema(type=openapi.TYPE_STRING, description="user personal telephone"),
            "work_phone": openapi.Schema(type=openapi.TYPE_STRING, description="user work phone"),
            "team_leader": openapi.Schema(type=openapi.TYPE_INTEGER, description="user leader  id", default=None),
            "company": openapi.Schema(type=openapi.TYPE_INTEGER, description="company id", default=None),
            "department": openapi.Schema(type=openapi.TYPE_INTEGER, description="department id", default=None),
            "job_position": openapi.Schema(type=openapi.TYPE_INTEGER, description="job_position id", default=None)
        }
    ))
    def patch(self, request, id: int) -> Response:
        """
        update user
        """
        company = Company.objects.get(pk=request.data['company'])
        country = Country.objects.get(pk=request.data['country'])
        try:
            user = User.objects.get(pk=id)
        except User.DoesNotExist:
            return HttpResponseNotFound(f"User not exist")

        if (request.data['team_leader'] != None):
            leader = User.objects.get(pk=request.data['team_leader'])
            try:
                team_leader = TeamLeader.objects.get(team_member=user)
                team_leader.team_leader = leader
                team_leader.save()
            except TeamLeader.DoesNotExist:
                return HttpResponseNotFound(f"Team Leader not exist")

        user.email = request.data["email"]
        user.is_active = request.data["is_active"]
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        user.avatar = request.data["avatar"]
        user.country = country
        user.personal_phone = request.data["personal_phone"]
        user.work_phone = request.data["work_phone"]
        user.company = company
        if (request.data["department"] != None):
            department = Department.objects.get(pk=request.data["department"])
            user.department = department
        if (request.data["job_position"] != None):
            job_position = JobPosition.objects.get(
                pk=request.data["job_position"])
            user.job_position = job_position
        # verification of existing roles
        [Role.objects.get(pk=x) for x in request.data["roles"]]
        user.save()

        user.roles.set(request.data["roles"])
        return Response(UserSerializer(user).data)


@permission_classes([AllowAny])
class UserChangePasswordEmailView(APIView):
    # add serializer
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, default="test@cheil.com", description="(string) user email"),
        }
    ))
    def post(self, request: HttpRequest) -> Response:
        """
        sent email to a user to change password
        """
        user = User.objects.get(email=request.data["email"])
        code = PasswordChangeCode(user=user)
        code.generate_random_code()
        code.set_expiration_date()

        code.save()
        result = send_mail("Password Recovery", email_change_credentials.format(
            password_change_code=code.code,
            environmentValue=os.environ.get(
                'FRONTEND_HOST', 'http://localhost:4200')
        ), user.email)

        if result:
            return Response({
                "detail": "email sent succesfully"
            })
        else:
            Response({
                "detail": "an error occured"
            })


@permission_classes([AllowAny])
class UserChangePasswordView(APIView):
    # add serializer

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, description="user email"),
            "code": openapi.Schema(type=openapi.TYPE_INTEGER, description="(int) password change validation code"),
            "password": openapi.Schema(type=openapi.TYPE_STRING, description="(int) new password"),
        }
    ))
    def post(self, request: HttpRequest) -> Response:
        """
        change password of a user if code and expiration dates are valid
        """
        email = request.data["email"]
        code = request.data["code"]
        user = User.objects.get(email=email)
        query = PasswordChangeCode.objects.filter(Q(expiration__gte=datetime.now()) & Q(
            code__exact=code) & (Q(user__exact=user.id)))

        if len(query) == 0:
            return JsonResponse({
                "detail": "either the code or the user does not exist. Verify the code is not expired."
            }, status=406)
        code = query[0]
        if code.used:
            return JsonResponse({
                "detail": "this code was already used"
            }, status=401)

        if not code.used:
            code: PasswordChangeCode = query[0]
            user.set_password(request.data["password"])
            user.save()
            code.used = True
            code.save()

        return Response({
            "detail": "user password changed succesfully"
        })


class UserChangePasswordV2View(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "password": openapi.Schema(type=openapi.TYPE_STRING, description="(int) new password"),
        }
    ))
    def post(self, request: HttpRequest, id: int) -> Response:
        """
        change password of a user
        """
        user = User.objects.get(id=id)
        user.set_password(request.data["password"])
        user.save()

        return Response({
            "detail": f"user ({user.email}) password changed succesfully"
        })


class RoleView(APIView):
    def get(self, request) -> Response:
        """
        Get all roles data
        """
        roles = Role.objects.all().order_by("role_name")
        serializer = RolesSerializer(roles, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "role_name": openapi.Schema(type=openapi.TYPE_STRING, description="(string) Role Name"),
            "status": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="(boolean) Status"),
            "countries": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) Country IDs"),
            "accounts": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) Account IDs"),
            "views": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) View IDs"),
            "divisions": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) Division IDs"),
        }
    ))
    def post(self, request) -> Response:
        """
        Create role
        """
        countries = Country.objects.filter(id__in=request.data['countries'])
        accounts = Account.objects.filter(id__in=request.data['accounts'])
        views = View.objects.filter(id__in=request.data['views'])
        division = Division.objects.filter(id__in=request.data['divisions'])

        try:
            role = Role.objects.create(
                role_name=request.data['role_name'], status=request.data['status'])
            for country in countries:
                role.countries.add(country)
            for account in accounts:
                role.accounts.add(account)
            for view in views:
                role.views.add(view)
            for d in division:
                role.divisions.add(d)
            serializer = RoleSerializer(role)
        except Exception as ex:
            return HttpResponseBadRequest(str(ex))

        return Response(serializer.data, status=201)


class RoleViewId(APIView):
    """
    Role service with specific Id
    """

    def get(self, request, id: int) -> Response:
        """
        <h3>Get role by id</h3>
        <hr>
        <p>this endpoint needs the role id as a parameter, and returns as a response an object with the role information, inside the object</p>
        """
        roles = Role.objects.filter(id=id).get()
        serializer = RoleSerializer(roles)
        return Response(serializer.data)

    def delete(self, request, id: int) -> Response:
        role = Role.objects.filter(id=id).get()
        serializer = RoleSerializer(role)
        Role.objects.filter(id=id).delete()
        return Response(serializer.data, status=204)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "role_name": openapi.Schema(type=openapi.TYPE_STRING, description="(string) Role Name"),
            "status": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="(boolean) Status"),
            "countries": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) Country IDs"),
            "accounts": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) Account IDs"),
            "views": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) View IDs"),
            "divisions": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER), description="(ARRAY) Division IDs"),
        }
    ))
    def patch(self, request, id: int) -> Response:

        role = Role.objects.filter(id=id)
        role_name, role_status = role.get().role_name, role.get().status
        role.update(role_name=request.data.get(
            'role_name', role_name), status=request.data.get('status', role_status))

        role = role.get()

        try:
            if request.data['countries'] != None:
                countries = Country.objects.filter(
                    id__in=request.data['countries'])
                role.countries.clear()
                for country in countries:
                    role.countries.add(country)
            if request.data['accounts'] != None:
                accounts = Account.objects.filter(
                    id__in=request.data['accounts'])
                role.accounts.clear()
                for account in accounts:
                    role.accounts.add(account)
            if request.data['views'] != None:
                views = View.objects.filter(
                    id__in=request.data['views'])
                role.views.clear()
                for view in views:
                    role.views.add(view)
            if request.data['divisions'] != None:
                divisions = Division.objects.filter(
                    id__in=request.data['divisions'])
                role.divisions.clear()
                for d in divisions:
                    role.divisions.add(d)

            serializer = RoleSerializer(role)
        except Exception as ex:
            return HttpResponseBadRequest(str(ex))

        return Response(serializer.data, status=201)


class ActionLogPost(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "view": openapi.Schema(type=openapi.TYPE_NUMBER, description="(number) View id", default="default"),
        }
    ))
    def post(self, request):
        # user
        try:
            user = User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            return HttpResponseNotFound(f"User does not exist")

        request.data['user'] = user
        # view
        try:
            view = View.objects.get(id=request.data['view'])
        except View.DoesNotExist:
            return HttpResponseNotFound(f"View does not exist")

        request.data['view'] = view
        # country
        try:
            country = Country.objects.get(
                id=user.country_id) if user.country_id != None else Country.objects.get(id=1)
        except Country.DoesNotExist:
            return HttpResponseNotFound(f"Country does not exist")

        request.data['country'] = country
        request.data['last_login'] = user.last_login
        # userrole
        try:
            user_role = Role.objects.filter(user__id=user.id)
        except Role.DoesNotExist:
            return HttpResponseNotFound(f"User role does not exist")
        # roles
        roles_concat = ""
        divisions_concat = ""
        accounts_concat = ""
        role_divisions_list = []
        role_accounts_list = []
        for role in user_role:
            roles_concat = f"{role.id}" if user_role[0] == role else f"{roles_concat},{role.id}"
            role_division = role.divisions.all()
            role_divisions_list.append(role_division)
            role_accounts = role.accounts.all()
            role_accounts_list.append(role_accounts)

        # divisions
        count = 0
        for divisions in role_divisions_list:
            count += 1
            for division in divisions:
                divisions_concat = f"{division.id},{divisions_concat}"
            if len(role_divisions_list) == count:
                divisions_concat = divisions_concat[:-1]

        # accounts
        count = 0
        for accounts in role_accounts_list:
            count += 1
            for account in accounts:
                accounts_concat = f"{account.id},{accounts_concat}"
            if len(role_accounts_list) == count:
                accounts_concat = accounts_concat[:-1]

        request.data['roles'] = roles_concat
        request.data['divisions'] = divisions_concat
        request.data['accounts'] = accounts_concat

        # viewlog
        try:
            viewLog = ViewsLog.objects.create(**request.data)
            serializer = ViewLogsSerializer(viewLog)
        except Exception as ex:
            return HttpResponseBadRequest(str(ex))

        return Response(serializer.data)


class ActionLogView(APIView):
    def get(self, request, group) -> Response:
        """
        Get all action log data
        """

        # get groups
        compound_groups = re.findall("groups:(.+)", group)
        if compound_groups:
            groups = compound_groups[0].split("$")
        else:
            groups = [group]

        action = get_action_logs_data(request.all_filters)

        action = action[groups]
        action["count"] = 1

        return Response(action, headers={
            "agg": {"count": "count"},
            "groups": ",".join(groups),
        })


class UserStatusLogView(APIView):
    def get(self, request, group) -> Response:
        """
        get users log data
        """
        compound_groups = re.findall("groups:(.+)", group)
        if compound_groups:
            groups = compound_groups[0].split("$")
        else:
            groups = [group]

        action = get_user_status_log_data(request.all_filters)

        action = action[groups]
        action["count"] = 1

        return Response(action, headers={
            "agg": {"count": "count"},
            "groups": ",".join(groups),
        })


class FilterByView(APIView):
    def get(self, request) -> Response:
        """
        Get all action log data
        """
        if (os.environ.get('PYTHON_ENV') == "prod"):
            action = FilterBy.objects.filter(view_log__user__is_staff=False)
        else:
            action = FilterBy.objects.all()
        serializer = FilterBySerializer(action, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "filter": openapi.Schema(type=openapi.TYPE_STRING, description="(string) filter name"),
            "value": openapi.Schema(type=openapi.TYPE_NUMBER, description="(Number) value number filtering"),
            "view_log": openapi.Schema(type=openapi.TYPE_NUMBER, description="(number) View log id"),
        }
    ))
    def post(self, request):
        try:
            view_log = ViewsLog.objects.get(id=request.data['view_log'])
        except ViewsLog.DoesNotExist:
            return HttpResponseNotFound(f"View log does not exist")

        request.data['view_log'] = view_log

        try:
            filter = Filter.objects.get(name=request.data['filter'])
        except Filter.DoesNotExist:
            filter = Filter.objects.create(name=request.data['filter'])

        request.data['filter'] = filter

        try:
            value = Value.objects.get(value=request.data['value'])
        except Value.DoesNotExist:
            value = Value.objects.create(value=request.data['value'])

        request.data['value'] = value

        try:
            filterBy = FilterBy.objects.create(**request.data)
            serializer = FilterBySerializer(filterBy)
        except Exception as ex:
            return HttpResponseBadRequest(str(ex))

        return Response(serializer.data)


class AuthorizedEmailDomainView(APIView):
    """
    Get all authorized emails
    """

    def get(self, request) -> Response:
        emails = AuthorizedEmailDomain.objects.all()
        serializer = Authorized_EmailsSerializer(emails, many=True)
        return Response(serializer.data)


class CompanyView(APIView):
    """
    Get all companies
    """

    def get(self, request) -> Response:
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)


class DepartmentView(APIView):
    """
    Get all departments
    """

    def get(self, request) -> Response:
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)


class JobPositionView(APIView):
    """
    Get all job positions
    """

    def get(self, request) -> Response:
        jobs = JobPosition.objects.all()
        serializer = JobPositionSerializer(jobs, many=True)
        return Response(serializer.data)


class TeamLeaderView(APIView):
    """
    Get all team leaders
    """

    def get(self, request) -> Response:
        leaders = TeamLeader.objects.all()
        serializer = TeamLeaderSerializer(leaders, many=True)
        return Response(serializer.data)


def get_total_by(data, groups, now, visits=False):
    by = groups[0]
    group_by = data[groups]
    group_by = group_by[group_by[by] == now]
    group_by['count'] = 1
    group_by = group_by.groupby(groups).agg({'count': 'count'}).reset_index()
    if (visits & (len(group_by) > 0)):
        group_by = group_by['count'][0]
    else:
        group_by = len(group_by)
    return group_by


@api_view(['GET'])
def active_users(request):
    df_data = get_user_status_log_data(request.all_filters)
    df_data['count'] = 1

    # get uniques dates
    timezone = pytz.timezone('America/Panama')

    res_data = {}
    res_data['data'] = df_data.groupby(['week', 'year', 'status', 'user__id']).agg({
        'count': 'count'}).copy().reset_index().to_dict('records')

    today = df_data.groupby(['date', 'year', 'status', 'user__id']).agg(
        {'count': 'count'}).copy().reset_index()
    today['date'] = today['date'].astype(str)

    res_data['today'] = len(today[today['date'] == (
        (datetime.now(timezone)+timedelta(days=-1)).strftime('%Y-%m-%d'))].reset_index())

    week = df_data.groupby(
        ['week', 'year', 'status', 'user__id']).agg({'count': 'count'}).copy().reset_index()
    week['week'] = week['week'].astype(int)
    week_numm = len(week[week['week']
                    == datetime.now().isocalendar()[1]].reset_index())
    if (week_numm == 0):
        week_numm = len(week[week['week']
                             == (datetime.now().isocalendar()[1]-1)].reset_index())
    res_data['weekly'] = week_numm

    month = df_data.groupby(
        ['month', 'year', 'status', 'user__id']).agg({'count': 'count'}).copy().reset_index()
    month['month'] = month['month'].astype(int)
    month_numm = len(month[month['month']
                           == datetime.now().month].reset_index())
    if (month_numm == 0):
        month_numm = len(month[month['month']
                               == (datetime.now().month-1)].reset_index())
    res_data['monthly'] = month_numm

    del today
    del week
    del week_numm
    del month
    del month_numm

    return Response(res_data)


@api_view(['GET'])
def users_visits(request):
    df_data = get_action_logs_data(request.all_filters)

    data_users = get_user_status_log_data(request.all_filters)

    # get week and user__id to df
    df = df_data[['week', 'user__id', 'year']].drop_duplicates().copy()
    df['active'] = df['user__id']
    del df['user__id']
    df = df.groupby(['week', 'year']).agg({'active': 'count'}).reset_index()

    # get active today

    # convert to json
    res_data = {}
    res_data['data'] = df.to_dict('records')
    res_data['today'] = get_total_by(
        df_data, ['date', 'user__id'], datetime.now().date())
    res_data['weekly'] = get_total_by(
        df_data, ['week', 'user__id'], datetime.now().isocalendar()[1])
    res_data['monthly'] = get_total_by(
        df_data, ['month', 'user__id'], datetime.now().month)

    return Response(res_data)


@api_view(['GET'])
def view_report(request):
    df_data = get_action_logs_data(request.all_filters)

    df = df_data[['week', 'year']].copy()
    df['count'] = 1
    df = df.groupby(['week', 'year']).agg({'count': 'count'}).reset_index()

    res_data = {}
    res_data['data'] = df.to_dict('records')

    res_data['today'] = get_total_by(
        df_data, ['date'], datetime.now().date(), True)
    res_data['weekly'] = get_total_by(
        df_data, ['week'], datetime.now().isocalendar()[1], True)
    res_data['monthly'] = get_total_by(
        df_data, ['month'], datetime.now().month, True)

    return Response(res_data)


@api_view(['GET'])
def users_by_countries_count(request):
    df = get_action_logs_data(request.all_filters)

    # get week and user__id to df
    groups = ['week', 'user__id', 'year', 'user__country__name']
    df = df[groups]
    df['users'] = 1

    df = df.groupby(groups).agg({'users': 'count'}).reset_index()

    del df['user__id']
    groups.remove('user__id')
    return Response(df, headers={
        "agg": {"users": "count"},
        "groups": ",".join(groups),
    })


@api_view(['GET'])
def weekly_active_users(request):
    df = get_action_logs_data(request.all_filters)
    df = df[['week', 'year', "view_id"]]
    df = df.groupby(['week', 'year']).agg({'view_id': 'count'}).reset_index()
    df['visits'] = df['view_id']
    del df['view_id']
    return Response(json.loads(df.to_json(orient="records")))


"el response debe tener los usuarios nuevos en lo 30 ultimos dias de ViewsLog"


@api_view(['GET'])
def new_users(request):
    if ((os.environ.get('PYTHON_ENV') == 'prod')):
        users = User.objects.filter(date_joined__range=[datetime.now(
        ) - timedelta(days=30), datetime.now()], is_staff=False)
    else:
        users = User.objects.filter(
            date_joined__range=[datetime.now() - timedelta(days=30), datetime.now()])
    serializers = UserMetricSerializer(users, many=True)
    return Response(serializers.data)


@api_view(['GET'])
def average_active_time(request):

    df = get_action_logs_data(request.all_filters)
    # date formatted to string (YYYY-MM-DD)
    df['date'] = df['native_date'].astype(str)
    df['str'] = pd.to_datetime(df['date']).dt.date
    # count all existing logs per user and day
    df_agrupation = df.groupby(['user__id', 'str']).count()
    df_summary = pd.DataFrame(columns=['date', 'timeseries'])  # empty df

    for i in df_agrupation.index:

        primera = datetime.strptime((df.loc[(df['user__id'] == i[0]) & (
            df['str'] == i[1])]['date'].head(1).values[0]), "%Y-%m-%d %H:%M:%S.%f%z")
        ultimo = datetime.strptime((df.loc[(df['user__id'] == i[0]) & (
            df['str'] == i[1])]['date'].tail(1).values[0]), "%Y-%m-%d %H:%M:%S.%f%z")
        diferencia = ultimo - primera
        df_summary.loc[len(df_summary), df_summary.columns] = str(
            primera.date()), round(diferencia.seconds, 2)

    df_summary = df_summary.groupby('date').mean()
    df_summary["hours"] = (df_summary["timeseries"] / 3600).astype("int32")
    df_summary["minutes"] = (
        (df_summary.timeseries - df_summary["hours"] * 3600)/60).astype("int32")
    df_summary["seconds"] = (((df_summary.timeseries - df_summary["hours"]
                             * 3600) - df_summary["minutes"] * 60)).astype("int32")
    df_summary["labels"] = df_summary.hours.astype("str").map('{:0>2}'.format)+":"+df_summary.minutes.astype(
        "str").map('{:0>2}'.format)+":"+df_summary.seconds.astype("str").map('{:0>2}'.format)
    df_summary = df_summary.round(2)
    df_summary = df_summary.reset_index()

    return Response(json.loads(df_summary.to_json(orient='records')))


@api_view(['GET'])
def new_visits(request):
    if ((os.environ.get('PYTHON_ENV') == 'prod')):
        action = ViewsLog.objects.filter(Q(date__range=[datetime.now(
        ) - timedelta(days=30), datetime.now()])).filter(user__is_staff=False)
    else:
        action = ViewsLog.objects.filter(
            Q(date__range=[datetime.now() - timedelta(days=30), datetime.now()]))
    df = pd.DataFrame(action.values())

    df['date'] = pd.to_datetime(df['date'], unit='ms').dt.date
    users = df['user_id'].unique().copy()

    df_result = pd.DataFrame(columns=['user_id', 'date'])
    for i in range(len(users)):
        df_result.loc[len(df_result), df_result.columns] = users[i], df.loc[df['user_id']
                                                                            == users[i]]['date'].head(1).values[0]
    df_result = df_result.groupby('date').agg(
        {'user_id': 'count'}).reset_index()
    df_result['first'] = df_result['user_id']
    del df_result['user_id']
    df_result['week'] = pd.to_datetime(df_result['date']).dt.week
    df_result['year'] = pd.to_datetime(df_result['date']).dt.year
    del df_result['date']
    df_result = df_result.groupby(['week', 'year']).sum().reset_index()
    return Response(json.loads(df_result.to_json(orient='records')))


@api_view(['GET'])
def visits_table(request):
    users = get_user_status_log_data(request.all_filters)
    action = get_action_logs_data(request.all_filters)

    pl_users = pl.from_pandas(users)
    pl_action = pl.from_pandas(action)

    country = ((pl_users
                .filter(pl.col('year') == pl.col('year').max())
                .groupby(['country__name', 'user__id'])
                .agg([pl.count("country__name").alias("ytd_reg"),
                      pl.col('week').filter(pl.col('week') == pl.max(
                          'week')-3).count().cast(pl.Int64, strict=False).alias('first_last_week'),
                      pl.col('week').filter(pl.col('week') == pl.max(
                          'week') - 2).count().cast(pl.Int64, strict=False).alias('acc_users_first'),
                      pl.col('week').filter(pl.col('week') == pl.max(
                          'week') - 1).count().cast(pl.Int64, strict=False).alias('acc_users_second'),
                      pl.col('week').filter(pl.col('week') == pl.max('week')).count().cast(
                    pl.Int64, strict=False).alias('acc_users_third'),
                ])).groupby(['country__name'])
               .agg([pl.count(["ytd_reg", 'first_last_week', 'acc_users_first', 'acc_users_second', 'acc_users_third'])])
               .with_columns([
                   (((pl.col('ytd_reg')/pl.sum('ytd_reg')) * 100))
                   .alias("ytd_reg_pct"),
                   (pl.col('first_last_week') - pl.col('acc_users_first')
                    ).alias("acc_users_last_first"),
                   (pl.col('acc_users_first') - pl.col('acc_users_second')
                    ).alias("acc_users_last_second"),
                   (pl.col('acc_users_second') - pl.col('acc_users_third')
                    ).alias("acc_users_last_third"),
               ])
               .rename({'country__name': 'country'})
               .drop('first_last_week'))

    country_ac = ((pl_action
                   .with_column(pl.col('user__country__name').fill_null('default'))
                   .filter(pl.col('year') == pl.col('year').max())
                   .groupby(['user__country__name'])
                   .agg([
                       pl.col('week').filter(pl.col('week') == pl.max('week') -
                                             3).count().cast(pl.Int64, strict=False).alias('first_last_week'),
                       pl.col('week').filter(pl.col('week') == pl.max('week') -
                                             2).count().cast(pl.Int64, strict=False).alias('login_first'),
                       pl.col('week').filter(pl.col('week') == pl.max('week') -
                                             1).count().cast(pl.Int64, strict=False).alias('login_second'),
                       pl.col('week').filter(pl.col('week') == pl.max('week')
                                             ).count().cast(pl.Int64, strict=False).alias('login_third'),
                   ]))
                  .with_columns([
                      (pl.col('first_last_week') -
                       pl.col('login_first')).alias("login_last_first"),
                      (pl.col('login_first') -
                       pl.col('login_second')).alias("login_last_second"),
                      (pl.col('login_second') -
                       pl.col('login_third')).alias("login_last_third"),
                  ])
                  .rename({'user__country__name': 'country'})
                  .drop('first_last_week')
                  .join(country, on='country', how='outer')

                  .sort('ytd_reg', reverse=True))
    weeks = (pl_users
             .select([((pl.col('year'))
                       + 'W' +
                       pl.col('week')).alias('year_weeks')]).unique().sort('year_weeks').tail(3))
    response = {
        'table': country_ac.to_dicts(),
        'weeks': weeks.to_dicts()

    }
    return Response(response)


@api_view(['POST'])
def save_photo_user(request):
    print(request)
    ''' save file in s3 the request resive like this {file_name:'', file_type:'',file_value:'' } '''
    file_name = request.data['file_name']
    file_value = request.data['file_value']
    file_type = file_name.split('.')[-1]
    # save file in local
    with open(file_name, "wb") as fh:
        fh.write(base64.b64decode(file_value))
    # reanme file saved a sha256
    old, new = sha256(file_name)
    new = new + '.'+file_type
    os.rename(old, new)

    # se sube a la nube el fichero
    s3_bucket_name = 'lrm-public'
    key_name = 'profile_pictures/'+new

    with open(new, 'rb') as data:
        s3.upload_fileobj(data, s3_bucket_name, key_name)

    # res = s3.generate_presigned_url(
    #    "get_object", Params={'Bucket': s3_bucket_name, 'Key': key_name})

    # se borra el fichero local
    os.remove(new)

    # colocar res como imagen de usuario en UserModel avatar
    # user = User.objects.get(id=request.data['user_id'])
    # user.avatar = res
    # user.save()
    return Response({'url': f"https://lrm-public.s3.amazonaws.com/profile_pictures/{new}"})


@api_view(['GET'])
def get_users_logs_by_country(request):
    users = get_user_status_log_data(request.all_filters)

    timezone = pytz.timezone('America/Panama')

    pl_users = (pl.from_pandas(users)
                .filter(pl.col('date') == ((datetime.now(timezone)+timedelta(days=-1)).strftime('%Y-%m-%d')))
                .with_column(pl.lit(1).alias('count'))
                .groupby(['status', 'country__name'])
                .agg([pl.col('count').sum()]))
    return Response(pl_users.to_dicts())


@api_view(['POST'])
def share_otp(request):
    view_sh = ViewSharingAcc.objects.get(view__name=request.data['view_name'])
    user = User.objects.get(id=view_sh.user_id)
    code = user.generate_otp()

    token = TokenObtainPairSerializer().validate({
        "email": user.email,
        "password": str(code)
    })["access"]

    return Response({'code': token})
