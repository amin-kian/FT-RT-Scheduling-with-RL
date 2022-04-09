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
        self.backup_list.sort(reverse=True, key=FEST_Scheduler.getHPExecutionTime)

        # 4. Compute BB-overloading window size
        self.update_BB_overloading()

        # Generated schedule successfully
        return True

    def remove_from_backup_list(self, taskId):
        """
        Given a task id, remove its corresponding task from the backup_list.
        To be called when a task (either its primary or backup copy) completes execution successfully.

        taskId: id of the task to be removed
        """
        # remove task from backup list
        self.backup_list = [i for i in self.backup_list if i.getId() != taskId]
        # update size of BB-overloading window
        self.update_BB_overloading()

    def update_BB_overloading(self):
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
        self.backup_start = self.frame - reserve_cap

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
        # 1. Calculate the times when faults occur
        self.generate_fault_occurrences()

        # 2. "Simulate" execution/completion times of the tasks (take note of overlapping with backup core)
        num_faults_left = min(self.k, len(self.pri_schedule))
        for key in self.pri_schedule.keys(): # in sequence of execution start time

            curr_time = key     # the curr "simulation" time
            task = self.pri_schedule[key]    # reference to task

            # 0. at this time step, check if curr_time is greater than the completion time of a backup task, to update backup_list and BB-overloading window
            if curr_time > self.backup_start:   # we are within a backup execution time, proceed to further checks
                while curr_time > self.backup_start + self.backup_list[0].getHPExecutionTime(): # the backup task of a faulty task has completed
                    # NOTE: backup core's active duration for this task already accounted for when the task fails
                    # update backup execution list
                    self.remove_from_backup_list(self.backup_list[0].getId())

                    # TEMP: just a checker
                    num_faults_left -= 1

            # 1. work on primary task
            # i. update active duration for the execution time on LP core
            lp_cores[0].update_active_duration(task.getLPExecutedDuration())
            #lp_energy = lp_cores[0].energy_consumption_active(task.getLPExecutedDuration())
            #lp_cores[0].update_energy_consumption(lp_energy)

            # if task encountered fault, updating energy consumption for HP core is straightforward
            if task.getEncounteredFault():
                # ii. update active duration for the execution time on HP core
                # NOTE: removing from backup_list will only be done in a time step after this
                hp_core.update_active_duration(task.getHPExecutedDuration())
                #hp_energy = hp_core.energy_consumption_active(task.getHPExecutedDuration())
                #hp_core.update_energy_consumption(hp_energy)


            # else, check for overlap with backup execution
            else:
                # set the time the task completes
                completion_time = curr_time + task.getLPExecutedDuration()
                if self.log_debug:
                    print("Completion time: {0}".format(completion_time))
                task.setCompletionTime(completion_time)
                # check if task's primary copy has overlap with backup copy
                if completion_time >= self.backup_start:    # if the task completes after backup_start, there is a chance of overlap
                    # get start time of task's backup copy to calculate the overlap
                    backup_start_time = self.backup_start
                    for backup_copy in self.backup_list:
                        if task.getId() == backup_copy.getId():
                            break
                        else:
                            backup_start_time += backup_copy.getHPExecutionTime()

                    # check for overlap
                    if completion_time > backup_start_time:  # there is an overlap
                        backup_overlap = completion_time - backup_start_time     # calculate the overlap duration
                        # i. set the amount of time HP spends on this task as the overlap execution time
                        task.setHPExecutedDuration(backup_overlap)
                        # ii. update active duration for the execution time on HP core
                        hp_core.update_active_duration(backup_overlap)
                        #hp_energy = hp_core.energy_consumption_active(backup_overlap)
                        #hp_core.update_energy_consumption(hp_energy)

                # update backup execution list
                self.remove_from_backup_list(task.getId())

        # TEMP: just to check that tasks completed successfully
        if num_faults_left > 0:
            if num_faults_left < len(self.backup_list):
                print("Faults were not resolved properly. num_faults = {0}, backup_list length = {1}".format(num_faults_left, len(self.backup_list)))
            elif num_faults_left > len(self.backup_list):
                print("Some tasks cannot finish executing.")
            else:   # it is fine
                self.backup_list.clear()

        # 3. Calculate energy consumption of the system from active/idle durations
        for lpcore in lp_cores:
            # i. calculate active energy consumption for this core
            activeConsumption = lpcore.energy_consumption_active(lpcore.get_active_duration())
            lpcore.update_energy_consumption(activeConsumption)
            # ii. calculate idle energy consumption for this core
            idleConsumption = lpcore.energy_consumption_idle(self.frame - lpcore.get_active_duration())
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
                            break

                    elif fault_time < key:    # the fault_time does not overlap with execution time of any task
                        print("There's probably a potential bug, since you have encountered this branch, which you shouldn't for FEST.")
                        break
                else:   # the time step is after all the tasks arranged
                    fault_time = None