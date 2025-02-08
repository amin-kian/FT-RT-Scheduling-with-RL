import gym
import numpy as np
import os
from gym import spaces
from EnSuRe_Scheduler import EnSuRe_Scheduler
from Task import Task
from ApproxTask import ApproxTask
from TasksetGenerator import TasksetGenerator
import torch
from torch_geometric.data import Data
from torch_geometric.utils import dense_to_sparse

class EnSuReEnv(gym.Env):
    def __init__(self, num_lp_cores=2, frame_duration=200, lp_hp_ratio=0.8, sys_util=0.8, fault_prob=0.15):
        super(EnSuReEnv, self).__init__()

        # Scheduling parameters
        self.num_lp_cores = num_lp_cores
        self.frame_duration = frame_duration
        self.lp_hp_ratio = lp_hp_ratio
        self.sys_util = sys_util
        self.fault_prob = fault_prob  # Probability of fault occurrence

        # Scheduler instance (acts as simulator)
        self.scheduler = EnSuRe_Scheduler(k=2, frame=self.frame_duration, time_step=1,
                                          m_pri=self.num_lp_cores, lp_hp_ratio=self.lp_hp_ratio, log_debug=False)

        # Define action space (which core to assign a task)
        self.action_space = spaces.Discrete(2)  # 0 = Assign to LP, 1 = Assign to HP

        # Define observation space (graph-based state for GNN)
        # Define maximum tasks to set a fixed observation shape
        max_tasks = 2000  # Adjust as needed

        # Define observation space (graph-based state for GNN)
        self.observation_space = spaces.Dict({
            "graph": spaces.Box(low=-np.inf, high=np.inf, shape=(max_tasks, 2), dtype=np.float32),
            "node_num": spaces.Discrete(max_tasks),
            "ready": spaces.Box(low=0, high=1, shape=(max_tasks, 1), dtype=np.float32)
        })

        # Internal tracking of tasks
        self.current_task_index = 0
        self.tasks = []
        self.done = False

    def reset(self):
        """Reset the environment at the beginning of each episode using tasks from TasksetGenerator."""
        generator = TasksetGenerator(
            distribution=np.random.choice(["uniform", "normal"]),  # Random distribution
            n=np.random.randint(100, 2000),  # Random number of tasks
            frame_duration=self.frame_duration,
            sys_util=np.random.uniform(0.6, 0.9),  # Varying system utilization
            precision_dp=2, num_lpcores=self.num_lp_cores, lp_hp_ratio=self.lp_hp_ratio
        )

        filename = f"tasksets/sysutil{self.sys_util}_cores{self.num_lp_cores}_0.csv"
        generator.generate(filename)
        self.tasks = self.load_tasks_from_file(filename)

        self.current_task_index = 0
        self.done = False
        return self._get_state()

    def _rl_decision_on_fault(self):
        """Simulate an RL decision-making step for handling fault cases."""
        # The agent can decide whether to retry on LP or move to HP
        return np.random.choice(["LP", "HP"], p=[0.5, 0.5])  # 50% probability for each decision

    def step(self, action):
        """Take a step by scheduling the current task based on the RL action."""
        if self.done:
            return self._get_empty_state(), 0, True, {"r": 0, "l": self.current_task_index}  # ✅ Add "l"

        # Select the task
        task = self.tasks[self.current_task_index]

        # Assign task to LP or HP based on action
        assigned_core = "HP" if action == 1 else "LP"
        execution_time = task.getHPExecutionTime() if action == 1 else task.getLPExecutionTime()

        # Simulate a fault occurrence with a probability
        fault_occurred = np.random.rand() < self.fault_prob

        if fault_occurred:
            retry_action = self._rl_decision_on_fault()
            if retry_action == "LP":
                assigned_core = "LP"
                execution_time = task.getLPExecutionTime()
            elif retry_action == "HP":
                assigned_core = "HP"
                execution_time = task.getHPExecutionTime()

        # Simulate execution and update system state
        self.scheduler.pri_schedule[self.current_task_index] = assigned_core

        # Update the graph after the task assignment
        self._update_graph(task, execution_time, assigned_core)

        # Compute reward
        reward = self._calculate_reward(task, execution_time, assigned_core, fault_occurred)

        # Move to the next task
        self.current_task_index += 1
        if self.current_task_index >= len(self.tasks):
            self.done = True

        done = self.done
        observation = self._get_state() if not done else self._get_empty_state()

        # ✅ Ensure info always includes episode length "l"
        info = {
            "episode": {"r": float(reward), "l": self.current_task_index},  # ✅ Track episode length
            "fault_occurred": fault_occurred
        }

        return observation, reward, done, info

    def _get_empty_state(self):
        """Return a fixed-size zeroed-out observation when the episode is done."""
        max_tasks = 2000

        return {
            "graph": np.zeros((max_tasks, 2), dtype=np.float32),  # ✅ Fixed-size zero padding
            "node_num": np.array([0], dtype=np.int32),  # ✅ Fixed format
            "ready": np.zeros((max_tasks, 1), dtype=np.float32)  # ✅ Fixed size
        }

    def _get_state(self):
        """Convert the scheduling state into a fixed-size NumPy array representation."""
        max_tasks = 2000  # Fixed observation size

        if self.done:
            return self._get_empty_state()

        num_tasks = len(self.tasks)

        # Convert node features into a NumPy array (Variable size)
        node_features = np.array([
            [task.getLPExecutionTime() / self.frame_duration,
             task.getHPExecutionTime() / self.frame_duration]
            for task in self.tasks
        ], dtype=np.float32)

        # **Fix**: Pad or truncate node_features to fit (2000, 2)
        if num_tasks < max_tasks:
            padding = np.zeros((max_tasks - num_tasks, 2), dtype=np.float32)  # Zero-padding
            node_features = np.vstack([node_features, padding])  # Stack padded rows
        else:
            node_features = node_features[:max_tasks]  # Truncate extra tasks

        # Ensure node_num and ready are also correctly formatted
        node_num = np.array([min(num_tasks, max_tasks)], dtype=np.int32)  # Clamped node number
        ready = np.ones((max_tasks, 1), dtype=np.float32) if num_tasks > 0 else np.zeros((max_tasks, 1),
                                                                                         dtype=np.float32)

        return {
            "graph": node_features,  # ✅ Always (2000, 2)
            "node_num": node_num,  # ✅ Always scalar array
            "ready": ready  # ✅ Always (2000, 1)
        }

    def _calculate_reward(self, task, execution_time, assigned_core, fault_occurred):
        """Reward function with improved fault handling logic."""
        deadline_penalty = -5 if execution_time > task.getDeadline() else 5
        energy_cost = -execution_time * (0.5 if assigned_core == "LP" else 2.0)
        fault_reward = 6 if fault_occurred and assigned_core == "LP" else (-6 if fault_occurred else 0)
        lp_bonus = 5 if assigned_core == "LP" and execution_time <= task.getDeadline() else -3

        return float(energy_cost + deadline_penalty + fault_reward + lp_bonus)

    def _update_graph(self, task, execution_time, assigned_core):
        """Update the graph representation based on task execution."""
        task_index = self.current_task_index

        # Ensure task execution is stored
        self.tasks[task_index].execution_time = execution_time

        # Convert updated task features into a NumPy array
        node_features = np.array([
            [task.getLPExecutionTime() / self.frame_duration,
             task.getHPExecutionTime() / self.frame_duration]
            for task in self.tasks
        ], dtype=np.float32)

        # Ensure the adjacency matrix is converted into an edge list (compatible format)
        num_tasks = len(self.tasks)
        adjacency_matrix = np.zeros((num_tasks, num_tasks))
        for i in range(num_tasks - 1):
            adjacency_matrix[i, i + 1] = 1

        edge_index = dense_to_sparse(torch.tensor(adjacency_matrix, dtype=torch.float))[0].numpy()

        # Update the environment's state representation
        self.state = {
            "graph": node_features,  # ✅ Updated graph representation
            "node_num": np.array([num_tasks], dtype=np.int32),
            "ready": np.ones((num_tasks, 1), dtype=np.float32)
        }

    def load_tasks_from_file(self, filepath):
        """Reads a taskset file and returns a list of Task objects."""
        tasks = []
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Taskset file {filepath} not found!")

        with open(filepath, "r") as file:
            lines = file.readlines()

        for line in lines:
            data = line.strip().split(",")
            if len(data) < 3:
                continue

            task_id = int(data[0])
            lp_exec_time = float(data[1])
            hp_exec_time = float(data[2])
            deadline = float(data[3]) if len(data) > 3 else None

            tasks.append(ApproxTask(task_id, lp_exec_time, hp_exec_time, deadline))
        return tasks
