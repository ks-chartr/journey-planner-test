"""
Module to define the request serializers for the directions API.
"""

from rest_framework import serializers
from modules.logger import logger
from modules.constants import *


class StopSerializer(serializers.Serializer):
    """
    Serializer class to validate the request parameters for the multimodal API.
    """
    mode = serializers.ChoiceField(
        choices=[
            BUS_ENUM, METRO_ENUM, MULTI_ENUM, WALK_ENUM, NCRTC_ENUM
        ], required=False, default=MULTI_ENUM
    )
