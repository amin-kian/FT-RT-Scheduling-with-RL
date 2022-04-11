from Task import Task

class ApproxTask(Task):
    """
    Class which represents an independent task item with their own deadlines for an approximation-based system.
    Inherits from the base class Task to implement additional functionalities for custom task deadline and approximation-based features.
    """
    def __init__(self, id, lp_manExecTime, hp_manExecTime, lp_optExecTime, hp_optExecTime, deadline):
        """
        Class constructor (__init__).

        id: the task id
        lpExecTime: the execution time of the mandatory task component on a LP Core
        hpExecTime: the execution time of the mandatory task component on a HP Core
        lp_optExecTime: the execution time of the optional task component on a LP Core
        hp_optExecTime: the execution time of the optional task component on a HP Core
        deadline: the task deadline (in ms)
        """
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

        self.startTime = 0

    def setStartTime(self, startTime):
        self.startTime = startTime

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

    def resetEncounteredFault(self):
        # reset the encounteredFault flag
        self.encounteredFault = False
        self.completed = False

    def setEncounteredFault(self, idx, faultOccurredTime):
        """
        faultOccurredTime: relative to the start time of the primary copy of this task
        """
        # set the encounteredFault flag
        self.encounteredFault = True
        # set the new execution times for the task
        self.workload_quota[idx] = self.workload_quota[idx] - faultOccurredTime
        self.lpExecutedDuration = self.workload_quota[idx]
        self.hpExecutedDuration = self.backup_workload_quota[idx]
