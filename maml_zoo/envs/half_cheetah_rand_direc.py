import numpy as np
from maml_zoo.envs.base import MetaEnv
from maml_zoo.logger import logger
from gym import utils
from gym.envs.mujoco import mujoco_env

class HalfCheetahEnvRandDirec(MetaEnv, utils.EzPickle):

    def __init__(self, goal_vel=None):
        self.goal_vel = goal_vel
        self.goal_direction = 1.0
        mujoco_env.MujocoEnv.__init__(self, 'half_cheetah.xml', 5)
        utils.EzPickle.__init__(self)

    def sample_tasks(self, n_tasks):
        # for fwd/bwd env, goal direc is backwards if < 1.0, forwards if > 1.0
        return np.random.uniform(0.0, 2.0, (n_tasks, ))

    def set_task(self, task):
        """
        Args:
            task: task of the meta-learning environment
        """
        self.goal_vel = task
        self.goal_direction = -1.0 if self.goal_vel < 1.0 else 1.0

    def get_task(self):
        """
        Returns:
            task: task of the meta-learning environment
        """
        return self.goal_direction

    def _step(self, action):
        xposbefore = self.model.data.qpos[0, 0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.model.data.qpos[0, 0]
        ob = self._get_obs()
        reward_ctrl = - 0.1 * np.square(action).sum()
        reward_run = self.goal_direction * (xposafter - xposbefore)/self.dt
        reward = reward_ctrl + reward_run
        done = False
        return ob, reward, done, dict(reward_run=reward_run, reward_ctrl=reward_ctrl)

    def _get_obs(self):
        return np.concatenate([
            self.model.data.qpos.flat[1:],
            self.model.data.qvel.flat,
        ])

    def reset_model(self):
        qpos = self.init_qpos + self.np_random.uniform(low=-.1, high=.1, size=self.model.nq)
        qvel = self.init_qvel + self.np_random.randn(self.model.nv) * .1
        self.set_state(qpos, qvel)
        return self._get_obs()

    def viewer_setup(self):
        self.viewer.cam.distance = self.model.stat.extent * 0.5

    def log_diagnostics(self, paths, prefix=''):
        progs = [
            path["observations"][-1][-3] - path["observations"][0][-3]
            for path in paths
        ]
        logger.record_tabular(prefix+'AverageForwardProgress', np.mean(progs))
        logger.record_tabular(prefix+'MaxForwardProgress', np.max(progs))
        logger.record_tabular(prefix+'MinForwardProgress', np.min(progs))
        logger.record_tabular(prefix+'StdForwardProgress', np.std(progs))   