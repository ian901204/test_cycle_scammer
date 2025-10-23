from matplotlib import pyplot as plt

def plot_basic(data):
    #x axis as 5 time test cycles, y axis as Vf, Pf, Ith
    test_cycles = [1, 2, 3, 4, 5]
    
    fig, axs = plt.subplots(3, 1, figsize=(8, 12))
    axs[0].set_title(f'Pf over Test')
    axs[0].set_xlabel('Test Cycle')
    axs[0].set_ylabel('Pf')
    axs[1].set_title(f'Vf over Test')
    axs[1].set_xlabel('Test Cycle')
    axs[1].set_ylabel('Vf')
    axs[2].set_title(f'Ith over Test')
    axs[2].set_xlabel('Test Cycle')
    axs[2].set_ylabel('Ith')
    for ch in data:
        vf = data[ch]["vf"]
        pf = data[ch]["pf"]
        ith = data[ch]["ith"]
        axs[0].plot(test_cycles, pf, marker='o', label =f'Channel {ch}')
        axs[1].plot(test_cycles, vf, marker='o', label =f'Channel {ch}')
        axs[2].plot(test_cycles, ith, marker='o', label =f'Channel {ch}')
    plt.tight_layout()
    plt.show()

def plot_with_ch(vf, pf, ith):
    test_cycles = [1, 2, 3, 4, 5]
    fig, axs = plt.subplots(3, 1, figsize=(8, 12))
    axs[0].set_title(f'Pf over Test Cycles')
    axs[0].set_xlabel('Test Cycle')
    axs[0].set_ylabel('Pf')
    axs[0].plot(test_cycles, pf, marker='o')

    axs[1].set_title(f'Vf over Test Cycles')
    axs[1].set_xlabel('Test Cycle')
    axs[1].set_ylabel('Vf')
    axs[1].plot(test_cycles, vf, marker='o')
    axs[2].set_title(f'Ith over Test Cycles')
    axs[2].set_xlabel('Test Cycle')
    axs[2].set_ylabel('Ith')
    axs[2].plot(test_cycles, ith, marker='o')
    
    
    plt.tight_layout()
    plt.show()