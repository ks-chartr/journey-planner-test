"""
This file contains the views for the API.
"""

from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response

from modules.decorators import check_api_key_decorator
from serializers.request_serializers import MultiModalSerializer
from serializers.stop_serializer import StopSerializer
from algorithms.middleware.core import MiddleWare
import time
from models.swagger_models import *
from modules.logger import logger


class Stops(APIView):
    serializer_class = StopSerializer

    @staticmethod
    def index(request):
        logger.debug("Hit on Index: Redirecting to Stops version-2.")
        return redirect('api:stops_v2')

    @extend_schema(
        request=StopSerializer,
        responses=None,
        parameters=[
            OpenApiParameter(
                name='mode',
                description='Mode',
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        name="bus",
                        value="bus",
                        summary="Bus Mode",
                        description="Retrieve stops for Bus Mode"
                    ),
                    OpenApiExample(
                        name="metro",
                        value="metro",
                        summary="Metro Mode",
                        description="Retrieve stops for Metro Mode"
                    ),
                    OpenApiExample(
                        name="multi",
                        value="multi",
                        summary="Multi Mode",
                        description="Retrieve stops for Metro and Bus Mode combined"
                    )
                ],
            ),
            OpenApiParameter(
                name='x-api-key',
                description='API Key for authentication',
                required=True,
                type=str,
                location=OpenApiParameter.HEADER
            )
        ]
    )
    @check_api_key_decorator()
    def get(self, request):
        logger.info(f"Requested URL: {request.get_full_path()}")

        if request.method != 'GET':
            logger.error("Request method is not GET.")
            content = {'ERROR': 'Only GET requests are allowed'}
            return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        stop_serializer = self.serializer_class(data=request.query_params)

        if not stop_serializer.is_valid():

            errors_dict = stop_serializer.errors
            logger.error(f"Invalid Arguments: {errors_dict}")

            error_string_list = []
            for key, value in errors_dict.items():
                error_string_list.append(f'{key}: {", ".join(value)}')

            error_string = ' | '.join(error_string_list)
            content = {
                'message': 'Failure.',
                'description': error_string,
                'stops': []
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        validated_data = stop_serializer.validated_data

        response, status_code = MiddleWare().get_stops_v2(validated_data)

        return Response(response, status=status_code)


class MultiModal(APIView):
    """
    This class contains the views for the MultiModal API.
    """
    serializer_class = MultiModalSerializer

    @staticmethod
    def index(request):
        """
        This function redirects the user to the version-2 of the Directions app.
        """
        logger.debug("Hit on MultiModal Index: Redirecting to MultiModal version-2.")
        return redirect('api:multi_v2')

    @extend_schema(
        request=MultiModalSerializer,
        responses=None,
        parameters=[
            mode_parameter, src_parameter, src_type_parameter, src_name_parameter,
            dst_parameter, dst_type_parameter, dst_name_parameter, time_parameter,
            OpenApiParameter(
                name='x-api-key',
                description='API Key for authentication',
                required=True,  # Set to False if the key is optional
                type=str,
                location=OpenApiParameter.HEADER
            )
        ],
    )
    @check_api_key_decorator()
    def get(self, request):
        """
        This function returns the response for the version-2 of the Directions app.
        Args:
            request: The request object.
        Returns:
            The response object.
        """
        logger.info(f"Requested URL: {request.get_full_path()}") # TODO: Don't accept place
        if request.method != 'GET':
            content = {'ERROR': 'Only GET requests are allowed'}
            return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        t1 = time.time()
        print("Request Initiated")
        multimodal_serializer = MultiModalSerializer(data=request.query_params)

        if not multimodal_serializer.is_valid():
            errors_dict = multimodal_serializer.errors

            error_string_list = []
            for key, value in errors_dict.items():
                error_string_list.append(f'{key}: {", ".join(value)}')

            error_string = ' | '.join(error_string_list)
            content = {
                'message': 'Failure.',
                'description': error_string,
                'possible_directions': []
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        validated_data = multimodal_serializer.validated_data

        logger.info(f"data validated: {time.time() - t1}")
        response, status_code = MiddleWare().middleware_v2(validated_data)
        logger.info(f"response generated: {time.time() - t1}")

        return Response(response, status=status_code)
