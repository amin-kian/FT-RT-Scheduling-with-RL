from FEST_Scheduler import FEST_Scheduler
from EnSuRe_Scheduler import EnSuRe_Scheduler
from EnSuRe_RL_Scheduler import EnSuRe_RL_Scheduler
from Core import Core
import copy


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
        elif scheduler_type == "EnSuRe-RL":
            self.scheduler = EnSuRe_RL_Scheduler(k, frame, time_step, num_lp_cores, lp_hp_ratio, log_debug)
        # else:
        #     raise SystemExit("Invalid scheduler type given.")

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
        3. Print the results of the simulation (if log_debug == True)

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
            # self.scheduler.print_schedule()

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
        elif self.scheduler_type == "EnSuRe" or self.scheduler_type == "EnSuRe-RL":
            for backup_list in self.scheduler.backup_list:
                if len(backup_list) > 1:
                    print("THIS SHOULD NOT HAPPEN, BUT,")
                    print("Some tasks did not get to execute: ")
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
        """
        Get the duration that the HP core was active.
        """
        return self.hp_core.get_active_duration()
