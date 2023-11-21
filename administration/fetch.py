

# get action_data logs data
from datetime import datetime, timedelta
import os
import pandas as pd
import pytz
from administration.models import UserStatusLog, ViewsLog

action_adapter = {
    "user__country": "user_country",
    "date": "from_date",
}

user_adapter = {
    "country": "user_country",
    "date": "from_date",
    "country__name": "countryName"
}


VIEWS_LOG_FIELDS = ["date", "view_id", "country_id", "last_login", "roles", "divisions", "accounts", "view__name", "user__id", "view__group1",
                    "user__first_name", "user__last_name", "user__country__name", "user__country__code", "user__last_login", "user__country"]

USER_STATUS_LOG_FIELD = ["date", "user__id", "status",
                         "last_login", "country__id", "country__code", "country__name", "user__country__name", "country"]


def get_action_logs_data(filters):
   # get data
    if ((os.environ.get('PYTHON_ENV') == 'prod')):
        action_data = pd.DataFrame(ViewsLog.objects.filter(
            user__is_staff=False).values(*VIEWS_LOG_FIELDS))
    else:
        action_data = pd.DataFrame(
            ViewsLog.objects.all().values(*VIEWS_LOG_FIELDS))

    action_data = action_data.rename(columns=action_adapter)

    action_data["to_date"] = action_data["from_date"]

    if filters != None:
        action_data = action_data.query(filters)
    action_data = action_data.rename(
        columns={v: k for k, v in action_adapter.items()})

    del action_data["to_date"]

    # inactity status by last login, if last login is more than 1 month, user is LOW, and if last login is more than 3 month, user is inactive
    action_data['inactivity_status'] = action_data['user__last_login'].apply(lambda x: 'LOW' if x < datetime.now(pytz.timezone(
        "UTC")) - timedelta(days=30) else 'INACTIVE' if x < datetime.now(pytz.timezone("UTC")) - timedelta(days=90) else 'ACTIVE')
    # clean data
    action_data['native_date'] = action_data['date']
    action_data['datetime'] = pd.to_datetime(
        action_data['date'])

    action_data["week"] = action_data["datetime"].dt.isocalendar().week
    action_data["day"] = action_data["datetime"].dt.day_name()
    action_data['hour'] = action_data['datetime'].dt.strftime('%H:00')
    action_data["date"] = action_data["datetime"].dt.date
    action_data["month"] = action_data["datetime"].dt.month
    action_data["year"] = action_data["datetime"].dt.year
    action_data = action_data[action_data["view__name"] != "default"]

    return action_data


def get_user_status_log_data(filters):
    if ((os.environ.get('PYTHON_ENV') == 'prod')):
        action_data = pd.DataFrame(UserStatusLog.objects.filter(
            user__is_staff=False).values(*USER_STATUS_LOG_FIELD))
    else:
        action_data = pd.DataFrame(
            UserStatusLog.objects.all().values(*USER_STATUS_LOG_FIELD))

    action_data = action_data.rename(columns=user_adapter)

    action_data["to_date"] = action_data["from_date"]

    if filters != None:
        action_data = action_data.query(filters)
    action_data = action_data.rename(
        columns={v: k for k, v in user_adapter.items()})

    del action_data["to_date"]

    action_data['native_date'] = action_data['date']
    action_data['datetime'] = pd.to_datetime(
        action_data['date'])

    action_data["week"] = action_data["datetime"].dt.isocalendar().week
    action_data["day"] = action_data["datetime"].dt.day_name()
    action_data['hour'] = action_data['datetime'].dt.strftime('%H:00')
    action_data["date"] = action_data["datetime"].dt.date
    action_data["month"] = action_data["datetime"].dt.month
    action_data["year"] = action_data["datetime"].dt.year

    return action_data
