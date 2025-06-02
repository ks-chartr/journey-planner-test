import re
from algorithms.metro.config import METRO_STOPS_DF
from algorithms.bus.config import BUS_STOPS_DF, MAPPED_BUS_STOPS
from algorithms.ncrtc.config import NCRTC_STOPS_DF
from modules.constants import METRO_ENUM, BUS_ENUM, NCRTC_ENUM, WALK_ENUM
import pickle
from modules.logger import logger


class Route:
    def __init__(self):
        self.route = ''
        self.routes = []
        self.type = ''
        self.short_name = ''
        self.long_name = ''
        self.agency = ''
        self.vehicle_id = ''
        self.occupancy = ''
        self.departure_time = ''
        self.ending_time = ''
        self.color = ''
        self.description = ''
        self.trip_time = -1
        self.fare = 0
        self.available_options = []
        self.stops = []
        self.polyline = ''
        self.frequency = 0
        self.distance = 0
        self.meta_info = {}

    def to_dict(self):
        return {
            'route': self.route,
            'routes': self.routes,
            'type': self.type,
            'short_name': self.short_name,
            'long_name': self.long_name,
            'agency': self.agency,
            'vehicle_id': self.vehicle_id,
            'occupancy': self.occupancy,
            'departure_time': self.departure_time,
            'ending_time': self.ending_time,
            'color': self.color,
            'description': self.description,
            'trip_time': self.trip_time,
            'fare': self.fare,
            'available_options': self.available_options,
            'stops': self.stops,
            'polyline': self.polyline,
            'frequency': self.frequency,
            'distance': self.distance,
            'meta_info': self.meta_info
        }

    def __str__(self):
        return f"Route(route={self.route}, routes={self.routes}, type={self.type}, short_name={self.short_name}, " \
               f"long_name={self.long_name}, agency={self.agency}, vehicle_id={self.vehicle_id}, occupancy={self.occupancy}, " \
               f"departure_time={self.departure_time}, ending_time={self.ending_time}, color={self.color}, " \
               f"description={self.description}, trip_time={self.trip_time}, fare={self.fare}, " \
               f"available_options={self.available_options}, stops={self.stops}, polyline={self.polyline}, " \
               f"distance={self.distance}, frequency={self.frequency}, meta_info={self.meta_info})"


class RouteSection:
    def __init__(self):
        self.section_id = None
        self.child_node = None
        self.parent_node = None
        self.route_id = None
        self.arrival_time = None
        self.departure_time = None
        self.travel_time_of_edge = None
        self.distance = ''
        self.birds_distance = ''
        self.is_last_section = False
        self.child_info = None
        self.parent_info = None
        self.fare = None
        self.geometry = ''
        self.vehicle_id = ''

    def __eq__(self, other):
        if not isinstance(other, RouteSection):
            return False

        return (
                self.section_id == other.section_id and
                self.child_node == other.child_node and
                self.parent_node == other.parent_node and
                self.route_id == other.route_id and
                self.arrival_time == other.arrival_time and
                self.departure_time == other.departure_time and
                self.travel_time_of_edge == other.travel_time_of_edge and
                self.distance == other.distance and
                self.birds_distance == other.birds_distance and
                self.is_last_section == other.is_last_section and
                self.child_info == other.child_info and
                self.parent_info == other.parent_info and
                self.fare == other.fare and
                self.geometry == other.geometry and
                self.vehicle_id == other.vehicle_id
        )

    def copy(self, route_section):
        new_section = route_section()
        new_section.section_id = self.section_id
        new_section.child_node = self.child_node
        new_section.parent_node = self.parent_node
        new_section.route_id = self.route_id
        new_section.arrival_time = self.arrival_time
        new_section.departure_time = self.departure_time
        new_section.travel_time_of_edge = self.travel_time_of_edge
        new_section.distance = self.distance
        new_section.birds_distance = self.birds_distance
        new_section.is_last_section = self.is_last_section
        new_section.child_info = self.child_info
        new_section.parent_info = self.parent_info
        new_section.fare = self.fare
        new_section.vehicle_id = self.vehicle_id
        return new_section


