import gym
import aspygym

env = gym.make('NStats-v0')
stats = env.reset()
while True:
    if stats[-1][3] >= 0.95 * stats[-1][5]:
        action = .1
    else:
        action = (stats[-1][3]-stats[-1][5])*.9
    action = [action]
    env.render()
    stats, reward, _, _ = env.step(action)
    env.render()