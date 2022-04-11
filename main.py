from System import System
from ApproxTask import ApproxTask

from csv import reader
from ast import literal_eval

# scheduler variables
k = 20
frame_deadline = 500    # in ms
time_step = 0.0001     # fidelity of each time step for the scheduler/task execution times, in ms

system = System("EnSuRe", k, frame_deadline, time_step, 3, 0.5, True)

# 0. Test task set
# tasks = [
#     # Task(id, lp_manExecTime, hp_manExecTime, lp_optExecTime, hp_optExecTime, deadline)
#     ApproxTask(0, 20, 10, 4, 2, 80),
#     ApproxTask(1, 30, 15, 0, 0, 70),
#     ApproxTask(2, 12, 6, 0, 0, 90),
#     ApproxTask(3, 10, 25, 0, 0, 200),
#     ApproxTask(4, 12, 6, 0, 0, 100),
#     ApproxTask(5, 30, 15, 0, 0, 60),
#     ApproxTask(6, 30, 15, 0, 0, 50),

#     # ApproxTask(0, 30, 15, 4, 2, 40),
#     # ApproxTask(1, 20, 10, 0, 0, 100)
# ]

# 0. Read application task set from file
with open('tasksets/sysutil0.9_cores3_2.csv', 'r') as read_obj:
    # pass the file object to reader() to get the reader object
    csv_reader = reader(read_obj)
    # Get all rows of csv from csv_reader object as list of tuples
    tasks_data = [tuple(map(literal_eval, x)) for x in map(tuple, csv_reader)]
    
# convert data into Task objects
tasks = []
task_total_workload = 0
for task in tasks_data:
    tasks.append(ApproxTask(task[0], task[1], task[2], 0, 0, task[3]))
    task_total_workload += task[1]

#print(task_total_workload)

system.run(tasks)