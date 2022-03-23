import simpy

class Task:
    def __init__(self, id, lp_execTime, hp_execTime):
        self.id = id
        self.lpExecTime = lp_execTime
        self.hpExecTime = hp_execTime

    def getId(self):
        return self.id

    def getLPExecutionTime(self):
        return self.lpExecTime
    
    def getHPExecutionTime(self):
        return self.hpExecTime

    def execute(self, env, isLP, scheduler):
        print("{0}: TASK: Task {1} started on {2} core".format(env.now, self.id, ("LP" if isLP else "HP") ))
        print("TASK: {0} exec seconds".format(self.lpExecTime if isLP else self.hpExecTime))
        try:
            yield env.timeout(self.lpExecTime if isLP else self.hpExecTime)
            print("{0}: TASK: Task {1} completed successfully".format(env.now, self.id))
            # update scheduler on this task's completion
            scheduler.task_completed(self)

        except simpy.Interrupt: # interrupted by core
            print("{0}: TASK: Task {1} encountered a fault".format(env.now, self.id))