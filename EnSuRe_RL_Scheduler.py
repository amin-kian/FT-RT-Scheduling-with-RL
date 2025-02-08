import math
import copy
import random
from stable_baselines3 import DQN  # You can use PPO if needed
import numpy as np

class EnSuRe_RL_Scheduler:
    # Init method with model integration
    def __init__(self, k, frame, time_step, m_pri, lp_hp_ratio, log_debug):
        """
        Class constructor (__init__).

        k: number of faults the system can support
        frame: size of the frame, in ms
        time_step: fidelity of each time step for the scheduler/task execution times, in ms
        m_pri: number of primary (LP) cores
        log_debug: whether to print logging statements
        model_path: path to the pre-trained model (DQN, PPO)
        """
        # Application parameters
        self.k = k
        self.frame = frame  # Total duration
        self.time_step = time_step
        self.precision_dp = -round(math.log(self.time_step, 10))

        # System parameters
        self.m_pri = m_pri  # Number of primary cores
        self.lp_hp_ratio = lp_hp_ratio  # LP:HP speed ratio

        # Scheduler variables
        self.pri_schedule = dict()
        self.deadlines = None   # Array of task deadlines
        self.backup_start = []  # Backup start times for each time window
        self.backup_list = []   # Backup task lists for each time window

        # Logging
        self.log_debug = log_debug  # Whether to print log statements or not

        model_path = 'dqn_ensure_model.zip'
        # Model loading if provided
        if model_path:
            self.model = DQN.load(model_path)  # Load the pre-trained model
        else:
            self.model = None  # No RL model for classic scheduling

    # Helper functions
    def getTaskDeadline(self, task):
        """Helper function for sorting tasks by deadlines."""
        return task.getDeadline()

    def getTaskWQ(self, task):
        """Helper function for sorting tasks by workload-quota."""
        return task.getWorkloadQuota(len(task.workload_quota)-1)

    def roundUpTimeStep(self, value):
        """Round a given value up to the nearest time step."""
        out = round(math.ceil(value/self.time_step) * self.time_step, self.precision_dp)
        if out < self.time_step:
            out = self.time_step
        return out

    def remove_from_backup_list(self, idx, taskId, sim_time):
        """Remove task from backup list when it completes execution."""
        self.backup_list[idx] = [b for b in self.backup_list[idx] if b.getId() != taskId]
        self.update_BB_overloading(idx, sim_time)

    def update_BB_overloading(self, idx, sim_time):
        """Update backup start time with the new size of the BB-overloading window."""
        reserve_cap = 0
        l = min(self.k, len(self.backup_list[idx]))
        for z in range(l):
            reserve_cap += self.backup_list[idx][z].getBackupWorkloadQuota(idx)
        new_backup_start = self.deadlines[idx] - reserve_cap
        if len(self.backup_start) <= idx:
            self.backup_start.append(new_backup_start)
        else:
            self.backup_start[idx] = max(sim_time, new_backup_start)

    def extract_state(self, tasksList, sim_time):
        """Extract the state to feed into the RL model."""
        state = []
        for task in tasksList:
            state.append([task.getDeadline(), task.getWeight(), task.getWorkloadQuota(sim_time)])
        state.append([self.m_pri, sim_time])  # Add core count and simulation time
        return np.array(state)  # Convert to a numpy array

    def schedule_task(self, tasksList, sim_time):
        """Use the RL model to decide which core to assign the task to."""
        if self.model:  # If the model is loaded
            state = self.extract_state(tasksList, sim_time)
            action, _states = self.model.predict(state)
        else:
            # Classic logic (if no model is loaded)
            action = 0  # Assign task to LP core (classic logic)

        if action == 0:  # LP core
            core_type = "LP"
            execution_time = tasksList[0].getLPExecutionTime()
        else:  # HP core
            core_type = "HP"
            execution_time = tasksList[0].getHPExecutionTime()

        self.pri_schedule[sim_time] = (core_type, execution_time)

    def generate_schedule(self, tasksList):
        """Generate the schedule using RL-based decision-making."""
        tasksList.sort(reverse=False, key=self.getTaskDeadline)
        self.deadlines = []
        [self.deadlines.append(task.getDeadline()) for task in tasksList if task.getDeadline() not in self.deadlines]

        for i in range(len(self.deadlines)):
            time_window = self.deadlines[i] if i == 0 else self.deadlines[i] - self.deadlines[i-1]
            start_window = self.deadlines[i-1] if i > 0 else 0

            total_wq = 0
            for task in tasksList:
                wq = self.roundUpTimeStep(task.getWeight() * time_window)
                task.setWorkloadQuota(wq)
                bwq = self.roundUpTimeStep(self.lp_hp_ratio * task.getWeight() * time_window)
                task.setBackupWorkloadQuota(bwq)
                total_wq += wq

            if total_wq <= time_window * self.m_pri:
                tasksA = copy.deepcopy(tasksList)
                tasksA.sort(reverse=True, key=self.getTaskWQ)
                currPriCore = 0
                pri_cores = [start_window] * self.m_pri
                self.pri_schedule[i] = {}
                for t in tasksA:
                    lp_executionTime = t.getWorkloadQuota(i)
                    counter = 0
                    while pri_cores[currPriCore] + lp_executionTime > start_window + time_window:
                        currPriCore += 1
                        if currPriCore >= self.m_pri:
                            currPriCore = 0
                        counter += 1
                        if counter > self.m_pri:
                            print("Unable to schedule tasks when trying to assign to LP cores")
                            return False

                    self.schedule_task(tasksA, i)  # Use the model to schedule the task
                    pri_cores[currPriCore] += lp_executionTime
                    currPriCore += 1
                    if currPriCore >= self.m_pri:
                        currPriCore = 0

                self.pri_schedule[i] = dict(sorted(self.pri_schedule[i].items(), key=lambda key: key[0]))

                tempList = tasksA.copy()
                self.backup_list.append(tempList)
                self.update_BB_overloading(i, 0)

            else:
                print("Unable to schedule tasks, WQ < time_window")
                return False

        return True

    def print_schedule(self):
        """Print the generated schedule."""
        print("Schedule:")
        print(" Primary Tasks")
        for i in self.pri_schedule.keys():
            for key in self.pri_schedule[i].keys():
                print(f"  LP Core {key[1]}, {key[0]} ms, Task {self.pri_schedule[i][key].getId()}")

        print(" Backup Tasks")
        for i in range(len(self.deadlines)):
            print(f"  For time window {i}: {self.backup_start[i]} ms")

    def simulate(self, lp_cores, hp_core):
        """Simulate the task execution."""
        sim_time = 0
        for i in range(len(self.deadlines)):
            for t in self.pri_schedule[i].values():
                t.resetEncounteredFault()
            self.generate_fault_occurrences(i)
            lp_assignedTask = [None] * len(lp_cores)
            hp_assignedTask = None
            key = list(self.pri_schedule[i].keys())[0]
            keyIdx = 0
            while sim_time <= self.deadlines[i]:
                for lp in range(len(lp_assignedTask)):
                    if lp_assignedTask[lp] is not None:
                        lp_cores[lp].update_active_duration(self.time_step)
                if hp_assignedTask is not None:
                    hp_core.update_active_duration(self.time_step)
                for lp in range(len(lp_assignedTask)):
                    if lp_assignedTask[lp] is not None:
                        if sim_time >= lp_assignedTask[lp].getStartTime() + lp_assignedTask[lp].getWorkloadQuota(i):
                            if not lp_assignedTask[lp].getEncounteredFault():
                                self.remove_from_backup_list(i, lp_assignedTask[lp].getId(), sim_time)
                                if hp_assignedTask is not None and hp_assignedTask.getId() == lp_assignedTask[lp].getId():
                                    hp_assignedTask = None
                            lp_assignedTask[lp] = None
                if hp_assignedTask is not None:
                    if self.backup_list[i] and sim_time >= hp_assignedTask.getBackupStartTime() + hp_assignedTask.getBackupWorkloadQuota(i):
                        self.remove_from_backup_list(i, hp_assignedTask.getId(), sim_time)
                        hp_assignedTask = None
                while keyIdx < len(self.pri_schedule[i]) and sim_time >= key[0]:
                    if lp_assignedTask[key[1]] is None or lp_assignedTask[key[1]].getId() != self.pri_schedule[i][key].getId():
                        lp_assignedTask[key[1]] = self.pri_schedule[i][key]
                        lp_assignedTask[key[1]].setStartTime(sim_time)
                    keyIdx += 1
                    if keyIdx >= len(self.pri_schedule[i]):
                        key = None
                    else:
                        key = list(self.pri_schedule[i].keys())[keyIdx]
                if sim_time >= self.backup_start[i]:
                    if self.backup_list[i]:
                        if hp_assignedTask is None or hp_assignedTask.getId() != self.backup_list[i][0].getId():
                            hp_assignedTask = self.backup_list[i][0]
                            hp_assignedTask.setBackupStartTime(sim_time)
                    else:
                        hp_assignedTask = None
                sim_time += self.time_step

        for lpcore in lp_cores:
            activeConsumption = lpcore.energy_consumption_active(lpcore.get_active_duration())
            lpcore.update_energy_consumption(activeConsumption)
            idleConsumption = lpcore.energy_consumption_idle(self.frame - lpcore.get_active_duration())
            lpcore.update_energy_consumption(idleConsumption)

        hp_activeConsumption = hp_core.energy_consumption_active(hp_core.get_active_duration())
        hp_core.update_energy_consumption(hp_activeConsumption)
        hp_idleConsumption = hp_core.energy_consumption_idle(self.frame - hp_core.get_active_duration())
        hp_core.update_energy_consumption(hp_idleConsumption)

    def generate_fault_occurrences(self, idx):
        """Generate the fault occurrences for tasks."""
        l = min(self.k, len(self.pri_schedule[idx]))
        if idx == 0:
            time_window = self.deadlines[idx]
            start_window = 0
        else:
            time_window = self.deadlines[idx] - self.deadlines[idx-1]
            start_window = self.deadlines[idx-1]
        fault_times = []
        faulty_tasks = []
        for f in range(l):
            fault_time = None
            while fault_time is None:
                rand = random.randint(0, time_window // self.time_step)
                fault_time = (self.time_step * rand) + start_window
                for key in self.pri_schedule[idx].keys():
                    task = self.pri_schedule[idx][key]
                    if fault_time >= key[0] and fault_time <= key[0] + task.getWorkloadQuota(idx):
                        if not task.getEncounteredFault():
                            relative_fault_time = fault_time - key[0]
                            task.setEncounteredFault(idx, relative_fault_time)
                            fault_times.append(fault_time)
                            faulty_tasks.append(task.getId())
                            break
                else:
                    fault_time = None
        return faulty_tasks