class BusRouteSection(RouteSection):
    def __init__(self):
        super().__init__()
        self.stop_type = BUS_ENUM
        self.travel_time_till_edge = None
        self.transfers = 0
        self.edge_type = BUS_ENUM

    def __eq__(self, other):
        if not isinstance(other, BusRouteSection):
            return False

        # First, check if the parent class attributes are equal
        return (
            super().__eq__(other) and  # Call the __eq__ from the parent class
            self.stop_type == other.stop_type and
            self.travel_time_till_edge == other.travel_time_till_edge and
            self.transfers == other.transfers and
            self.edge_type == other.edge_type
        )

    def transform_to_route_section(self, edge):
        self.child_node = edge.child
        self.parent_node = edge.parent
        self.route_id = edge.route_id
        self.arrival_time = edge.arrival_time
        self.departure_time = edge.departure_time
        self.travel_time_till_edge = edge.cost
        self.travel_time_of_edge = edge.travel_time
        self.transfers = edge.transfers
        self.vehicle_id = edge.vehicle_id
        self.distance = edge.walk_distance
        self.birds_distance = edge.walk_distance
        self.child_info = Location(edge.child, self.stop_type).location_info
        self.parent_info = Location(edge.parent, self.stop_type).location_info
        return self

    def __copy__(self):
        new_section = super().copy(BusRouteSection)
        new_section.stop_type = self.stop_type
        new_section.travel_time_till_edge = self.travel_time_till_edge
        new_section.transfers = self.transfers
        new_section.edge_type = self.edge_type
        return new_section

    def __str__(self):
        return f"BusRouteSection(section_id={self.section_id}, child_node={self.child_node}, " \
               f"parent_node={self.parent_node}, route_id={self.route_id}, arrival_time={self.arrival_time}, " \
               f"departure_time={self.departure_time}, travel_time_of_leg={self.travel_time_of_edge}, " \
               f"distance={self.distance}, is_last_section={self.is_last_section})"


class MetroRouteSection(RouteSection):
    def __init__(self):
        super().__init__()
        self.stop_type = METRO_ENUM
        self.edge_type = METRO_ENUM

    def __copy__(self):
        new_section = super().copy(MetroRouteSection)
        new_section.stop_type = self.stop_type
        new_section.edge_type = self.edge_type
        return new_section

    def __str__(self):
        return f"MetroRouteSection(section_id={self.section_id}, child_node={self.child_node}, " \
               f"parent_node={self.parent_node}, route_id={self.route_id}, arrival_time={self.arrival_time}, " \
               f"departure_time={self.departure_time}, travel_time_of_leg={self.travel_time_of_edge}, " \
               f"metro_fare={self.fare}, distance={self.distance}, geometry={self.geometry} is_last_section={self.is_last_section})"


class ParkRideRouteSection(RouteSection):
    def __init__(self):
        super().__init__()
        self.stop_type = METRO_ENUM
        self.edge_type = METRO_ENUM
        self.meta_info = {}
        self.psa = {}
        self.map_dict = {}

    def __copy__(self):
        new_section = super().copy(ParkRideRouteSection)
        new_section.stop_type = self.stop_type
        new_section.edge_type = self.edge_type
        new_section.meta_info = self.meta_info
        new_section.psa = self.psa
        new_section.map_dict = self.map_dict
        return new_section

    def __str__(self):
        return f"ParkRideRouteSection(section_id={self.section_id}, child_node={self.child_node}, " \
               f"parent_node={self.parent_node}, route_id={self.route_id}, arrival_time={self.arrival_time}, " \
               f"departure_time={self.departure_time}, travel_time_of_leg={self.travel_time_of_edge}, " \
               f"metro_fare={self.fare}, distance={self.distance}, geometry={self.geometry}, " \
               f"is_last_section={self.is_last_section})"


