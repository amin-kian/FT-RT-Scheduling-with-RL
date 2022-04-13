import random

class FEST_Scheduler:
    # init
    def __init__(self, k, frame, time_step, log_debug):
        """
        Class constructor (__init__).

        k: number of faults the system can support
        frame: size of the frame, in ms
        time_step: fidelity of each time step for the scheduler/task execution times, in ms
        log_debug: whether to print logging statements
        """
        # application parameters
        self.k = k
        self.frame = frame
        self.time_step = time_step

        # scheduler variables
        self.pri_schedule = dict()
        self.backup_start = 0
        self.backup_list = None

        # logging
        self.log_debug = log_debug  # whether to print log statements or not

    # class helper functions
    def getLPExecutionTime(task):
        """
        Helper function for sorting tasks in order of their execution times on the LP core.
        """
        return task.getLPExecutionTime()
    
    def getHPExecutionTime(task):
        """
        Helper function for sorting tasks in order of their execution times on the HP core.
        """
        return task.getHPExecutionTime()

    # Function to generate schedule
    def generate_schedule(self, tasksList):
        """
        Try to generate a schedule for the given task set. This follows the pseudo-code of the FEST algorithm from the paper.
        Returns True if a feasible schedule is generated successfully, or False if no feasible schedule can be generated.
        
        tasksList: the task set to generate a schedule for.
        """
        # 1. Sort tasks in non-increasing order of execution time
        tasksList.sort(reverse=True, key=FEST_Scheduler.getLPExecutionTime)

        # 2. Schedule primary tasks onto the LP core
        start_time = 0
        for task in tasksList:
            lp_executionTime = FEST_Scheduler.getLPExecutionTime(task)
            if start_time + lp_executionTime <= self.frame:
                self.pri_schedule[start_time] = task
                start_time += lp_executionTime
            else:   ## if not schedulable, exit
                print("Unable to schedule tasks")
                return False

        # 3. Create backup list
        self.backup_list = tasksList.copy()
        #self.backup_list.sort(reverse=True, key=FEST_Scheduler.getHPExecutionTime)

        # 4. Compute BB-overloading window size
        self.update_BB_overloading(0)

        # Generated schedule successfully
        return True

    def remove_from_backup_list(self, taskId, sim_time):
        """
        Given a task id, remove its corresponding task from the backup_list.
        To be called when a task (either its primary or backup copy) completes execution successfully.

        taskId: id of the task to be removed
        """
        # remove task from backup list
        self.backup_list = [i for i in self.backup_list if i.getId() != taskId]
        # update size of BB-overloading window
        self.update_BB_overloading(sim_time)

    def update_BB_overloading(self, sim_time):
        """
        Update backup_start with the current size of the BB-overloading window.
        Up to k tasks will be reserved for BB-overloading.
        """
        # compute BB-overloading window size
        reserve_cap = 0
        l = min(self.k, len(self.backup_list))
        for i in range(l):
            reserve_cap += self.backup_list[i].getHPExecutionTime()

        # reserve reserve_cap units of backup slots
        self.backup_start = max(sim_time, self.frame - reserve_cap)

    def print_schedule(self):
        """
        Print the generated schedule to the console log.
        """
        print("Schedule:")
        print(" Primary Tasks")
        for key in self.pri_schedule.keys():
            print("  {0} ms: LP Core, Task {1}".format(key, self.pri_schedule[key].getId()))

        print(" Backup Tasks")
        print("  Start: {0} ms".format(self.backup_start))

    def simulate(self, lp_cores, hp_core):
        """
        Simulate the execution of the tasks. The high-level steps:
        1. 

        lp_cores: list of references to the LP Core objects in the System.
        hp_core: reference to the HP Core object in the System.
        """
        sim_time = 0

        # 1. Calculate the times when faults occur
        self.generate_fault_occurrences()

        # 2. Simulate time steps
        lp_assignedTask = None
        hp_assignedTask = None
        key = list(self.pri_schedule.keys())[0]
        keyIdx = 0

        while sim_time <= self.frame:
            # i. increment active durations
            if not lp_assignedTask is None:
                lp_cores[0].update_active_duration(self.time_step)
            if not hp_assignedTask is None:
                hp_core.update_active_duration(self.time_step)

            # ii. if a primary task has completed, unassign it from core
            if not lp_assignedTask is None:
                if sim_time >= lp_assignedTask.getStartTime() + lp_assignedTask.getLPExecutedDuration():
                    # if it is a task that shouldn't have encountered an error
                    if not lp_assignedTask.getEncounteredFault():
                        # iii. remove from backup list
                        self.remove_from_backup_list(lp_assignedTask.getId(), sim_time)
                        # if its backup task is already executing and it completed (i.e. did not encounter a fault), cancel the backup task
                        if not hp_assignedTask is None and hp_assignedTask.getId() == lp_assignedTask.getId():
                            hp_assignedTask = None

                    # unassign from core
                    lp_assignedTask = None

            # iv. if a backup task has completed, remove it from backup core
            if not hp_assignedTask is None:
                if self.backup_list and sim_time >= hp_assignedTask.getBackupStartTime() + hp_assignedTask.getHPExecutionTime():
                    #remove from backup list
                    self.remove_from_backup_list(hp_assignedTask.getId(), sim_time)

                    # unassign from backup core
                    hp_assignedTask = None

            # v. update primary task assignment to cores
            while (keyIdx < len(self.pri_schedule)) and (sim_time >= key):
                # it actually completed execution, but floating point's a bitch
                if not lp_assignedTask is None and lp_assignedTask.getId() != self.pri_schedule[key].getId():
                    # if it is a task that shouldn't have encountered an error
                    if not lp_assignedTask.getEncounteredFault():
                        # iii. remove from backup list
                        self.remove_from_backup_list(lp_assignedTask.getId(), sim_time)
                        # if its backup task is already executing and it completed (i.e. did not encounter a fault), cancel the backup task
                        if hp_assignedTask is not None and hp_assignedTask.getId() == lp_assignedTask.getId():
                            hp_assignedTask = None

                if lp_assignedTask is None or lp_assignedTask.getId() != self.pri_schedule[key].getId():
                    lp_assignedTask = self.pri_schedule[key]
                    lp_assignedTask.setStartTime(sim_time)

                keyIdx += 1
                if keyIdx >= len(self.pri_schedule):
                    key = None
                else:
                    key = list(self.pri_schedule.keys())[keyIdx]


            # vi. update task assignment to backup core
            if sim_time >= self.backup_start:
                if self.backup_list:
                    # task hasn't started on backup core yet
                    if hp_assignedTask is None or hp_assignedTask.getId() != self.backup_list[0].getId():
                        hp_assignedTask = self.backup_list[0]
                        hp_assignedTask.setBackupStartTime(sim_time)
                else:
                    hp_assignedTask = None

            sim_time += self.time_step                

        # 3. Calculate energy consumption of the system from active/idle durations
        for lpcore in lp_cores:
            # i. calculate active energy consumption for this core
            active = lpcore.get_active_duration()
            activeConsumption = lpcore.energy_consumption_active(active)
            lpcore.update_energy_consumption(activeConsumption)
            # ii. calculate idle energy consumption for this core
            idleConsumption = lpcore.energy_consumption_idle(self.frame - active)
            lpcore.update_energy_consumption(idleConsumption)
        
        # iii. calculate active energy consumption for HP core
        hp_activeConsumption = hp_core.energy_consumption_active(hp_core.get_active_duration())
        hp_core.update_energy_consumption(hp_activeConsumption)
        # iv. calculate idle energy consumption for HP core
        hp_idleConsumption = hp_core.energy_consumption_idle(self.frame - hp_core.get_active_duration())
        hp_core.update_energy_consumption(hp_idleConsumption)
        

    def generate_fault_occurrences(self):
        """
        Generate the times at which faults will occur, and mark the affected tasks to have encountered a fault.
        k faults will be generated. It is assumed that each task can only encounter one fault.
        If the number of tasks is smaller than k, then a fault will be generated for all tasks.

        The procedure for generating a fault:
        1. Randomly sample a discrete time step within the frame.
        2. Convert the discrete time step into the actual simulation time.
        3. Check if the generated fault time is valid, by seeing if it occurs during the execution time of a task, and the task is not already marked to have encountered a fault.
        4. If the generated fault time is not valid, repeat steps 1-3.
        5. Repeat steps 1-4 for k times or number of tasks, whichever is smaller.
        """
        #  randomly generate the time occurrence of k faults
        fault_times = []
        faulty_tasks = []
        l = min(self.k, len(self.pri_schedule))
        for i in range(l):
            # randomly choose a time for the fault to occur
            fault_time = None
            # randomly generate until a valid fault_time for fault to occur is obtained
            while fault_time is None:
                # randomly generate a time for the fault to occur
                rand = random.randint(0, self.frame / self.time_step)   # randint [0, self.frame / self.time_step) generates the random timestep it occurs
                fault_time = self.time_step * rand  # get the actual time of the fault in ms
                # check if time step is valid
                for key in self.pri_schedule.keys():
                    task = self.pri_schedule[key]
                    if fault_time >= key and fault_time < key + task.getLPExecutionTime():
                        # if task already has a fault, skip it
                        if task.getEncounteredFault():
                            fault_time = None
                            break
                        else:
                            # calculate the time step where fault occurred relative to the task start time
                            relative_fault_time = fault_time - key
                            # mark task as having a fault
                            task.setEncounteredFault(relative_fault_time)

                            # add it to list of time steps that a fault occurs
                            fault_times.append(fault_time)
                            faulty_tasks.append(task.getId())
                            break

                    elif fault_time < key:    # the fault_time does not overlap with execution time of any task
                        print("There's probably a potential bug, since you have encountered this branch, which you shouldn't for FEST.")
                        break
                else:   # the time step is after all the tasks arranged
                    fault_time = None

        return faulty_tasks