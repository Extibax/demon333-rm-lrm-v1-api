from django.db import models

from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import make_password
import pytz
from api.settings import ddb, SIMPLE_JWT
from datetime import datetime, timedelta
from random import random
from .managers import UserManager


# LRM MODELS
from locations.models import Country
from store.models import PointOfSale
from views.models import View
from store.models import Account
from product.models import Division
from django.contrib.auth.hashers import (
    check_password,
)
from dynamodb_json import json_util as ddb_json


class Role(models.Model):
    role_name = models.CharField(
        max_length=30, blank=False, null=False, unique=True)
    status = models.BooleanField(default=False)
    countries = models.ManyToManyField(Country)
    views = models.ManyToManyField(View)
    accounts = models.ManyToManyField(Account)
    divisions = models.ManyToManyField(Division)
    point_of_sales = models.ManyToManyField(PointOfSale)

    def __str__(self) -> str:
        return f"{self.role_name} ({self.id})"


class AuthorizedEmailDomain(models.Model):
    value = models.TextField(max_length=100, null=False)

    def __str__(self):
        return f"@{self.value}"


class Company(models.Model):
    value = models.TextField(max_length=50, null=False)

    def __str__(self):
        return f"{self.value}"


class Department(models.Model):
    value = models.TextField(max_length=50, null=False)

    def __str__(self):
        return f"{self.value}"


class JobPosition(models.Model):
    value = models.TextField(max_length=50, null=False)

    def __str__(self):
        return f"{self.value[:9]}..."


