import math
import copy

class EnSuRe_Scheduler:
    # init
    def __init__(self, k, frame, time_step, m_pri, lp_hp_ratio, log_debug):
        """
        k: number of faults the system can support
        frame: size of the frame, in ms
        time_step: fidelity of each time step for the scheduler/task execution times, in ms
        m_pri: number of primary (LP) cores
        log_debug: whether to print logging statements
        """
        # application parameters
        self.k = k
        self.frame = frame  # total duration
        self.time_step = time_step

        self.precision_dp = -round(math.log(self.time_step, 10))

        # system parameters
        self.m_pri = m_pri  # no. primary cores
        self.lp_hp_ratio = lp_hp_ratio  # LP:HP speed ratio

        # scheduler variables
        self.pri_schedule = dict()
        self.deadlines = None   # an array of the task deadlines, ordered in increasing order
        self.backup_start = []  # an array of backup start times, one per time window
        self.backup_list = []   # an array of backup lists, one list per time window

        # logging
        self.log_debug = log_debug  # whether to print log statements or not

    # class helper functions
    def getLPExecutionTime(task):
        return task.getLPExecutionTime()
    
    def getHPExecutionTime(task):
        return task.getHPExecutionTime()

    def getTaskDeadline(task):
        return task.getDeadline()

    def getTaskWQ(task):
        return task.getWorkloadQuota(len(task.workload_quota)-1)

    def roundUpTimeStep(self, value):
        return round(math.ceil(value/self.time_step) * self.time_step, self.precision_dp)

    def update_BB_overloading(self, idx):
        # compute BB-overloading window size
        reserve_cap = 0
        l = min(self.k, len(self.backup_list[idx]))
        print("HI " + str(l))
        for i in range(l):
            reserve_cap += self.backup_list[idx][i].getBackupWorkloadQuota(idx) # NOTE: modification to schedule by backup workload quota

        # reserve reserve_cap units of backup slots
        new_backup_start = self.deadlines[idx] - reserve_cap
        if len(self.backup_start) <= idx:
            self.backup_start.append(new_backup_start)
        else:
            self.backup_start[idx] = new_backup_start

    # Function to generate schedule
    def generate_schedule(self, tasksList):
        # 1. Sort tasks in increasing order of deadlines to obtain deadline sequence
        tasksList.sort(reverse=False, key=EnSuRe_Scheduler.getTaskDeadline)
        self.deadlines = []
        [self.deadlines.append(task.getDeadline()) for task in tasksList if task.getDeadline() not in self.deadlines]   # NOTE: removes duplicate deadlines

        print(self.deadlines)

        # 2. In each time window, schedule primary tasks onto the LP core
        for i in range(len(self.deadlines)): # each task in the list is the next deadline
            # i. calculate time window
            if i == 0:  # first deadline
                time_window = self.deadlines[i]
                start_window = 0
            else:
                time_window = self.deadlines[i] - self.deadlines[i-1]
                start_window = self.deadlines[i-1]

            # ii. for each task, calculate workload-quota
            total_wq = 0
            for task in tasksList:
                wq = self.roundUpTimeStep(task.getWeight() * time_window)
                task.setWorkloadQuota(wq)
                bwq = self.roundUpTimeStep(self.lp_hp_ratio * task.getWeight() * time_window)
                task.setBackupWorkloadQuota(bwq)
                total_wq += wq
            
            # iii. check if system-wide capacity >= total workload-quota for all running tasks
            if total_wq <= time_window * self.m_pri: # equation satisfied, feasible schedule

                # iv. execute tasks in the primary cores as per workload-quota
                tasksA = copy.deepcopy(tasksList)
                tasksA.sort(reverse=True, key=EnSuRe_Scheduler.getTaskWQ)
                # keep track of cores' schedules
                currPriCore = 0
                pri_cores = [start_window] * self.m_pri
                for t in tasksA:
                    lp_executionTime = t.getWorkloadQuota(i)
                    # attempt to schedule onto this core
                    if pri_cores[currPriCore] + lp_executionTime > start_window + time_window: # cannot be scheduled onto this core
                        # go to another core
                        currPriCore += 1
                        if currPriCore >= self.m_pri:
                            currPriCore = 0

                    # schedule onto this core
                    self.pri_schedule[(pri_cores[currPriCore], currPriCore)] = t
                    pri_cores[currPriCore] += lp_executionTime

                    # v. remove task from tasksList if workload-quota completes
                    if self.deadlines[i] == t.getDeadline():    # true if task would be completed in this time window
                        for t_toRemove in tasksList:
                            if t_toRemove.getId() == t.getId():
                                tasksList.remove(t_toRemove)
                                break

                # vi. calculate t_slack (start of slack time) and available slack for each core
                available_slack = [0] * self.m_pri
                t_slack = pri_cores[0]
                for m in range(self.m_pri):
                    available_slack[m] = pri_cores[m]
                    if pri_cores[m] < t_slack:
                        t_slack = pri_cores[m]

                # vii. calculate urgency factor of tasks - actually, this is the same as the sorted task list, right?

                # viii. schedule optional portion of the task

                # ix. create backup list
                tempList = tasksA.copy()    # NOTE: taskA is used as it still contains the task that would get completed in this time window
                tempList.sort(reverse=True, key=EnSuRe_Scheduler.getTaskWQ) # NOTE: modification to schedule by backup workload quota
                self.backup_list.append(tempList)

                # x. compute BB-overloading window size
                self.update_BB_overloading(i)
                

            else:   ## if not schedulable, exit
                print("Unable to schedule tasks")
                return False

        # Generated schedule successfully
        return True

    def print_schedule(self):
        print("Schedule:")
        #for i in range(len(self.deadlines)): # each task in the list is the next deadline 
        print(" Primary Tasks")
        for key in self.pri_schedule.keys():
            print("  LP Core {0}, {1} ms, Task {2}".format(key[1], key[0], self.pri_schedule[key].getId()))

        print(" Backup Tasks")
        for i in range(len(self.deadlines)): # each task in the list is the next deadline 
            print("  For time window {0}: {1} ms".format(i, self.backup_start[i]))
