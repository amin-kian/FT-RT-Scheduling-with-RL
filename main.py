from FEST_Scheduler import FEST_Scheduler
from Core import Core
from Task import Task

import sys

# FEST variables
k = 5
frame_deadline = 200    # in ms
time_step = 0.1     # fidelity of each time step for the scheduler/task execution times, in ms

# Represents the system
class System:
    def __init__(self, k, frame, time_step):
        self.power_consumption = 0
        self.scheduler = FEST_Scheduler(k, frame, time_step)

        #self.sim_time = 0
        self.sim_step = time_step   # ms

        self.lp_cores = [ Core(name="LP_Core0", isLP=True, ai=0.3, f=0.8, xi=0.03, p_idle=0.02) ]
        self.hp_core = Core(name="HP_Core", isLP=False, ai=1.0, f=1.0, xi=0.1, p_idle=0.05)

    def run(self):
        # 0. Application task set (TEMP)
        tasks = [
            Task(0, 20, 14),
            Task(1, 22, 13),
            Task(2, 22, 12),
            Task(3, 18, 17),
            Task(4, 25, 20),
            Task(5, 21, 15),
        ]

        # 1. Generate schedule
        if not self.scheduler.generate_schedule(tasks):
            print("Failed to generate schedule. Exiting simulation")
            return
        
        print("Schedule generated")
        self.scheduler.print_schedule()

        # 2. Runtime: execute tasks
        print("Start running simulation ...")
        # start running the scheduler
        self.scheduler.simulate(self.lp_cores, self.hp_core)
        
        # 3. RESULTS
        print("===RESULTS===")
        # check which core executed each tasks

        # check if any tasks did not manage to complete
        if self.scheduler.backup_list:
            print("THIS SHOULD NOT HAPPEN, BUT,")
            print("Some tasks did not get to execute: ", end="")
            for task in self.scheduler.backup_list:
                print(task.getId())
        # print energy consumption
        print("Active Durations:")
        for lpcore in self.lp_cores:
            print("  {0}: {1}".format(lpcore.name, lpcore.get_active_duration()))
        print("  {0}: {1}".format(self.hp_core.name, self.hp_core.get_active_duration()))
        print("Energy Consumption:")
        for lpcore in self.lp_cores:
            print("  {0}: {1}".format(lpcore.name, lpcore.get_energy_consumed()))
        print("  {0}: {1}".format(self.hp_core.name, self.hp_core.get_energy_consumed()))

def taskset_generator():
    pass

if __name__ == "__main__":
    # parse arguments
    try:
        k = int(sys.argv[1])
        frame_deadline = int(sys.argv[2])
    except IndexError:
        raise SystemExit("Error: please run 'python38 main.py [k] [frame]', e.g. 'python38 main.py 5 200'\r\n\r\n  k = no. faults to tolerate | frame = deadline (ms)")

    print("===SCHEDULER PARAMETERS===")
    print("Scheduler = {0}".format("FEST"))
    print("k = {0}".format(k))
    print("frame = {0} ms".format(frame_deadline))

    print("===SIMULATION===")
    system = System(k, frame_deadline, time_step)
    system.run()