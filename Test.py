from csv import reader
from ast import literal_eval
import matplotlib.pyplot as plt
import numpy as np
from TasksetGenerator import TasksetGenerator
from System import System
from Task import Task
from ApproxTask import ApproxTask

# Task Set Parameters
sys_utils = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9]
num_sets = 4  # No. task sets to generate with this configuration
n = 100  # No. tasks in set
frame_duration = 200  # Length of frame, in ms
precision_taskgen = 2  # Decimal places for execution time in taskset generation, i.e. 0.01 = 2 dp
precision_dp = 4  # Decimal places for system, i.e. 0.001 = 3 dp
time_step = 1 / 10 ** precision_dp  # Time step for execution time
lp_hp_ratio = 0.8  # LP core:HP core speed ratio
num_lpcores = [1, 2, 3, 4]
seed = 50
repeat = 5  # Times to run for average
k = 20  # Scheduler parameters
# Scheduler parameters for LP/HP core speed ratio
lp_hp_ratios = [0.2, 0.4, 0.6, 0.8, 1.0]

# Results to collect
energy_consumed_results = []  # Energy consumed from simulations
energy_consumed_per_sysutil = []  # Energy results per system utilization



# Helper function for task set generation
def generate_tasksets():
    for sys_util in sys_utils:
        for i in range(num_sets):
            for x in num_lpcores:
                taskset_gen = TasksetGenerator("normal", n, frame_duration, sys_util, precision_taskgen, x, lp_hp_ratio,
                                               seed)
                taskset_gen.generate(f'tasksets/sysutil{sys_util}_cores{x}_{i}.csv')


# Run simulation and calculate energy consumption
def run(scheduler_type, num_lpcores):
    sys_util = 0.5  # Fixed at 50% system utilization
    energy_consumed_per_sysutil = 0

    for i in range(num_sets):
        # Import task set from CSV
        with open(f'tasksets/sysutil{sys_util}_cores{1}_{i}.csv') as read_obj:
            csv_reader = reader(read_obj)
            tasks_data = [tuple(map(literal_eval, x)) for x in map(tuple, csv_reader)]

        # Convert data into Task objects
        tasks = []
        for task in tasks_data:
            if scheduler_type == "FEST":
                tasks.append(Task(task[0], task[1], task[2]))
            elif scheduler_type == "EnSuRe":
                tasks.append(ApproxTask(task[0], task[1], task[2], task[3]))

        # Run the simulation and compute energy consumption
        energy_consumed = 0
        for x in range(repeat):
            system = System(scheduler_type, k, frame_duration, time_step, num_lpcores, lp_hp_ratio, False)
            system.run(tasks)
            energy_consumed += system.get_energy_consumption()

        energy_consumed /= repeat  # Average energy consumption
        energy_consumed_per_sysutil += energy_consumed

    # Average energy consumption for this sys_util value
    energy_consumed_per_sysutil /= num_sets
    return energy_consumed_per_sysutil


# Run experiments for different configurations
def run_experiments():
    print("Run FEST")
    energy_consumed_results.append(run("FEST", 1))

    for num_lp in num_lpcores:
        print(f"Run EnSuRe - {num_lp} LP cores")
        energy_consumed_results.append(run("EnSuRe", num_lp))

    print("Done")
    print(energy_consumed_results)


# Normalize results for plotting
def normalize_results():
    max_energy = max(energy_consumed_results)
    results_norm = np.array(energy_consumed_results) / max_energy
    print(results_norm)
    return results_norm


# Plot results (Energy Consumption vs No. LP Cores)
def plot_results():
    results_norm = normalize_results()
    plt.title('Energy Consumption vs No. LP Cores')
    plt.ylabel('Normalized Energy Consumption (%)')
    plt.ylim([0.0, 1.1])
    x_axis = ['FEST', 'EnSuRe\n(1 LP-core)', 'EnSuRe\n(2 LP-core)', 'EnSuRe\n(3 LP-core)', 'EnSuRe\n(4 LP-core)']
    plt.plot(x_axis, results_norm, marker='o')
    plt.show()


