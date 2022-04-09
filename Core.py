class Core:
    """
    Class which represents a Core in the System.
    It keeps track of the duration it has spent active (i.e. executing a task), and
    calculates its energy consumption based on its energy model parameters.
    """
    def __init__(self, name, isLP, ai, f, xi, p_idle):
        """
        Class constructor (__init__).

        name: the name of the core (used for identification in debug logs)
        isLP: whether this core is an LP core (not in use anymore)
        ai: the switching capacitance in the active state power model.
        f: the processing frequency of the core in the active state power model.
        xi: the frequency-independent power consumption in the active state power model.
        p_idle: the constant power consumption when idle.
        """
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
        The energy consumed by the core when active. Power model = (ai*(f^3) + xi)
        Assumption: the following energy consumption variables are equal for all tasks: ai (switching frequency), xi (freq-independent power consumption)

        time: in ms
        """
        return (self.ai * self.f*self.f*self.f + self.xi) * time

    def energy_consumption_idle(self, time):
        """
        The energy consumed by the core when idle. The core consumes a constant amount of energy when idle.

        time: in ms
        """
        return self.p_idle * time

    def get_energy_consumed(self):
        """
        Get the energy consumption of the core.
        """
        return self.energy_consumed

    def get_active_duration(self):
        """
        Get the duration (in ms) that the core has been active (i.e. time spent executing a task).
        """
        return self.activeDuration

    def update_active_duration(self, duration):
        """
        Update the duration the core has spent active. This is updated incrementally while task execution is simulated.

        duration: increment the core's activeDuration by this amount.
        """
        self.activeDuration += duration

    def update_energy_consumption(self, amount):
        """
        Update the energy consumption of the core.

        amount: increment the core's energy_consumed by this amount.
        """
        self.energy_consumed += amount