import requests, os, json, time

class MSOConnectionError(Exception):
    """Exception raised for MSO errors."""
    pass

class MSO:
    hostname = os.environ.get("MSO_HOSTNAME", "")
    user = os.environ.get("MSO_USER", "")
    cred = os.environ.get("MSO_CRED", "")
    email = os.environ.get("MSO_EMAIL", "")
    
    @classmethod
    def auth(cls):
        retries = 5
        count = 0
        while retries > count:
            try:
                token = json.loads(requests.post(f"{cls.hostname}/v2/api/Auth/LoginWebAdmin", json={
                    "userName": cls.user,
                    "password": cls.cred,
                    "email": cls.email
                }).content.decode("utf-8"))["session"]["token"]
                count = retries
            except Exception as ex:
                time.sleep(5)
                count += 1
                if retries == count:
                    raise MSOConnectionError(f"Couldnt retrieve MSO API Token. {ex}")
        return token

    @classmethod
    def mso_requests(cls,path,service):
        retries = 5
        count = 0
        while retries > count:
            try:
                response = json.loads(requests.get(f"{cls.hostname}{path}", 
                            headers={f"Authorization": "Bearer "+ cls.auth()}).content.decode("utf-8"))
                count = retries
            except Exception as ex:
                time.sleep(5)
                count += 1
                if retries == count:
                    raise MSOConnectionError(f"Couldnt retrieve {service} information. {ex}")

        return response

    @classmethod
    def getSiteLocation(cls, site_id, service):
        service_group = {
            "SiteLocation": "GetSiteLocationRM",
            "GoldenZone": "GetGoldenZoneRM",
            "OneSamsung": "GetOneSamsungRM",
            "Samples": "GetSamplesRM",
            "Stretch": "GetStretchRM",
            "Tables": "GetTablesRM",
            "Display": "GetDisplayRM",
            "Tickets": "GetTicketSOS"
        }
        path = f"/v1/api/SiteLocations/{service_group[service]}/{site_id}"
        response = MSO.mso_requests(path, service)
        return response

        