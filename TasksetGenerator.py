import numpy as np
import sys
import random

# n = 200     # no. tasks
# sys_util = 1.0  # % utilisation of the system
# frame_duration = 200    # in ms

# precision = 2   # decimal places

# min_norm = 1/10**precision

# lp_hp_ratio = 0.5   # ratio of LP speed : HP speed

# # normal sampling values
# mean = 1
# sd = 5

# generalise it so it can also generate task set for EnSuRe, then to generate for FEST it is a specific restriction?

class TasksetGenerator:
    def __init__(self, distribution, n, frame_duration, sys_util, precision_dp, lp_hp_ratio):
        """
        distribution: "uniform" or "normal"
        n: no. tasks per set
        frame_duration: frame deadline (ms)
        sys_util: system utilisation (%)
        """
        self.distribution = distribution
        self.n = n
        self.sys_util = sys_util
        self.frame_duration = frame_duration

        self.precision = precision_dp
        self.min_norm = 1/10**precision_dp

        self.lp_hp_ratio = lp_hp_ratio
        
        # normal sampling values
        self.mean = 1
        self.sd = 5

        # Determine expected "magnitude" to meet target system utilisation (sys_util * frame_duration)
        self.target_magnitude = self.sys_util * self.frame_duration

    def generate(self, filename):
        """
        1. Randomise n numbers from 0 to 1  - continuous uniform distribution or normal distribution
        2. Sum them up to find the current "magnitude", then normalize/scale to the expected magnitude (e.g. 50% of 200ms)
        3. Round to the precision
        4. Determine a deadline for each task (would only be used by EnSuRe)
        5. Generate the task list
        """
        # 1. Randomly sample n numbers
        if self.distribution == "uniform":
            rand_sample = np.random.random_sample(n)
        elif self.distribution == "normal":
            rand_sample = np.random.normal(loc=self.mean, scale=self.sd, size=self.n)
            # normalize to 0 to 1
            rand_sample = (1-self.min_norm)*(rand_sample - np.min(rand_sample))/np.ptp(rand_sample) + self.min_norm

        # 2. Get the "magnitude" of the array (sum of the array)
        magnitude = sum(rand_sample)

        # 3. Scale the samples to the expected magnitude
        exec_times = rand_sample * (self.target_magnitude / magnitude)

        # 4. Determine a deadline for each task
        # NOTE: one way to guarantee WQ: split deadlines into equal parts
        # then, if any task's deadline is smaller than its execution time, increase it 
        deadlines = []
        time_window = self.frame_duration / self.n
        half_time_window = time_window * 0.5
        for i in range(len(exec_times)):
            #deadline = np.random.uniform(exec_time, self.frame_duration)    # deadline is anywhere between end of task execution, and frame_duration
            
            # introduce a small gaussian distribution to vary the deadline
            deadline = min(i * time_window + half_time_window * np.random.normal(), self.frame_duration)
            # if any task's deadline is smaller than its execution time, increase it 
            while deadline < exec_times[i]:
                deadline += min(exec_times[i], self.frame_duration)

            deadlines.append(deadline)

        # NOTE: how to ensure WQ must be within?

        # 5. Generate the task data
        tasks = ""
        lpexec_check = []
        hpexec_check = []
        for i in range(len(exec_times)):
            # i. task id
            tasks = tasks + str(i) + ","

            # ii. LP execution time (rounded to precision)
            lp_exec = round(exec_times[i], self.precision)
            tasks = tasks + str(lp_exec) + ","
            
            lpexec_check.append(lp_exec)

            # iii. HP execution time (rounded to precision)
            hp_exec = round(lp_exec * self.lp_hp_ratio, self.precision)
            tasks = tasks + str(hp_exec) + ","

            hpexec_check.append(hp_exec)

            # iii. task deadline (for EnSuRe only)
            tasks = tasks + str(deadlines[i])

            # iv. optional execution time (for EnSuRe only)

            tasks = tasks + "\n"

        # 5. Write task data to CSV file
        # print(np.max(lpexec_check))
        # print(np.min(lpexec_check))
        # print(sum(lpexec_check))
        # print(sum(hpexec_check))
        with open(filename, 'w') as f:
            f.write(tasks)


if __name__ == "__main__":

    # parse arguments
    try:
        n = int(sys.argv[1])
        frame_duration = int(sys.argv[2])
        sys_util = float(sys.argv[3])
    except IndexError:
        raise SystemExit("Error: please run 'python38 taskset_generator.py [n] [frame] [sys_util]', e.g. 'python38 taskset_generator.py 5 200 0.75'\r\n\r\n  n = no. tasks per set | frame = deadline (ms) | sys_util = system utilisation (%)")

    print("===TASKSET PARAMETERS===")
    print("For Scheduler = {0}".format("FEST"))
    print("no. tasks n = {0}".format(n))
    print("frame = {0} ms".format(frame_duration))
    print("system utilisation % = {0}".format(sys_util))

    # run
    taskset_gen = TasksetGenerator(n, frame_duration, sys_util, 2, 0.5)
    taskset_gen.generate('tasksets/test.csv')