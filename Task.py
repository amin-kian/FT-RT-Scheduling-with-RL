class Task:
    def __init__(self, id, lp_execTime, hp_execTime):
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

    def getId(self):
        return self.id

    def getLPExecutionTime(self):
        return self.lpExecTime
    
    def getHPExecutionTime(self):
        return self.hpExecTime

    def getCompletionTime(self):
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
        
    def setEncounteredFault(self, faultOccurredTime):
        """
        faultOccurredTime: relative to the start time of the primary copy of this task
        """
        # set the encounteredFault flag
        self.encounteredFault = True
        # set the new execution times for the task
        self.lpExecutedDuration = self.lpExecTime - faultOccurredTime
        self.hpExecutedDuration = self.hpExecTime

    def setCompletionTime(self, completionTime):
        self.completionTime = completionTime

    def setHPExecutedDuration(self, duration):
        """
        Set the duration that the HP core has executed for.
        This method is only necessary when the execution of the primary task overlaps with its backup copy.
        """
        self.hpExecutedDuration = duration
    
    def getEncounteredFault(self):
        return self.encounteredFault