from drf_yasg import openapi

manual_params = [
    openapi.Parameter('account', in_=openapi.IN_QUERY,
                      description='account (customer) integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('division', in_=openapi.IN_QUERY,
                      description='division integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('product_group', in_=openapi.IN_QUERY,
                      description='product group integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('country', in_=openapi.IN_QUERY,
                      description='country integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('store', in_=openapi.IN_QUERY,
                      description='store integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('region', in_=openapi.IN_QUERY,
                      description='region (geographic) integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('country_zone', in_=openapi.IN_QUERY,
                      description='Country Zone (geographic) integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('city', in_=openapi.IN_QUERY,
                      description='City integer id or ids separated by comma. Example: 1 or 1,2,3,4', type=openapi.TYPE_STRING, ),
    openapi.Parameter('year_start', in_=openapi.IN_QUERY,
                      description='NOT AVAILABLE on all requests. year start of request. example: 2020', type=openapi.TYPE_STRING, ),
    openapi.Parameter('year_end', in_=openapi.IN_QUERY,
                      description='NOT AVAILABLE on all requests. year end of request. example: 2022', type=openapi.TYPE_STRING, ),
    openapi.Parameter('week_start', in_=openapi.IN_QUERY,
                      description='NOT AVAILABLE on all requests. week start of request. example: 20', type=openapi.TYPE_STRING, ),
    openapi.Parameter('week_end', in_=openapi.IN_QUERY,
                      description='NOT AVAILABLE on all requests. week end of request. example: 32', type=openapi.TYPE_STRING, )
]
