class Task:
    """
    Class which represents an independent task item.
    """
    def __init__(self, id, lp_execTime, hp_execTime):
        """
        Class constructor (__init__).

        id: the task id
        lpExecTime: the execution time of this task on a LP Core
        hpExecTime: the execution time of this task on a HP Core
        """
        self.id = id
        self.lpExecTime = lp_execTime
        self.hpExecTime = hp_execTime

        # results about the completion of the task
        self.completionTime = 0
        # whether this task encountered a fault occurring
        self.encounteredFault = False
        # how much time this task spent executing on the LP/HP core
        # (by default, it would execute for lp_execTime on the LP core unless a fault occurred)
        # (execution time on hp_execTime depends on task overlap, which cannot be determined until schedule is generated)
        self.lpExecutedDuration = lp_execTime
        self.hpExecutedDuration = 0

        self.start_time = 0
        self.backup_start_time = 0
        self.completed = False

    def getId(self):
        """
        Get this task's id.
        """
        return self.id

    def getLPExecutionTime(self):
        """
        Get the execution time of this task on a LP Core.
        """
        return self.lpExecTime
    
    def getHPExecutionTime(self):
        """
        Get the execution time of this task on a HP Core.
        """
        return self.hpExecTime

    def getCompletionTime(self):
        """
        Get the time this task completes.
        """
        return self.completionTime

    def getLPExecutedDuration(self):
        """
        Get the actual time this task executed on an LP core.
        """
        return self.lpExecutedDuration
        
    def getHPExecutedDuration(self):
        """
        Get the actual time this task executed on the HP core.
        """
        return self.hpExecutedDuration

    def getStartTime(self):
        """
        Get the time this task started executing on the LP core.
        """
        return self.start_time
        
    def getBackupStartTime(self):
        """
        Get the time this task started executing on the backup (HP) core.
        """
        return self.backup_start_time
        
    def setEncounteredFault(self, faultOccurredTime):
        """
        Set that the task would be encountering a fault.

        faultOccurredTime: relative to the start time of the primary copy of this task
        """
        # set the encounteredFault flag
        self.encounteredFault = True
        # set the new execution times for the task
        self.lpExecutedDuration = self.lpExecTime - faultOccurredTime
        self.hpExecutedDuration = self.hpExecTime

    def setStartTime(self, startTime):
        """
        Set the start time of the task, i.e. the time at which the task begins execution on the LP core.
        """
        self.start_time = startTime
        
    def setBackupStartTime(self, backupStartTime):
        """
        Set the start time of the task, i.e. the time at which the task begins execution on the backup (HP) core.
        """
        self.backup_start_time = backupStartTime

    def setCompletionTime(self, completionTime):
        """
        Set the completion time of the task, i.e. the time at which the task completes.

        completionTime: completion time of the task
        """
        self.completionTime = completionTime
        self.completed = True

    def setHPExecutedDuration(self, duration):
        """
        Set the duration that the HP core has executed for.
        This method is only necessary when the execution of the primary task overlaps with its backup copy.
        """
        self.hpExecutedDuration = duration
    
    def getEncounteredFault(self):
        """
        Get whether the task encountered a fault during its execution.
        Since the simulation works by determining the occurrence of faults beforehand, this method returns whether the task is due to encounter a fault in this frame/time-window.
        """
        return self.encounteredFault