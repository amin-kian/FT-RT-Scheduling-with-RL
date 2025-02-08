from stable_baselines3 import DQN, PPO
from EnsureEnv import EnSuReEnv
from stable_baselines3.common.evaluation import evaluate_policy

# Create the environment
env = EnSuReEnv(num_lp_cores=2, frame_duration=200, lp_hp_ratio=0.8, sys_util=0.8)

# Initialize the model (DQN or PPO)
model = DQN("MultiInputPolicy", env, verbose=1, learning_rate=0.001, buffer_size=10000, batch_size=32, gamma=0.99)

# Train the model (for 100,000 time steps)
model.learn(total_timesteps=100000)

# Save the trained model
model.save("dqn_ensure_model")

# Optionally, evaluate the trained model
mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
print(f"Mean Reward: {mean_reward}, Standard Deviation: {std_reward}")
