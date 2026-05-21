# Directions API
This is an API that provides directions between two points with different properties.

# Installation + Setup
## Installation from the source code
To install the API, you need to follow the steps written below:
- Make sure you have `python==3.10` installed in your system, check the version of python using the following command.
```sh
python3 --version  # this should return 3.10.x
```
- Clone the `jatin` branch from the directions service repository at your desired location using the following command.
```sh
git clone https://github.com/transport-stack/journey-planner.git
```
- Move to the directions folder (which is the root folder of the project).
- Open the terminal at the root folder location of the project and create a virtual environment using the following command.
```sh
python3 -m venv venv
```
- Activate the virtual environment using the following command
```sh
source venv/bin/activate  # for linux machines
/venv/Scripts/activate  # for windows machines
```
- Install poetry and then install the project requiremtns using the following command .
```sh
pip install poerty
poerty install
```
- Create a data folder in the root location of the repository.
- Move the required data in the folder.
- Run the project using any of the following command in cmd or from the IDE GUI based runners
```sh
poetry run python manage.py runserver  # for linux macines
python python manage.py runserver # for linux macines
poetry run python ./manage.py runserver  # for windows macines
python python ./manage.py runserver # for windows macines
```

# Dependecies  
## Build Dependecies
- python = "^3.10"
- django = "^5.0.2"
- geopy = "^2.4.1"

## Testing Dependecies
- pytest = "^8.0.0"
- black = "^22.1.0"
- flake8 = "^4.0.1"
- mypy = "^0.910"
- isort = "^5.10.3"
- pylint = "^2.11.1"



# Integration
The api has the following endpoint:

1. `/api/<version>/get_multi_modal/?<args>`
2. `/api/<version>/get_stops/?<args>`

##  1. `/api/<version>/get_multi_modal/?<args>`
The version is the version of the api. The current version is 2.
The current version of API can be accessed at `/api/v2/get_multi_modal/`.

Similarly, the previous version of API can be accessed at `/api/v1/get_multi_modal/`.

The args are of two types:
1. Required args
2. Optional args

The required args are as follows:
1. `src_type`: The type of the source point. 
   1. The options are: place, bus, metro
2. `src`: The source point. This can be a place_id or a latlng.
   1. If the src_type is place, then the src should be a latlng in list of length 2 having lat at 0th index and lng at 1st index.
   2. If the src_type is bus, then the src should be one metro stop_id either in list of length 1 or non-list form.
   3. If the src_type is metro,  then the src should be one metro stop_id either in list of length 1 or non-list form.
3. `dst_type`: The type of the destination point. 
   1. The options are: place, bus, metro
4. `dst`: The destination point. This can be a place_id or a latlng.
   1. If the dst_type is place, then the src should be a latlng in list of length 2 having lat at 0th index and lng at 1st index.
   2. If the dst_type is bus, then the src should be one metro stop_id either in list of length 1 or non-list form.
   3. If the dst_type is metro,  then the src should be one metro stop_id either in list of length 1 or non-list form.
5. `mode`: The mode of transport. The options are: bus, metro, combination of bus and metro.
   1. `bus` The api will return the directions for bus only.
   2. `metro` The api will return the directions for metro only.
   3. `multi` The api will return the directions with the combination of bus and metro.
   4. `ptx/auto/bike`: The api will return the response from src_cord to dst_cord using rapido/auto/bike.
   5. `walk`: The api will return the response from src to cord using walk only.
   6. `ptx,metro`: The api will return the response using rapido and metro.
   7. `ptx,bus`: The API will return the response using rapido and bus.

The optional args are as follows:
1. `time`: The time of departure. 
   1. The format is HH:MM:SS.
   2. The default is the current time.
2. `src_name`: The name of the source point. 
   1. The default is  `Your Location`.
3. `dst_name`: The name of the destination point. 
   1. The default is `destination`.

The examples api calls are as follows:
1. `/api/v2/get_multi_modal/?src=[28.7041,77.1025]&src_type=place&dst=28.7041,77.1025&dst_type=place&mode=bus`
2. `/api/v2/get_multi_modal/?src=44&src_type=metro&dst=101&dst_type=metro&mode=metro&time=12:00:00`
3. `/api/v2/get_multi_modal/?src=44&src_type=metro&dst=101&dst_type=metro&mode=multi&time=12:00:00`
4. `/api/v2/get_multi_modal/?src=44&src_type=metro&dst=101&dst_type=metro&mode=ptx,metro&time=12:00:00`
5. `/api/v2/get_multi_modal/?src=44&src_type=metro&dst=101&dst_type=metro&mode=ptx,bus&time=12:00:00`
6. `/api/v2/get_multi_modal/?src=44&src_type=metro&dst=101&dst_type=metro&mode=bike&time=12:00:00`
7. `/api/v2/get_multi_modal/?src=44&src_type=metro&dst=101&dst_type=metro&mode=auto&time=12:00:00`
8. `/api/v2/get_multi_modal/?src=44&src_type=metro&dst=101&dst_type=metro&mode=ptx&time=12:00:00`

##  2. `/api/<version>/get_multi_modal/?<args>`
The version is the version of the api. The current version is 2.
The current version of API can be accessed at `/api/v2/get_stops/`.\
Similarly, the previous version of API can be accessed at `/api/v1/get_stops/`.

The args have only required arg: mode.
1. `mode`: The mode of transport. The options are: bus, metro, multi, ptx, 'ptx,bus', 'ptx,metro' combination of bus and metro.
   1. `bus`: then the api will return the bus stops.
   2. `metro`: then the api will return the metro stops.


The example API calls are as follows:
1. `/api/v2/get_stops/?mode=bus`
2. `/api/v2/get_stops/?mode=metro`
