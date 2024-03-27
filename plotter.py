import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use('Agg')

class HMPlotter:

    def __init__(self, name = "defaultplot", width=0, height=0, initial_state=None):
        self.name = name
        if initial_state is not None:
            self.state = np.array(initial_state)
        else:
            self.state = np.array([[0]*width for x in range(height)])


    def add(self, add_state):
        self.state = self.state + np.array(add_state)
        pass

    def update_img(self):
        plt.imshow(self.state, cmap='jet')
        plt.colorbar()
        plt.title(self.name)
        plt.savefig('hm.png')
        plt.clf()
        pass
    
    def reset(self):
        for i in range(len(self.state)):
            for j in range(len(self.state[0])):
                self.state[i][j] = 0
        self.update_img()
