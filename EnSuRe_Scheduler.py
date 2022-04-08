import math

class EnSuRe_Scheduler:
    # init
    def __init__(self, k, frame):
        # application parameters
        self.k = k
        self.frame = frame

        # scheduler variables
        self.pri_schedule = dict()
        self.backup_start = 0
        self.backup_list = None

    # class helper functions
    def getLPExecutionTime(task):
        return task.getLPExecutionTime()
    
    def getHPExecutionTime(task):
        return task.getHPExecutionTime()

    def getTaskDeadline(task):
        return task.getDeadline()

    def getTaskWQ(task):
        return task.getWorkloadQuota()

    # Function to generate schedule
    def generate_schedule(self, tasksList, m_pri):
        # 1. Sort tasks in increasing order of deadlines to obtain deadline sequence
        tasksList.sort(reverse=False, key=EnSuRe_Scheduler.getTaskDeadline)
        deadlines = [task.getDeadline() for task in tasksList]

        # 2. In each time window, schedule primary tasks onto the LP core
        for i in range(len(deadlines)): # each task in the list is the next deadline
            # i. calculate time window
            if i == 0:  # first deadline
                time_window = deadlines[i]
            else:
                time_window = deadlines[i] - deadlines[i-1]

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
                        start_time = pri_cores[currPriCore]

                    # schedule onto this core
                    self.pri_schedule[(pri_cores[currPriCore], currPriCore)] = task
                    pri_cores[currPriCore] += lp_executionTime

                    # v. remove task from tasksList if workload-quota completes
                    if t.hasTaskCompleted():
                        for t_toRemove in tasksList:
                            if t_toRemove.getId() == t.getId():
                                tasksList.remove(t_toRemove)
                                break

                # vi. calculate available slack on each primary core
                

                # vii. calculate urgency factor of task

                # viii. execute optional portion of task

                # ix. create backup list
                '''
                # 3. Create backup list
                self.backup_list = tasksList.copy()
                self.backup_list.sort(reverse=True, key=FEST_Scheduler.getHPExecutionTime)

                # 4. Update BB-overloading window
                self.update_BB_overloading()
                '''
                
                # x. schedule backup list

            else:   ## if not schedulable, exit
                print("Unable to schedule tasks")
                return False

        # Generated schedule successfully
        return True