# Running the experiments
generate_tasksets()
run_experiments()
plot_results()



energy_consumed_results = []
active_duration_results = []

def run_with_speed_ratios():
    for spd_ratio in lp_hp_ratios:
        energy_consumed_per_sysutil = 0
        active_duration_per_spdratio = 0
        for i in range(num_sets):
            # Import task set from CSV
            with open(f'tasksets/sysutil{0.5}_cores{1}_{i}.csv') as read_obj:
                csv_reader = reader(read_obj)
                tasks_data = [tuple(map(literal_eval, x)) for x in map(tuple, csv_reader)]

            # Convert data into Task objects
            tasks = []
            for task in tasks_data:
                hp_execTime = round(task[1] * spd_ratio, precision_dp)
                if scheduler_type == "FEST":
                    tasks.append(Task(task[0], task[1], hp_execTime))
                elif scheduler_type == "EnSuRe":
                    tasks.append(ApproxTask(task[0], task[1], hp_execTime, 0, 0, task[3]))

            # Run the simulation and compute energy consumption
            energy_consumed = 0
            active_duration = 0
            for x in range(repeat):
                system = System(scheduler_type, k, frame_duration, time_step, 1, spd_ratio)
                system.run(tasks)
                energy_consumed += system.get_energy_consumption()
                active_duration += system.get_hpcore_active_duration()

            energy_consumed /= repeat
            active_duration /= repeat
            energy_consumed_per_sysutil += energy_consumed
            active_duration_per_spdratio += active_duration

        energy_consumed_per_sysutil /= num_sets
        active_duration_per_spdratio /= num_sets
        energy_consumed_results.append(energy_consumed_per_sysutil)
        active_duration_results.append(active_duration_per_spdratio)


# Plot energy consumption and active duration vs LP/HP core speed ratio
def plot_speed_ratio_results():
    run_with_speed_ratios()
    max_energy = max(energy_consumed_results)
    results_norm = np.array(energy_consumed_results) / max_energy
    plt.title('Energy Consumption vs LP/HP Core Speed (Ratio)')
    plt.xlabel('LP/HP Core Frequency (Ratio)')
    plt.ylabel('Normalized Energy Consumption (%)')
    plt.ylim([0.0, 1.1])
    plt.plot(lp_hp_ratios, results_norm, marker='o', label='FEST')
    plt.plot(lp_hp_ratios, results_norm, marker='v', label='EnSuRe (2 LP-core)')
    plt.legend()
    plt.show()


# Plot backup core active duration vs LP/HP core speed
def plot_backup_core_active_duration():
    plt.plot(lp_hp_ratios, active_duration_results[0], marker='o', label='FEST')
    plt.plot(lp_hp_ratios, active_duration_results[1], marker='v', label='EnSuRe (2 LP-core)')
    plt.plot(lp_hp_ratios, active_duration_results[2], marker='s', label='EnSuRe (3 LP-core)')
    plt.plot(lp_hp_ratios, active_duration_results[3], marker='H', label='EnSuRe (4 LP-core)')
    plt.title('Active Duration vs LP/HP Core Speed (Ratio)')
    plt.xlabel('LP/HP Core Frequency (Ratio)')
    plt.ylabel('Backup Core Active Duration')
    plt.legend()
    plt.show()


# Run the final experiments with varying number of faults (k values)
def run_with_k_values():
    k_values = [20, 40, 60, 80]
    energy_consumed_results = []

    for k in k_values:
        energy_consumed_per_sysutil = 0
        for i in range(num_sets):
            # Import task set from CSV
            with open(f'tasksets/sysutil{0.5}_cores{1}_{i}.csv') as read_obj:
                csv_reader = reader(read_obj)
                tasks_data = [tuple(map(literal_eval, x)) for x in map(tuple, csv_reader)]

            #

