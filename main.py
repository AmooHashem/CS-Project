import time
import math
import copy
from numpy import random
from enum import Enum
from tqdm import tqdm

# inputs
input_requests_rate = 30
simulation_duration = 2880
instances_counts = [2, 1, 1, 1, 1, 1, 1]
timeout = [25, 30, 25, 30, 30, 40, 20]

# consts:
services_time_duration = [8, 5, 6, 9, 12, 2, 3]

# variables and lists
current_time = 0
sections = []
fully_done_requests = []

# util


def get_sample_uniform():
    return random.uniform()

# util


def get_sample_exponential(lambda_value):
    return random.exponential(scale=lambda_value)


class SectionsTypes(Enum):
    RESTAURANT_MANAGEMENT = 0
    CUSTOMERS_MANAGEMENT = 1
    ORDERS_MANAGEMENT = 2
    CONTACT_DELIVERY = 3
    PAYMENT = 4
    MOBILE_API_GATE = 5
    WEB_GATE = 6


requests_path = [
    [SectionsTypes.MOBILE_API_GATE,
        SectionsTypes.ORDERS_MANAGEMENT, SectionsTypes.PAYMENT],

    [SectionsTypes.WEB_GATE, SectionsTypes.ORDERS_MANAGEMENT, SectionsTypes.PAYMENT],

    [SectionsTypes.MOBILE_API_GATE, SectionsTypes.CUSTOMERS_MANAGEMENT,
     SectionsTypes.CONTACT_DELIVERY],

    [SectionsTypes.MOBILE_API_GATE, SectionsTypes.RESTAURANT_MANAGEMENT],

    [SectionsTypes.WEB_GATE, SectionsTypes.RESTAURANT_MANAGEMENT],

    [SectionsTypes.WEB_GATE, SectionsTypes.RESTAURANT_MANAGEMENT,
        SectionsTypes.CONTACT_DELIVERY],

    [SectionsTypes.MOBILE_API_GATE, SectionsTypes.ORDERS_MANAGEMENT],
]


class RequestsTypes(Enum):
    TYPE1 = 0
    TYPE2 = 1
    TYPE3 = 2
    TYPE4 = 3
    TYPE5 = 4
    TYPE6 = 5
    TYPE7 = 6

# util


def generate_random_request_type():
    random_number = random.rand()
    if random_number < 0.2:
        return RequestsTypes.TYPE1
    if random_number < 0.3:
        return RequestsTypes.TYPE2
    if random_number < 0.35:
        return RequestsTypes.TYPE3
    if random_number < 0.6:
        return RequestsTypes.TYPE4
    if random_number < 0.75:
        return RequestsTypes.TYPE5
    if random_number < 0.95:
        return RequestsTypes.TYPE6
    if random_number <= 1:
        return RequestsTypes.TYPE7

# util


def get_section(section_type: SectionsTypes):
    return sections[section_type.value]


class Request:
    def __init__(self, request_type: RequestsTypes):
        self.step = 0
        self.create_time = current_time
        self.enter_queue_time = []
        self.start_process_time = []
        self.end_process_time = []
        self.type = request_type
        path = copy.deepcopy(requests_path[request_type.value])
        self.path = path
        self.needed_times = [math.ceil(
            get_sample_exponential(get_section(path[i]).service_time_average)) for i in range(len(path))]
        self.timeout = timeout[request_type.value]


class Queue:
    def __init__(self):
        self.current_requests: List[Request] = []
        # TODO: calculate
        self.sum_of_queue_length_during_time = 0

    def calculate_queue_info(self):
        self.sum_of_queue_length_during_time += len(self.current_requests)

    def add_request_to_queue(self, request: Request):
        self.current_requests.append(request)

    def remove_request(self):
        first_request = self.current_requests[0]
        self.current_requests.remove(first_request)
        return first_request


class Subsection:
    is_available = True


class Section:
    def __init__(self, section_type: SectionsTypes):
        self.type = section_type
        self.service_time_average = services_time_duration[section_type.value]
        self.subsections: list[Subsection] = [Subsection() for i in range(
            instances_counts[section_type.value])]
        self.queue: Queue = Queue()
        self.in_progress: List[Request] = []
        self.time_in_use = 0
        self.timeout = False
        self.error = False

    def handle_requests(self):
        self.handle_in_queue_requests()
        self.handle_in_progress_requests()
        if len(self.in_progress) > 0:
            self.time_in_use += 1

    def handle_in_queue_requests(self):
        self.queue.calculate_queue_info()
        for subsection in self.subsections:
            if subsection.is_available and len(self.queue.current_requests) > 0:
                first_request = self.queue.remove_request()
                self.add_request_to_in_progress_queue(
                    first_request, subsection)

    def handle_in_progress_requests(self):
        for request in self.in_progress:
            # TODO: check timeout
            request.needed_times[request.step] -= 1
            if request.needed_times[request.step] == 0:
                self.make_request_done(request)

    def add_request_to_section(self, request: Request):
        flag = False
        request.enter_queue_time.append(current_time)
        for subsection in self.subsections:
            if subsection.is_available:
                self.add_request_to_in_progress_queue(request, subsection)
                flag = True
                break
        if not flag:
            self.queue.add_request_to_queue(request)

    def add_request_to_in_progress_queue(self, request: Request, subsection: Subsection):
        subsection.is_available = False
        self.in_progress.append(request)
        request.start_process_time.append(current_time)

    def make_request_done(self, request: Request):
        self.in_progress.remove(request)
        request.end_process_time.append(current_time)
        for subsection in self.subsections:
            if not subsection.is_available:
                subsection.is_available = True
                break

        request.step += 1
        if len(request.needed_times) == request.step:
            fully_done_requests.append(request)
        else:
            next_section = get_section(request.path[request.step])
            next_section.add_request_to_section(request)

###############################


def print_logs():
    tmp = []
    # for section in sections:
    #     tmp.append(len(section.in_progress))
    # print(tmp)
    # tmp = []
    # for section in sections:
    #     tmp.append(len(section.queue.current_requests))
    # print(tmp)
    # print(len(fully_done_requests))
    # print()


def initiate():
    for section in SectionsTypes:
        sections.append(Section(section))


def put_request_in_section(request: Request):
    section = get_section(request.path[request.step])
    section.add_request_to_section(request)


def take_turn():
    global current_time
    new_requests = [Request(generate_random_request_type())
                    for i in range(input_requests_rate)]

    for request in new_requests:
        put_request_in_section(request)

    # from end to start
    sections[3].handle_requests()
    sections[4].handle_requests()
    sections[0].handle_requests()
    sections[1].handle_requests()
    sections[2].handle_requests()
    sections[5].handle_requests()
    sections[6].handle_requests()

    print_logs()

    current_time += 1


#######################

# execution

initiate()

for i in range(simulation_duration):
    take_turn()

while len(fully_done_requests) < simulation_duration * input_requests_rate:
    for section in sections:
        section.handle_requests()
    print_logs()
    current_time += 1

# test

index = 1000
print(fully_done_requests[index].start_process_time)
print(fully_done_requests[index].enter_queue_time)
print(fully_done_requests[index].end_process_time)
print(fully_done_requests[index].path)
print(fully_done_requests[index].needed_times)
