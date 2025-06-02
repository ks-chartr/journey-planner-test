from drf_spectacular.utils import OpenApiParameter, OpenApiExample, OpenApiTypes
from datetime import datetime

import pytz

utc_time = datetime.utcnow()

# Convert to IST
ist_timezone = pytz.timezone('Asia/Kolkata')
ist_time = utc_time.astimezone(ist_timezone)

mode_parameter = OpenApiParameter(
    name='mode',
    description='Mode (only transit-based modes are supported)',
    required=True,
    type=OpenApiTypes.STR,
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
            name="ncrtc",
            value="ncrtc",
            summary="Ncrtc Mode",
            description="Retrieve stops for Ncrtc Mode"
        ),
        OpenApiExample(
            name="multi",
            value="multi",
            summary="Multi Mode",
            description="Retrieve stops for Metro and Bus Mode combined."
        )
    ],
)

src_type_parameter = OpenApiParameter(
    name='src_type',
    description='Source Type (only transit stops supported)',
    required=True,
    type=OpenApiTypes.STR,
    examples=[
        OpenApiExample(
            name="src_type",
            value="bus",
            summary="Bus Stop",
            description="Type to be selected in case of bus stop id."
        ),
        OpenApiExample(
            name="src_type",
            value="metro",
            summary="Metro Stop",
            description="Type to be selected in case of metro stop id."
        ),
        OpenApiExample(
            name="src_type",
            value="ncrtc",
            summary="NCRTC Stop",
            description="Type to be selected in case of NCRTC stop id."
        )
    ],
)

dst_type_parameter = OpenApiParameter(
    name='dst_type',
    description='Destination Type (only transit stops supported)',
    required=True,
    type=OpenApiTypes.STR,
    examples=[
        OpenApiExample(
            name="bus",
            value="bus",
            summary="Bus Stop",
            description="Type to be selected in case of bus stop id."
        ),
        OpenApiExample(
            name="metro",
            value="metro",
            summary="Metro Stop",
            description="Type to be selected in case of metro stop id."
        ),
        OpenApiExample(
            name="ncrtc",
            value="ncrtc",
            summary="NCRTC Stop",
            description="Type to be selected in case of NCRTC stop id."
        )
    ],
)

time_parameter = OpenApiParameter(
    name='time',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Datetime of travel in ISO format.',
    required=True,
    examples=[
        OpenApiExample(
            'Time Example',
            value=utc_time.astimezone(ist_timezone).strftime("%H:%M:%S"),
            summary='Current time'
        )
    ]
)

src_name_parameter = OpenApiParameter(
    name='src_name',
    description='Source Name',
    type=OpenApiTypes.STR,
)

dst_name_parameter = OpenApiParameter(
    name='dst_name',
    description='Destination Name',
    type=OpenApiTypes.STR,
)

src_parameter = OpenApiParameter(
    name='src',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description='Source transit stop ID',
    required=True,
    examples=[
        OpenApiExample(
            'Bus Stop ID',
            value="44",
            summary='Example bus stop ID'
        ),
        OpenApiExample(
            'Metro Stop ID',
            value="101",
            summary='Example metro stop ID'
        )
    ]
)

dst_parameter = OpenApiParameter(
    name='dst',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Destination transit stop ID',
    required=True,
    examples=[
        OpenApiExample(
            'Bus Stop ID',
            value="55",
            summary='Example bus stop ID'
        ),
        OpenApiExample(
            'Metro Stop ID',
            value="120",
            summary='Example metro stop ID'
        )
    ]
)