class NCRTCRouteSection(RouteSection):
    def __init__(self):
        super().__init__()
        self.stop_type = NCRTC_ENUM
        self.edge_type = NCRTC_ENUM

    def __copy__(self):
        new_section = super().copy(NCRTCRouteSection)
        new_section.stop_type = self.stop_type
        new_section.edge_type = self.edge_type
        return new_section

    def __str__(self):
        return f"NCRTCRouteSection(section_id={self.section_id}, child_node={self.child_node}, " \
               f"parent_node={self.parent_node}, route_id={self.route_id}, arrival_time={self.arrival_time}, " \
               f"departure_time={self.departure_time}, travel_time_of_leg={self.travel_time_of_edge}, " \
               f"metro_fare={self.fare}, distance={self.distance}, geometry={self.geometry}, " \
               f"is_last_section={self.is_last_section})"


class MultiRouteSection(RouteSection):
    def __init__(self):
        super().__init__()
        self.transfers = 0
        self.parent_node_stop_type = ""
        self.child_node_stop_type = ""
        self.edge_type = ""

    def __copy__(self):
        new_section = super().copy(MultiRouteSection)
        new_section.transfers = self.transfers
        new_section.parent_node_stop_type = self.parent_node_stop_type
        new_section.child_node_stop_type = self.child_node_stop_type
        new_section.edge_type = self.edge_type
        return new_section

    def transform(self, route_section, to):
        self.section_id = route_section.section_id
        self.child_node = route_section.child_node
        self.parent_node = route_section.parent_node
        self.route_id = route_section.route_id
        self.transfers = 0
        self.parent_node_stop_type = to
        self.child_node_stop_type = to
        self.edge_type = to
        self.arrival_time = route_section.arrival_time
        self.departure_time = route_section.departure_time
        self.travel_time_of_edge = route_section.travel_time_of_edge
        self.fare = route_section.fare
        self.geometry = route_section.geometry
        self.distance = route_section.distance
        self.birds_distance = route_section.birds_distance
        self.is_last_section = route_section.is_last_section
        self.child_info = route_section.child_info
        self.parent_info = route_section.parent_info
        return self

    def __str__(self):
        return (
            f"[{self.child_node}, {self.parent_node}, {self.route_id}, {self.arrival_time}, "
            f"{self.departure_time}, {self.travel_time_of_edge}, {self.fare}, {self.transfers}, {self.vehicle_id}, "
            f"{self.parent_node_stop_type}, {self.child_node_stop_type}, {self.edge_type}]"
        )


class WalkRouteSection(RouteSection):
    def __init__(self):
        super().__init__()
        self.vehicle_id = 'walk'
        self.parent_node_stop_type = ""
        self.child_node_stop_type = ""
        self.edge_type = WALK_ENUM

    def __copy__(self):
        new_section = super().copy(WalkRouteSection)
        new_section.vehicle_id = self.vehicle_id
        new_section.parent_node_stop_type = self.parent_node_stop_type
        new_section.child_node_stop_type = self.child_node_stop_type
        new_section.edge_type = self.edge_type
        return new_section

    def __str__(self):
        return f"WalkRouteSection(section_id={self.section_id}, child_node={self.child_node}, " \
               f"parent_node={self.parent_node}, route_id={self.route_id}, arrival_time={self.arrival_time}, " \
               f"departure_time={self.departure_time}, travel_time_of_leg={self.travel_time_of_edge}, " \
               f"distance={self.distance}, is_last_section={self.is_last_section})"


class NearestStop:
    def __init__(self, stop_id, stop_name, stop_code, stop_type, geometry, distance, birds_distance, travel_time,
                 source_name,
                 fare=0):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.tkt_code = stop_code
        self.stop_type = stop_type
        self.geometry = geometry
        self.distance = distance
        self.birds_distance = birds_distance
        self.travel_time = travel_time
        self.source_name = source_name
        self.fare = fare
        self.stop_of = None
        self.data = {}

    def to_dict(self):
        return {
            'stop_id': self.stop_id,
            'stop_name': self.stop_name,
            'stop_code': self.tkt_code,
            'stop_type': self.stop_type,
            'geometry': self.geometry,
            'distance': self.distance,
            'travel_time': self.travel_time,
            'source_name': self.source_name
        }

    def __str__(self):
        return f"NearestStop(stop_id={self.stop_id}, stop_name={self.stop_name}, stop_type={self.stop_type}, " \
               f"geometry={self.geometry}, distance={self.distance}, travel_time={self.travel_time}, " \
               f"source_name={self.source_name})"


