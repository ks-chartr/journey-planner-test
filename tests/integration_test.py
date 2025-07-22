import click
from .utils_route_existence import *
from .utils_distance import *
import warnings

warnings.filterwarnings("ignore")


def route_existence_test(request_type):
    parallel_stop_existence_zero(request_type)


def replicate_route_existence_test(request_type):
    if request_type == 'zero':
        replicate_zero_hop_test()


def distance_test(request_type):
    distance_test_parallel(request_type)


# distance_test, zero_hop_test
# make an argument accepting string from user with above two option
@click.command()
@click.argument('test_type',
                type=click.Choice(
                    ['distance_test', 'zero_hop_test', 'replicate_zero_hop_test']
                )
                )
def main(test_type):
    if test_type == 'distance_test':
        print('Running distance test')
        distance_test('')

    elif test_type == 'zero_hop_test':
        print('Running zero hop test')
        route_existence_test('zero')

    elif test_type == 'replicate_zero_hop_test':
        print('Running replicate zero hop test')
        replicate_route_existence_test('zero')


if __name__ == '__main__':
    main()
