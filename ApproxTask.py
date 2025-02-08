from Task import Task

class ApproxTask(Task):
    """
    Class which represents an independent task item with their own deadlines for an approximation-based system.
    Inherits from the base class Task to implement additional functionalities for custom task deadline and approximation-based features.
    """
    def __init__(self, id, lp_manExecTime, hp_manExecTime, deadline):
        """
        Class constructor (__init__).

        id: the task id
        lpExecTime: the execution time of the mandatory task component on a LP Core
        hpExecTime: the execution time of the mandatory task component on a HP Core
        lp_optExecTime: the execution time of the optional task component on a LP Core (not used)
        hp_optExecTime: the execution time of the optional task component on a HP Core (not used)
        deadline: the task deadline (in ms)
        """
        Task.__init__(self, id, lp_manExecTime, hp_manExecTime)

        # for EnSuRe
        self.deadline = deadline


        # calculate execution rate demand, i.e. weight
        self.weight = lp_manExecTime / deadline

        # will be appended to in each time window
        self.workload_quota = []
        self.backup_workload_quota = []

    def getDeadline(self):
        """
        Get the task deadline.
        """
        return self.deadline

    def getWeight(self):
        """
        Get the task weight, which is defined as ((mandatory execution time) / deadline).
        """
        return self.weight

    def getWorkloadQuota(self, idx):
        """
        Get the task workload-quota for a time-window, which is defined as (weight * time-window).

        idx: Which time-window to get the workload-quota of
        """
        return self.workload_quota[idx]

    def getBackupWorkloadQuota(self, idx):
        """
        Get the task's backup workload-quota for a time-window.

        idx: Which time-window to get the workload-quota of
        """
        return self.backup_workload_quota[idx]

    def setWorkloadQuota(self, wq):
        """
        Add a newly computed task's workload-quota to the list of workload-quotas.

        wq: the newly computed workload-quota
        """
        self.workload_quota.append(wq)
        
    def setBackupWorkloadQuota(self, bwq):
        """
        Add a newly computed backup task's workload-quota to the list of backup workload-quotas.

        wq: the newly computed backup workload-quota
        """
        self.backup_workload_quota.append(bwq)

    def resetEncounteredFault(self):
        """
        Reset for a new time-window whether the task encountered a fault.
        """
        # reset the encounteredFault flag
        self.encounteredFault = False

    def setEncounteredFault(self, idx, faultOccurredTime):
        """
        Set that the task would be encountering a fault.

        faultOccurredTime: relative to the start time of the primary copy of this task
        """
        # set the encounteredFault flag
        self.encounteredFault = True
        # set the new execution times for the task
        self.workload_quota[idx] = self.workload_quota[idx] - faultOccurredTime
        self.lpExecutedDuration = self.workload_quota[idx]
        self.hpExecutedDuration = self.backup_workload_quota[idx]
