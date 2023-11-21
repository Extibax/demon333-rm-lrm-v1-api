from datetime import datetime


def normalize_fields_from_list(response: list, new_fields: dict):
    if not type(response) == list:
        raise Exception(
            f"Response sent is of type {type(response)}. Should be list")
    for item in response:
        for old, new in new_fields.items():

            item[new] = item[old]
            del item[old]

    return response


def transform_to_week(year, week):
    return datetime.strptime(f"{year}-{week}-1", "%G-%V-%u")
