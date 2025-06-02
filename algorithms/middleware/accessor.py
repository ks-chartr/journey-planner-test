from algorithms.bus.v2 import BusV2
from algorithms.metro.v2 import MetroV2
# PTX mode is not implemented
from algorithms.multimodal.v2 import MultiModalV2
from algorithms.multincrtc.core import MultiNCRTC
from algorithms.ncrtc.v2 import NCRTCV2
from modules.constants import *
from modules.logger import logger
from serializers.utils import is_in_location


class ResourceAccessorV2:
    resource_dict = None
    resource_object_dict = {
        'walk_metro': MetroV2(),
        'walk_bus': BusV2(),
        'walk_multi': MultiModalV2(),
        'walk_ncrtc': NCRTCV2(),
        'walk_metroncrtc': MultiNCRTC(),
        'walk_busncrtc': MultiNCRTC(),
        'walk_multincrtc': MultiNCRTC(),
    }

    def __init__(self, key):
        self.resource_dict = {
            'walk_metro': self.get_walk_metro,
            'walk_bus': self.get_walk_bus,
            'walk_multi': self.get_walk_multi,
            'walk_ncrtc': self.get_walk_ncrtc,
            'walk_metroncrtc': self.get_walk_metro_ncrtc,
            'walk_busncrtc': self.get_walk_bus_ncrtc,
            'walk_multincrtc': self.get_walk_multi_ncrtc,
            'walk_generic': self.get_generic_resource,
        }

        self.key = key
        self.request_data = None
        self.resource_object = self.resource_object_dict[self.key]

    def get_walk_metro(self):
        logger.debug("In Walk Metro")
        resource = self.resource_object
        return resource

    def get_walk_bus(self):
        logger.debug("In Walk Bus")
        resource = self.resource_object
        return resource

    def get_walk_multi(self):
        logger.debug("In Walk Multi")
        resource = self.resource_object
        return resource

    def get_walk_ncrtc(self):
        resource = self.resource_object
        return resource

    def get_walk_metro_ncrtc(self):
        resource = self.resource_object
        return resource

    def get_walk_bus_ncrtc(self):
        resource = self.resource_object
        return resource

    def get_walk_multi_ncrtc(self):
        resource = self.resource_object
        return resource

    def get_generic_resource(self):
        if self.request_data is None:
            logger.error("Not a valid implementation, request data is None.")
            assert False, "Request data is None."

        src_info = self.request_data.get(SRC).location_info  # Location objects
        dst_info = self.request_data.get(DST).location_info
        if src_info is None or dst_info is None:
            logger.error("Not a valid implementation, src or dst is None.")
            assert False, "Src or Dst is None."

        src_coord = (src_info[LAT], src_info[LON])
        dst_coord = (dst_info[LAT], dst_info[LON])
        mode_to_reach_transit, _ = self.request_data.get('mode')
        self.request_data['mode'][1] = METRO_ENUM

        if (
                (is_in_location(src_coord) and not is_in_location(dst_coord)) or
                (not is_in_location(src_coord) and is_in_location(dst_coord)) or
                (not is_in_location(src_coord) and not is_in_location(dst_coord))
        ):
            logger.info("Requesting for NCRTC case with Walk:")
            return self.get_walk_metro_ncrtc()
        else:
            logger.info("Requesting for Metro case with Walk:")
            return self.get_walk_metro()

    def get_resource_by_mode(self, request_data=None):
        self.request_data = request_data
        logger.debug(f"Resource allocation key: {self.key}")
        return self.resource_dict[self.key]()
