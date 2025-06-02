"""
Module to define the request serializers for the directions API.
"""

import ast
from datetime import datetime

from rest_framework import serializers

from models.models import Location
from modules.constants import *
from modules.constants import STOP_TYPE_CHOICES, REACHING_CHOICES, TRANSIT_CHOICES
from modules.logger import logger


class TimeField(serializers.CharField):
    """
    Custom field to parse time in HH:MM:SS format and convert it from 12-hour to 24-hour format.
    """

    def to_internal_value(self, data: str) -> str:
        """
        Method to parse the time in HH:MM:SS format and convert it from 12-hour to 24-hour format.
        Args:
            data: The time data to parse.
        Returns:
            The parsed time in 24-hour format.
        """
        # Remove all spaces from the input
        standardized_data = ''.join(data.split())

        # First, try parsing time in 12-hour format, then in 24-hour format if the first fails
        formats = [('%I:%M:%S %p', True), ('%H:%M:%S', False)]  # Pair format with whether it's 12-hour
        for time_format, is_twelve_hour in formats:
            try:
                parsed_time = datetime.strptime(standardized_data, time_format)
                # If it's in 12-hour format, convert to 24-hour format
                if is_twelve_hour:
                    return parsed_time.strftime('%H:%M:%S')
                return standardized_data  # Already in 24-hour format
            except ValueError:
                continue  # Try the next format

        # If neither format is correct, raise a validation error
        raise serializers.ValidationError("Time must be in the format HH:MM:SS or HH:MM:SS AM/PM.")


