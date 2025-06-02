from rest_framework import status
from algorithms.middleware.accessor import ResourceAccessorV2
from models.models import Location
from modules.constants import *
from modules.logger import logger


class MiddleWare:

    @staticmethod
    def middleware_v2(request_data, *args, **kwargs):
        logger.debug("Hit on Version-2 Middleware.")
        mode_to_reach, mode_for_transit = request_data.get('mode')
        resource_key = f"{mode_to_reach}_{mode_for_transit}"
        transit_mode = ResourceAccessorV2(resource_key).get_resource_by_mode(request_data)
        # src = Location(location_value=[28.543938, 77.2690394], location_type=PLACE_TYPE_ENUM,
        #                location_name='IIIT-Delhi R&D Building')
        # request_data['src'] = src

        available_routes = transit_mode.get_response(request_data)

        if not available_routes:
            response = {
                'message': 'Failure',
                'version': 'v2',
                'description': 'No routes available',
                'data': []
            }
            return response, status.HTTP_400_BAD_REQUEST
        else:
            response = {
                'message': 'Success',
                'version': 'v2',
                'description': 'Route found',
                'data': available_routes
            }
            return response, status.HTTP_200_OK

    @staticmethod
    def get_stops_v2(request_data, *args, **kwargs):
        logger.error("Request method is not GET.")

        mode = request_data.get('mode')
        resource_key = f"{WALK_ENUM}_{mode}"
        transit_mode = ResourceAccessorV2(resource_key).get_resource_by_mode()
        stops_list = transit_mode.get_stops_json()

        if not stops_list:
            response = {
                'message': 'Failure',
                'version': 'v2',
                'description': 'No stops found',
                'data': []
            }
            return response, status.HTTP_400_BAD_REQUEST
        else:
            response = {
                'message': 'Success',
                'version': 'v2',
                'description': 'Stops found',
                'data': stops_list
            }
            return response, status.HTTP_200_OK