class User(AbstractBaseUser, PermissionsMixin):
    """User custom model"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    roles = models.ManyToManyField(Role)
    country = models.ForeignKey(
        Country, related_name='user', on_delete=models.DO_NOTHING, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    avatar = models.CharField(max_length=250, blank=True)
    is_staff = models.BooleanField(default=False)
    is_dev = models.BooleanField(default=False)
    otp = models.TextField(max_length=128, default=None, null=True)
    personal_phone = models.TextField(max_length=30, default=None, null=True)
    work_phone = models.TextField(max_length=30, default=None, null=True)
    company = models.ForeignKey(
        Company, related_name='user', on_delete=models.DO_NOTHING, blank=True, null=True)
    department = models.ForeignKey(
        Department, related_name='user', on_delete=models.DO_NOTHING, blank=True, null=True)
    job_position = models.ForeignKey(
        JobPosition, related_name='user', on_delete=models.DO_NOTHING, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def hidden_name(self):
        name = self.first_name + " " + self.last_name
        return name.replace(name[3:-3], "*"*(len(name)-6))

    def check_password(self, raw_password):
        # or check_password(raw_password, self.otp, setter)
        def setter(raw_password):
            self.set_password(raw_password)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["password"])

        #year,month,day = datetime.now().year,datetime.now().month,datetime.now().day
        #SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]=datetime(year=year, month=month,day=day+1,minute=0,second=0)-datetime.now()

        # print(SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"])
        validation = super().check_password(raw_password) or check_password(
            raw_password, self.otp if self.otp else "", setter)

        self.last_login = datetime.now(pytz.timezone("UTC"))
        self.save()

        return validation

    def generate_otp(self):
        otp = str(random())[2:8]
        self.otp = make_password(otp)
        self.save()
        return otp

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    # get user active by last login, if last login is more than 1 month, user is LOW, and if last login is more than 3 month, user is inactive

    def __get_user_active(self):
        if self.is_active == False:
            return "DISABLED"
        if self.last_login:
            if datetime.now(pytz.timezone("UTC")) - self.last_login > timedelta(days=30):
                return "LOW"
            elif datetime.now(pytz.timezone("UTC")) - self.last_login > timedelta(days=90):
                return "INACTIVE"
            else:
                return "ACTIVE"
        else:
            return "ACTIVE"
        # self.save()
        # return self.active_status

    def inactivity_status(self):
        return self.__get_user_active()

    def jobposition(self):
        return self.job_position.value if self.job_position else "-"

    def department_name(self):
        return self.department.value if self.department else "-"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class TeamLeader(models.Model):
    team_member = models.OneToOneField(
        User, related_name='teammember', on_delete=models.CASCADE)
    team_leader = models.ForeignKey(
        User, related_name='teamleader', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.team_leader}->{self.team_member}"


class Session(models.Model):
    user = models.ForeignKey(User, related_name='user',
                             on_delete=models.DO_NOTHING)
    date_started = models.DateTimeField(auto_now_add=True)


class ViewsLog(models.Model):
    user = models.ForeignKey(User, related_name='log',
                             on_delete=models.DO_NOTHING)
    date = models.DateTimeField(auto_now_add=True)
    view = models.ForeignKey(View, related_name='log',
                             on_delete=models.DO_NOTHING)
    country = models.ForeignKey(
        Country, related_name='log', on_delete=models.DO_NOTHING, blank=True, null=True)
    last_login = models.DateTimeField(null=True)
    roles = models.TextField(max_length=255, default=None, null=True)
    divisions = models.TextField(max_length=255, default=None, null=True)
    accounts = models.TextField(max_length=255, default=None, null=True)

    def __str__(self):
        return f"{self.id}"


class UserStatusLog(models.Model):
    ''' properties: user, status last_login, country '''
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, related_name='user_log', on_delete=models.CASCADE)
    status = models.CharField(max_length=100, blank=False, null=False)
    last_login = models.DateTimeField(null=True)
    country = models.ForeignKey(
        Country, related_name='user_log', on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return f"{self.id}"


class Filter(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class Value(models.Model):
    value = models.IntegerField()

    def __str__(self):
        return f"{self.value}"


class FilterBy(models.Model):
    view_log = models.ForeignKey(ViewsLog, on_delete=models.DO_NOTHING)
    filter = models.ForeignKey(Filter, on_delete=models.DO_NOTHING)
    value = models.ForeignKey(Value, on_delete=models.DO_NOTHING)


class CacheBatchJob(models.Model):
    endpoint = models.CharField(max_length=200, blank=True)
    job_id = models.CharField(max_length=36, blank=True)
    query = models.CharField(max_length=250, blank=True)
    #cache_key = models.CharField(max_length=250, blank=True)
    started = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField()
    failed = models.BooleanField(default=False)
    result = models.CharField(max_length=200, blank=True)
    #ip = models.CharField(max_length=15, default="000.000.000.000", blank=True)


class PasswordChangeCode(models.Model):
    user = models.ForeignKey(User, related_name='password_change_code',
                             on_delete=models.DO_NOTHING)
    code = models.PositiveIntegerField(null=False)
    used = models.BooleanField(default=False)
    expiration = models.DateTimeField()

    def generate_random_code(self):
        self.code = int(round(random()*1000000, 0))
        return self.code

    def set_expiration_date(self):
        self.expiration = datetime.now()+timedelta(hours=1)
        return self.expiration


class ViewSharingAcc(models.Model):
    view = models.ForeignKey(
        View, related_name='view_sharing_acc', on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, related_name='view_sharing_acc', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}"


class CacheProcessItem():
    table_name: str = 'cache-layer-1-progress'

    @classmethod
    def get(cls, page=1):
        response = ddb_json.loads(ddb.query(
            TableName=cls.table_name,
            # IndexName='string',
            Select='ALL_ATTRIBUTES',
            # Limit=123,
            # ConsistentRead=True|False,
            KeyConditionExpression="begins_with(SK,:sortKey) and PK = :primaryKey",

            #FilterExpression="batch_cache_enabled = :boolean",
            ExpressionAttributeValues={
                ":primaryKey": {"S": "cache-layer-1-item"},
                ":sortKey": {"S": "item"},
                # ":boolean":{"BOOL":True}
            },
        ))
        return response
