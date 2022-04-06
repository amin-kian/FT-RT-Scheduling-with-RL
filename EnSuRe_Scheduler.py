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

    '''
    # Function to recompute BB-overloading window size and reserve execution slots on the backup core
    def update_BB_overloading(self):
        # compute BB-overloading window size
        reserve_cap = 0
        l = min(self.k, len(self.backup_list))
        for i in range(l):
            reserve_cap += FEST_Scheduler.getHPExecutionTime(self.backup_list[i])
        
        # reserve reserve_cap units of backup slots
        self.backup_start = self.frame - reserve_cap
        print(self.backup_start)

    def task_completed(self, task):
        # if backup copy of completed task is currently executing, remove it

        # else, remove task from backup list
        self.backup_list = [i for i in self.backup_list if i.getId() != task.getId()]

        # update BB-overloading window
        self.update_BB_overloading()

    def run(self, env, step, lp_cores, hp_core):
        # start the cores
        cores_active = []
        # start the LP core(s)
        for lp_core in lp_cores:
            cores_active.append( env.process(lp_core.run(env, step, self)) )
        # start the HP core
        cores_active.append( env.process(hp_core.run(env, step, self)) )

        print("{0}: Begin task execution".format(env.now))
        # run for one frame
        while env.now < self.frame:
            time = env.now
            # check if to schedule a primary task
            if time in self.pri_schedule.keys():
                task = self.pri_schedule[time]
                # execute next scheduled primary task
                print("{0}: FEST: Scheduled task {1} for LP core".format(time, task.getId()))
                # assign to LP core
                lp_cores[0].schedule_task(env, task)

            # if time >= BB-overloading window, execute next backup task on list
            if time == self.backup_start and self.backup_list:  # TODO: current PROBLEM, backup_start only updates later on, so the next backup task will not get scheduled
                # execute next backup task on list
                print("{0}: FEST: Execute backup task {1} on HP core".format(env.now, self.backup_list[0].getId()))
                # assign to HP core
                hp_core.schedule_task(env, self.backup_list[0])

            yield env.timeout(step)

        print("{0}: Frame deadline reached".format(env.now))

        # wait an extra step before terminating everything
        yield env.timeout(step)

        # execution completed, stop the cores
        for core in cores_active:
            core.interrupt()

    def print_schedule(self):
        print("Schedule:")
        print(" Primary Tasks")
        for key in self.pri_schedule.keys():
            print("  {0} ms: LP Core, Task {1}".format(key, self.pri_schedule[key].getId()))

        print(" Backup Tasks")
        print("  Start: {0} ms".format(self.backup_start))
    '''