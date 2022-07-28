import time
import math
import copy
from numpy import random
from enum import Enum
from tqdm import tqdm

# inputs
input_requests_rate = 30
simulation_duration = 2880
instances_counts = [20, 10, 10, 10, 10, 10, 10]
timeout = [25, 30, 25, 30, 30, 40, 20]

# consts:
services_time_duration = [8, 5, 6, 9, 12, 2, 3]

# variables and lists
current_time = 0
sections = []
all_requests = []
fully_done_requests = []
dropped_requests = []

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
        self.is_timed_out = False


class Queue:
    def __init__(self):
        self.current_requests: List[Request] = []
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
            # check timeout
            if current_time - request.create_time > request.timeout:
                self.drop_request(request)
                continue
            # end of check timeout
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

    def drop_request(self, request: Request):
        self.in_progress.remove(request)
        request.end_process_time.append(current_time)
        for subsection in self.subsections:
            if not subsection.is_available:
                subsection.is_available = True
                break

        request.is_timed_out = True
        dropped_requests.append(request)




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


def handle_all_sections():
    # from end to start
    sections[3].handle_requests()
    sections[4].handle_requests()
    sections[0].handle_requests()
    sections[1].handle_requests()
    sections[2].handle_requests()
    sections[5].handle_requests()
    sections[6].handle_requests()

    print_logs()


def take_turn():
    global current_time
    new_requests = [Request(generate_random_request_type())
                    for i in range(input_requests_rate)]

    all_requests.extend(new_requests)

    for request in new_requests:
        put_request_in_section(request)

    handle_all_sections()

    current_time += 1


#######################

# execution

initiate()

for i in range(simulation_duration):
    take_turn()

while len(fully_done_requests) + len(dropped_requests) != len(all_requests):
    handle_all_sections()

    current_time += 1

# test

# calculate average queues length
my_sum = 0
for section in sections:
    my_sum += section.queue.sum_of_queue_length_during_time / current_time
average_queues_length = my_sum / len(sections)

index = 1
print(fully_done_requests[index].start_process_time)
print(fully_done_requests[index].enter_queue_time)
print(fully_done_requests[index].end_process_time)
print(fully_done_requests[index].path)
print(fully_done_requests[index].needed_times)

print("Average queues length:", average_queues_length)

# calculating queue delays
request_types_total_delay = [0] * 7
request_types_count = [0] * 7
for req in all_requests:
    req: Request
    req_delay_sum = 0
    for i in range(len(req.enter_queue_time)):
        req_delay_sum += req.start_process_time[i] - req.enter_queue_time[i]
    request_types_count[req.type.value] += 1
    request_types_total_delay[req.type.value] += req_delay_sum

request_types_average_delay = [0] * 7
for i in range(len(request_types_count)):
    request_types_average_delay[i] = request_types_total_delay[i] / request_types_count[i]

print("Average total requests queue delay:", sum(request_types_total_delay) / len(all_requests))
print("Average requests queue delay by request type:", request_types_average_delay)

# calculating sections utilization
sections_utilization = [0] * 7
for i in range(len(sections)):
    sections_utilization[i] = sections[i].type.name + ": " + str(sections[i].time_in_use / current_time * 100)
print("Utilization of each service:", sections_utilization)

print("Total Percentage of timed out requests:")
print("Percentage of timed out requests by type:")

print("Done requests:", len(fully_done_requests))
print("Dropped requests:", len(dropped_requests))

print("Simulation time:", current_time)