class Location:
    stop_types = None

    def __init__(self, location_value, location_type, location_name=None):
        self.location_type = location_type
        self.location_value = location_value
        self.location_name = location_name if location_name else f"Unknown {location_type} Location"
        self.tkt_code = self.clean_stop_name(location_name)
        self.cords = None
        self.location_info = self.assign_location_information()

    def __len__(self):
        return len(self.location_info)

    @staticmethod
    def clean_stop_name(name):
        try:
            name = name.strip(" \t\n\r!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
            name = re.sub(r'\W+', '_', name)
            return name
        except AttributeError:
            return name

    @staticmethod
    def get_mapped_stops(mapping_file):
        try:
            with open(mapping_file, 'rb') as file:
                mapping = pickle.load(file)
        except:
            mapping = {}

        return mapping

    @staticmethod
    def get_stops_dict(stops_df):
        try:
            stops_df.rename(
                columns={'stop_id': 'id', 'stop_name': 'name', 'stop_lat': 'lat', 'stop_lon': 'lon', 'lng': 'lon'},
                inplace=True)
        except KeyError as e:
            print(e)
            pass
        if stops_df.empty:
            logger.warning("Stops_df is empty, replacing with empty dict.")
            return {}
        else:
            stops_df['idx'] = stops_df.loc[:, 'id']
            if 'tkt_code' not in stops_df:
                stops_df['tkt_code'] = ''
            stops_dict = stops_df[['idx', 'id', 'name', 'lat', 'lon', 'tkt_code']].set_index('idx').T.to_dict()
            del stops_df

        return stops_dict

    def assign_location_information(self):
        if Location.stop_types is None:
            Location.stop_types = {

                METRO_ENUM: {
                    "stops_dict": self.get_stops_dict(METRO_STOPS_DF),
                    "stops_mapping": self.get_mapped_stops(MAPPED_BUS_STOPS)
                },
                BUS_ENUM: {
                    "stops_dict": self.get_stops_dict(BUS_STOPS_DF),
                    "stops_mapping": self.get_mapped_stops("no_file")
                },
                NCRTC_ENUM: {
                    "stops_dict": self.get_stops_dict(NCRTC_STOPS_DF),
                    "stops_mapping": self.get_mapped_stops("no-file")
                }
            }

        try:
            # print(Location.stop_types[self.location_type]["stops_dict"][self.location_value])
            # print(self.location_value, self.location_type)
            stop_information: dict = Location.stop_types[self.location_type]["stops_dict"][self.location_value]
            self.location_name = stop_information['name']
            self.location_value = stop_information['id']
            self.cords = (round(stop_information['lat'], 6), round(stop_information['lon'], 6))
            self.tkt_code = stop_information['tkt_code']
            return {
                'id': self.location_value,
                'lat': stop_information['lat'],
                'lon': stop_information['lon'],
                'name': self.location_name,
                'tkt_code': str(self.tkt_code)
            }

        except KeyError as e:
            try:
                stop_information: dict = Location.stop_types[self.location_type]["stops_mapping"][self.location_value]
                self.location_name = stop_information['name']
                self.location_value = stop_information['id']
                self.cords = (round(stop_information['lat'], 6), round(stop_information['lon'], 6))
                return {
                    'id': self.location_value,
                    'lat': stop_information['lat'],
                    'lon': stop_information['lon'],
                    'name': self.location_name,
                    'tkt_code': ''
                }

            except KeyError as e:
                # print(self.location_value, ":", e)
                self.location_name = self.location_name
                self.location_value = self.location_value
                self.cords = self.location_value

                return {
                    'id': self.location_value,
                    'lat': '' if isinstance(self.location_value, int) else round(self.location_value[0], 6),
                    'lon': '' if isinstance(self.location_value, int) else round(self.location_value[1], 6),
                    'name': self.location_name,
                    'tkt_code': ''
                }

    def __str__(self):
        return f"LocationType(location_type={self.location_type}, location_value={self.location_value}, " \
               f"location_name={self.location_name}, location_info={self.location_info})"

    def to_dict(self):
        return {
            'location_type': self.location_type,
            'location_value': self.location_value,
            'location_info': self.location_info
        }
