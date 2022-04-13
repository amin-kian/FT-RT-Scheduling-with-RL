from FEST_Scheduler import FEST_Scheduler
from EnSuRe_Scheduler import EnSuRe_Scheduler
from Core import Core
from Task import Task
from ApproxTask import ApproxTask

import sys

from csv import reader
from ast import literal_eval

import copy

# FEST variables
k = 20
frame_deadline = 200    # in ms
precision_dp = 3
time_step = 1/10**precision_dp     # fidelity of each time step for the scheduler/task execution times, in ms
lp_hp_ratio = 0.8

class System:
    """
    Class which represents a heterogeneous system that has one or more Low-Power (LP) cores, and one High-Performance (HP) core.
    """
    def __init__(self, scheduler_type, k, frame, time_step, num_lp_cores, lp_hp_ratio, log_debug=False):
        """
        Class constructor (__init__).

        scheduler_type: the scheduler to use, "FEST" or "EnSuRe"
        k: number of faults the system can support
        frame: size of the frame, in ms
        time_step: fidelity of each time step for the scheduler/task execution times, in ms
        lp_hp_ratio: ratio of LP to HP frequency
        log_debug: whether to print logging statements
        """
        # define scheduler
        self.scheduler_type = scheduler_type
        if scheduler_type == "FEST":
            self.scheduler = FEST_Scheduler(k, frame, time_step, log_debug)
        elif scheduler_type == "EnSuRe":
            self.scheduler = EnSuRe_Scheduler(k, frame, time_step, num_lp_cores, lp_hp_ratio, log_debug)
        else:
            raise SystemExit("Invalid scheduler type given.")

        lp_freq = 1.0
        hp_freq = lp_freq / lp_hp_ratio

        self.lp_cores = []
        for i in range(num_lp_cores):
            self.lp_cores.append(Core(name="LP_Core{0}".format(i), isLP=True, ai=0.3, f=lp_freq, xi=0.03, p_idle=0.02))
        self.hp_core = Core(name="HP_Core", isLP=False, ai=1.0, f=hp_freq, xi=0.1, p_idle=0.05)

        # logging
        self.log_debug = log_debug  # whether to print log statements or not

    def run(self, taskset):
        """
        Runs the scheduling algorithm with the following high-level steps:
        1. Generate schedule. If no feasible schedule can be generated, exit
        2. Simulate execution of the tasks, and calculate the system's energy consumption

        taskset: the taskset to be scheduled by the algorithm.
        """
        # make a copy of the task set to allow reusability
        tasks = copy.deepcopy(taskset)

        # 1. Generate schedule
        if not self.scheduler.generate_schedule(tasks):
            print("Failed to generate schedule. Exiting simulation")
            return
        
        if self.log_debug:
            print("Schedule generated")
            #self.scheduler.print_schedule()

        # 2. Runtime: execute tasks
        if self.log_debug:
            print("Start running simulation ...")
        # start running the scheduler
        self.scheduler.simulate(self.lp_cores, self.hp_core)
        
        # 3. RESULTS
        if self.log_debug:
            print("===RESULTS===")
        # check which core executed each tasks

        # check if any tasks did not manage to complete
        if self.scheduler_type == "FEST":
            if len(self.scheduler.backup_list) > 1:
                print("THIS SHOULD NOT HAPPEN, BUT,")
                print("Some tasks did not get to execute: ")
                for task in self.scheduler.backup_list:
                    print(task.getId())
        elif self.scheduler_type == "EnSuRe":
            for backup_list in self.scheduler.backup_list:
                if len(backup_list) > 1:
                    print("THIS SHOULD NOT HAPPEN, BUT,")
                    print("Some tasks did not get to execute: ", end="")
                    for task in backup_list:
                        print(task.getId())

        # print energy consumption
        if self.log_debug:
            print("Active Durations:")
            for lpcore in self.lp_cores:
                print("  {0}: {1}".format(lpcore.name, lpcore.get_active_duration()))
            print("  {0}: {1}".format(self.hp_core.name, self.hp_core.get_active_duration()))
            print("Energy Consumption:")
            for lpcore in self.lp_cores:
                print("  {0}: {1}".format(lpcore.name, lpcore.get_energy_consumed()))
            print("  {0}: {1}".format(self.hp_core.name, self.hp_core.get_energy_consumed()))


    def get_energy_consumption(self):
        """
        Get the total energy consumption of this system, which is the sum of the energy consumption of its cores.
        """
        energy_consumption = 0
        for lpcore in self.lp_cores:
            energy_consumption += lpcore.get_energy_consumed()
        energy_consumption += self.hp_core.get_energy_consumed()

        return energy_consumption

    def get_hpcore_active_duration(self):
        return self.hp_core.get_active_duration()


if __name__ == "__main__":    # parse arguments
    try:
        file = sys.argv[1]
    except IndexError:
        raise SystemExit("Error: please run 'python38 System.py [file]', e.g. 'python38 System.py tasksets/sysutil0.5_cores1_0.csv'\r\n\r\n  file = CSV file containing the taskset")

    print("===SCHEDULER PARAMETERS===")
    print("Scheduler = {0}".format("FEST"))
    print("k = {0}".format(k))
    print("frame = {0} ms".format(frame_deadline))

    print("===SIMULATION===")
    system = System("EnSuRe", k, frame_deadline, time_step, 1, lp_hp_ratio, True)

    # 0. Read application task set from file
    with open(file, 'r') as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)
        # Get all rows of csv from csv_reader object as list of tuples
        tasks_data = [tuple(map(literal_eval, x)) for x in map(tuple, csv_reader)]
        
    # convert data into Task objects
    tasks = []
    for task in tasks_data:
        hp_execTime = round(task[1] * lp_hp_ratio, precision_dp)
        #tasks.append(Task(task[0], task[1], hp_execTime))
        tasks.append(ApproxTask(task[0], task[1], hp_execTime, 0, 0, task[3]))


    system.run(tasks)