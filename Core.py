'''
In the FEST paper:
- Assumes TIbe to be negligible
- The following energy consumption variables are equal for all tasks: ai (switching frequency), xi (freq-independent power consumption)
'''
class Core:
    def __init__(self, name, isLP, ai, f, xi, p_idle):
        self.name = name
        self.energy_consumed = 0    # stores how much total energy this core consumed in the simulation duration
        self.activeDuration = 0     # the duration this core was in active state, i.e. executing a task

        # whether this core is an LP or HP core
        self.isLPCore = isLP

        # energy model parameters
        self.ai = ai
        self.f = f
        self.xi = xi
        self.p_idle = p_idle
        
    def energy_consumption_active(self, time):
        """
        time: in ms
        """
        return (self.ai * self.f*self.f*self.f + self.xi) * time

    def energy_consumption_idle(self, time):
        """
        time: in ms
        """
        return self.p_idle * time

    def get_energy_consumed(self):
        return self.energy_consumed

    def get_active_duration(self):
        return self.activeDuration

    def update_active_duration(self, duration):
        self.activeDuration += duration

    def update_energy_consumption(self, amount):
        self.energy_consumed += amount