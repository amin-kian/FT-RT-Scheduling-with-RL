import simpy
import random

'''
In the paper:
- Assumes TIbe to be negligible
- The following energy consumption variables are equal for all tasks: ai (switching frequency), xi (freq-independent power consumption)
'''
class Core:
    def __init__(self, name, isLP, ai, f, xi, p_idle):
        self.name = name
        self.energy_consumed = 0    # stores how much energy this core has consumed

        # whether this core is an LP or HP core
        self.isLPCore = isLP

        # energy model parameters
        self.ai = ai
        self.f = f
        self.xi = xi
        self.p_idle = p_idle
        
        # probability of fault occurring per unit time when core is active
        self.p = 0.01

        # runtime state
        self.active = False # whether core is active (i.e. processing) or not

        # for handle execution of task process
        self.task = None
        self.assignedTask = False
        self.taskProcess = None

    def run(self, env, step, scheduler):
        print("{0} start".format(self.name))
        while True:
            try:
                if self.assignedTask:
                    # execute task
                    self.taskProcess = env.process(self.task.execute(env, self.isLPCore, scheduler))
                    print("{0}: CORE: Task {1} execution begun".format(env.now, self.task.getId()))
                    self.assignedTask = False
                    self.active = True

                if self.active:
                    # calculate odds of encountering fault
                    if self.isLPCore:   # only LP cores cannot encounter faults
                        faultRng = random.uniform(0, 1)
                        if faultRng < self.p:
                            print("{0}: CORE: FAULT ENCOUNTERED!! in {1}".format(env.now, self.name))
                            # interrupt the task
                            self.taskProcess.interrupt()
                            self.active = False
                    # else, check if execution completed
                    if not self.taskProcess.is_alive:
                        print("{0}: CORE: Task {1} execution completed, {2} leaving active state".format(env.now, self.task.getId(), self.name))
                        self.active = False

                    # calculate and add power consumption
                    self.energy_consumed += self.energy_consumption_active(step)

                else:
                    self.energy_consumed += self.energy_consumption_idle(step)

                yield env.timeout(step)
            except simpy.Interrupt:
                print("{0}: CORE: {1} execution stopped".format(env.now, self.name))


    def schedule_task(self, env, task):
        self.assignedTask = True
        self.task = task
        print("{0}: CORE: {1} has been assigned task {2}".format(env.now, self.name, task.getId()))

    def energy_consumption_active(self, step):
        return (self.ai * self.f*self.f*self.f + self.xi) * step

    def energy_consumption_idle(self, step):
        return self.p_idle * step

    def is_busy(self):
        if self.taskProcess is None:
            return False
        return self.taskProcess.is_alive

    def get_energy_consumed(self):
        return self.energy_consumed