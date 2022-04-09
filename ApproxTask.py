from Task import Task

class ApproxTask(Task):
    def __init__(self, id, lp_manExecTime, hp_manExecTime, lp_optExecTime, hp_optExecTime, deadline):
        Task.__init__(self, id, lp_manExecTime, hp_manExecTime)

        # for EnSuRe
        self.deadline = deadline
        self.lp_optExecTime = lp_optExecTime
        self.hp_optExecTime = hp_optExecTime

        # calculate execution rate demand, i.e. weight
        self.weight = lp_manExecTime / deadline

        # will be appended to in each time window
        self.workload_quota = []
        self.backup_workload_quota = []

    def getDeadline(self):
        return self.deadline

    def getWeight(self):
        return self.weight

    def getWorkloadQuota(self, idx):
        return self.workload_quota[idx]

    def getWorkloadQuota(self, idx):
        return self.workload_quota[idx]

    def getBackupWorkloadQuota(self, idx):
        return self.backup_workload_quota[idx]

    def setWorkloadQuota(self, wq):
        self.workload_quota.append(wq)
        
    def setBackupWorkloadQuota(self, bwq):
        self.backup_workload_quota.append(bwq)