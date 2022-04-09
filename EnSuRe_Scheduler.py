import math

class EnSuRe_Scheduler:
    # init
    def __init__(self, k, frame, time_step, log_debug):
        """
        k: number of faults the system can support
        frame: size of the frame, in ms
        time_step: fidelity of each time step for the scheduler/task execution times, in ms
        log_debug: whether to print logging statements
        """
        # application parameters
        self.k = k
        self.frame = frame  # total duration
        self.time_step = time_step

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
        return task.getWorkloadQuota()

    def update_BB_overloading(self, idx):
        # compute BB-overloading window size
        reserve_cap = 0
        l = min(self.k, len(self.backup_list[idx]))
        for i in range(l):
            reserve_cap += self.backup_list[idx][i].getHPExecutionTime()    # TODO PROBLEM: should schedule only the WQ?

        # reserve reserve_cap units of backup slots
        new_backup_start = self.deadlines[idx] - reserve_cap
        if len(self.backup_start) < idx:
            self.backup_start.append(new_backup_start)
        else:
            self.backup_start[idx] = new_backup_start


    # Function to generate schedule
    def generate_schedule(self, tasksList, m_pri):
        # 1. Sort tasks in increasing order of deadlines to obtain deadline sequence
        tasksList.sort(reverse=False, key=EnSuRe_Scheduler.getTaskDeadline)
        self.deadlines = [task.getDeadline() for task in tasksList]

        # 2. In each time window, schedule primary tasks onto the LP core
        for i in range(len(self.deadlines)): # each task in the list is the next deadline
            # i. calculate time window
            if i == 0:  # first deadline
                time_window = self.deadlines[i]
            else:
                time_window = self.deadlines[i] - self.deadlines[i-1]

            # ii. for each task, calculate workload-quota
            total_wq = 0
            for task in tasksList:
                wq = math.ceil(task.getWeight() * time_window)
                task.setWorkloadQuota(wq)
                total_wq += wq
            
            # iii. check if system-wide capacity >= total workload-quota for all running tasks
            if total_wq <= time_window * m_pri: # equation satisfied, feasible schedule

                # iv. execute tasks in the primary cores as per workload-quota
                tasksA = tasksList.copy()
                tasksA.sort(reverse=False, key=EnSuRe_Scheduler.getTaskWQ)
                # keep track of cores' schedules
                currPriCore = 0
                pri_cores = [0] * m_pri
                for t in tasksA:
                    lp_executionTime = t.getWorkloadQuota()
                    # attempt to schedule onto this core
                    if pri_cores[currPriCore] + lp_executionTime > time_window: # cannot be scheduled onto this core
                        # go to another core
                        currPriCore += 1
                        if currPriCore >= m_pri:
                            currPriCore = 0

                    # schedule onto this core
                    self.pri_schedule[(pri_cores[currPriCore], currPriCore)] = task
                    pri_cores[currPriCore] += lp_executionTime

                    # v. remove task from tasksList if workload-quota completes
                    if t.hasTaskCompleted():
                        for t_toRemove in tasksList:
                            if t_toRemove.getId() == t.getId():
                                tasksList.remove(t_toRemove)
                                break

                # vi. calculate t_slack (start of slack time) and available slack for each core
                available_slack = [0] * m_pri
                t_slack = pri_cores[0]
                for i in range(m_pri):
                    available_slack[i] = pri_cores[i]
                    if pri_cores[i] < t_slack:
                        t_slack = pri_cores[i]

                # vii. calculate urgency factor of tasks - actually, this is the same as the sorted task list, right?

                # viii. schedule optional portion of the task

                # ix. create backup list
                tempList = tasksList.copy()
                tempList.sort(reverse=True, key=EnSuRe_Scheduler.getHPExecutionTime)
                self.backup_list.append(tempList)

                # x. compute BB-overloading window size
                self.update_BB_overloading(i)
                

            else:   ## if not schedulable, exit
                print("Unable to schedule tasks")
                return False

        # Generated schedule successfully
        return True