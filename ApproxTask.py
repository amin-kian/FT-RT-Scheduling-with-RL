class ApproxTask(Task):
    def __init__(self, id, lp_manExecTime, hp_manExecTime, lp_optExecTime, hp_optExecTime, deadline):
        Task.__init__(self, id, lp_manExecTime, hp_manExecTime)

        # for EnSuRe
        self.deadline = deadline
        self.lp_optExecTime = lp_optExecTime
        self.hp_optExecTime = hp_optExecTime

        # calculate execution rate demand, i.e. weight
        self.weight = lp_manExecTime / deadline

        # temp value, will be set for each time window
        self.workload_quota = 0

        # internal counter to check if task would be completed
        self.taskCompletion

    def getDeadline(self):
        return self.deadline

    def getWeight(self):
        return self.weight

    def getWorkloadQuota(self):
        return self.workload_quota

    def setWorkloadQuota(self, wq):
        self.workload_quota = wq

    def hasTaskCompleted(self):
        return True