class LocationField(serializers.CharField):
    """
    Custom field to validate location based on the type of location provided (place, metro, bus).
    """

    def __init__(self, location_type_field: str, location_name: str, field_name: str, **kwargs):
        """
        Method to initialize the LocationField object.
        Args:
            location_type_field: The field name in the parent serializer that contains the location type.
            location_name: The name of the location.
            field_name: The name of the field (source (i.e. src) or destination (i.e. dst)).
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.location_type_field = location_type_field
        self.field_name = field_name
        self.location_name = location_name

    def to_internal_value(self, data) -> Location:
        """
        Method to validate the location based on its type.
        Args:
            data: The location data to validate.
        Returns:
            The validated location as a Location object.
        """
        data = super().to_internal_value(data)  # Get the original string value
        # Retrieve the location type from the parent serializer's validated data
        location_type = self.parent.initial_data.get(self.location_type_field)
        location_name_value = self.parent.initial_data.get(self.location_name)
        if self.field_name is SRC:
            location_name_value = location_name_value if location_name_value else 'Your location'
        elif self.field_name is DST:
            location_name_value = location_name_value if location_name_value else 'Destination'
        else:
            location_name_value = location_name_value

        # Validate the location type (ensure it's a transit type, not a place)
        if location_type not in [METRO_TYPE_ENUM, BUS_TYPE_ENUM, NCRTC_TYPE_ENUM]:
            raise serializers.ValidationError(
                f"Only transit stops are supported. Invalid {self.field_name} type: {location_type}")

        # Validate the location value (must be an integer stop ID for transit)
        try:
            # Check if data is list format (which would indicate coordinates, not allowed)
            if isinstance(data, str) and ('[' in data or ',' in data):
                raise serializers.ValidationError(
                    f"Coordinates are not supported. Please provide a valid transit stop ID.")

            # Parse the data value
            data = ast.literal_eval(data) if isinstance(data, str) else data

            # Convert to integer if provided as a list with one element or as a string
            if isinstance(data, list):
                if len(data) != 1:
                    raise serializers.ValidationError(
                        f"Invalid {self.field_name} format. Please provide a single transit stop ID.")
                data = data[0]
            if isinstance(data, str):
                data = int(data)

            # Final check - must be an integer
            if not isinstance(data, int):
                raise serializers.ValidationError(
                    f"Invalid {self.field_name} value. Transit stop IDs must be integers.")

            return Location(location_value=data, location_type=location_type, location_name=location_name_value)

        except (ValueError, SyntaxError) as e:
            print(e)
            logger.error(f"Error: {e}: Invalid {self.field_name} coordinates: {data}")
            raise serializers.ValidationError(f"Invalid {self.location_type_field} coordinates.")

        except serializers.ValidationError as e:
            raise e  # Reraise the caught validation error


class ModeField(serializers.CharField):
    """
    Custom field to validate mode
    """

    def __init__(self, transit_choices, reaching_choices: list, **kwargs):
        super().__init__(**kwargs)
        self.reaching_choices = reaching_choices
        self.transit_choices = transit_choices

    def to_internal_value(self, data) -> list:
        mode = super().to_internal_value(data)

        # Check if mode contains any non-supported types (PTX, AUTO, BIKE, etc.)
        if all(m not in mode for m in TRANSIT_CHOICES):
            logger.warning(f"Non-transit mode requested: {mode}")
            raise serializers.ValidationError("Only transit-based modes are supported (bus, metro, multi, ncrtc)")

        # Default to walk as the mode to reach transit
        mode1 = WALK_ENUM

        # Extract the transit mode
        _filtered_mode = sorted(mode.strip().split(','))
        _filtered_mode = "".join(_filtered_mode).strip()
        mode2 = ''.join(filter(str.isalpha, _filtered_mode))

        # Validate that the transit mode is supported
        if mode2 not in self.transit_choices:
            raise serializers.ValidationError(f"Transit mode '{mode2}' is not supported.")

        return [mode1, mode2]


class MultiModalSerializer(serializers.Serializer):
    """
    Serializer class to validate the request parameters for the multimodal API.
    """
    src = LocationField(
        location_type_field=SRC_TYPE, location_name=SRC_NAME, field_name=SRC, required=True, max_length=500
    )
    dst = LocationField(
        location_type_field=DST_TYPE, location_name=DST_NAME, field_name=DST, required=True, max_length=500
    )
    src_type = serializers.ChoiceField(choices=STOP_TYPE_CHOICES, required=True)
    dst_type = serializers.ChoiceField(choices=STOP_TYPE_CHOICES, required=True)

    time = TimeField(max_length=11, default=datetime.now().time().strftime("%H:%M:%S"))
    mode = ModeField(
        transit_choices=TRANSIT_CHOICES,
        reaching_choices=REACHING_CHOICES,
        required=False, default=[WALK_ENUM, MULTI_ENUM]
    )
    max_fare = serializers.IntegerField(min_value=1, max_value=500, default=500, required=False)

    src_name = serializers.CharField(required=False, default='Your location')
    dst_name = serializers.CharField(required=False, default='Destination')

    # uncomment the following line to test the serializer.
    request_type = serializers.CharField(required=False, default='')

    # Parameters validators
    @staticmethod
    def validate_src_type(value: str) -> str:
        """
        Method to validate the source type.
        Args:
            value: The source type to validate.
        Returns:
            The validated source type.
        """
        if value not in STOP_TYPE_CHOICES:
            raise serializers.ValidationError("Invalid source type.")
        return value

    @staticmethod
    def validate_dst_type(value: str) -> str:
        """
        Method to validate the destination type.
        Args:
            value: The destination type to validate.
        Returns:
            The validated destination type.
        """
        if value not in STOP_TYPE_CHOICES:
            raise serializers.ValidationError("Invalid destination type.")
        return value

    def validate(self, attrs):
        src = attrs.get('src')
        dst = attrs.get('dst')

        if src.location_type == dst.location_type:
            if src.location_value == dst.location_value:
                raise serializers.ValidationError("Duplicate destination.")
        return attrs

    def __str__(self):
        """
        Method to return the string representation of the MultiModalSerializer object.
        """
        return f"MultiModalSerializer(src={self.src}, dst={self.dst}, src_type={self.src_type}, " \
               f"dst_type={self.dst_type}, time={self.time}, mode={self.mode})"
