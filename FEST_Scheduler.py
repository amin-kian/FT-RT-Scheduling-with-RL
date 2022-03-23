class ScheduleItem:
    pass

class FEST_Scheduler:
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

    # Function to generate schedule
    def generate_schedule(self, tasksList):
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

        # 4. Update BB-overloading window
        self.update_BB_overloading()

        # Generated schedule successfully
        return True

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