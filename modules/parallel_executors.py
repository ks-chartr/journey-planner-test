from multiprocessing import pool, Pool
import asyncio
from threading import Thread
from queue import Queue
from modules.logger import logger
import signal
from concurrent.futures import ThreadPoolExecutor

TIMEOUT = 10


def run_sync_coroutine(coroutine_function, *args):
    return asyncio.run(coroutine_function(*args))


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


# def parallel_executor(target_functions, arguments, no_of_max_function=4):
#     """
#     :param target_functions: A list of function
#     :param arguments:  A list of arguments(tuple of all arguments) passed for corresponding function.
#     :param no_of_max_function: Number of maximum function allowed at once
#     :return: list of result index at their respective function index
#     """
#     logger.info(f"Parallel execution of {str(target_functions)}")
#     assert len(target_functions) == len(arguments) and len(arguments) <= no_of_max_function
#     number_of_executors = len(arguments)
#     results = []
#     with Pool(processes=number_of_executors, initializer=init_worker) as process_pool:

#         try:
#             results = [process_pool.apply_async(function, args=argument)
#                 for function, argument in zip(target_functions, arguments)]
#             results = [r.get(timeout=TIMEOUT) for r in results]

#         except TimeoutError as e:
#             logger.info(f"Task timeout: {e}")
#             results = -1
#         except Exception as e:
#             logger.error(f"Handle this error: {e}")
#             results = -2
#             exit(-2)

#     print("got2")

#     process_pool.close()
#     process_pool.join()

#     results = [result for result in results if result]
#     if not results:
#         results = [function(argument) for function, argument in zip(target_functions, arguments)]

#     if results == -1:
#         logger.log("Can not find ptx stops due to timeout.")
#         return []

#     return results


def parallel_executor(target_functions, arguments, no_of_max_function=4):
    """
    :param target_functions: A list of function
    :param arguments:  A list of arguments(tuple of all arguments) passed for corresponding function.
    :param no_of_max_function: Number of maximum function allowed at once
    :return: list of result index at their respective function index
    """
    logger.info(f"Parallel execution of {str(target_functions)}")
    assert len(target_functions) == len(arguments) and len(arguments) <= no_of_max_function
    number_of_executors = len(arguments)

    def runner1():
        print(arguments[0])
        return target_functions[0](arguments[0][0], arguments[0][1])

    def runner2():
        print(arguments[1])
        return target_functions[1](arguments[1][0], arguments[0][1])

    with ThreadPoolExecutor() as executor:
        future_result_1 = executor.submit(runner1)
        future_result_2 = executor.submit(runner2)

    results = [future_result_1.result(), future_result_2.result()]

    return results


def runner(target_function, argument, queue):
    result = target_function(*argument)
    queue.put(result)


def run_parallel_one(target_function, argument, queue):
    thread = Thread(target=runner, args=(target_function, argument, queue))
    thread.start()
    return thread


