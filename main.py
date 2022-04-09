from System import System
from ApproxTask import ApproxTask

# scheduler variables
k = 2
frame_deadline = 100    # in ms
time_step = 0.01     # fidelity of each time step for the scheduler/task execution times, in ms

system = System("EnSuRe", k, frame_deadline, time_step, 3, 0.8, True)

# 0. Read application task set from file
tasks = [
    # Task(id, lp_manExecTime, hp_manExecTime, lp_optExecTime, hp_optExecTime, deadline)
    ApproxTask(0, 20, 10, 4, 2, 80),
    ApproxTask(1, 30, 15, 0, 0, 70),
    ApproxTask(2, 12, 6, 0, 0, 90),
    ApproxTask(3, 10, 25, 0, 0, 200),
    ApproxTask(4, 12, 6, 0, 0, 100),
    ApproxTask(5, 30, 15, 0, 0, 60),
    ApproxTask(6, 30, 15, 0, 0, 50),

    # ApproxTask(0, 30, 15, 4, 2, 40),
    # ApproxTask(1, 20, 10, 0, 0, 100)
]

system.run(tasks)