from matplotlib import pyplot as plt, animation as an
import numpy as np
import matplotlib.animation as animation

def teste1():
    fig = plt.figure()
    board = plt.axes(xlim=(0, 200), ylim=(0, 100))

    x = 10
    y = 10
    r = 10

    for p in range(10):
        circle = plt.Circle((x, y), r, fc='w', ec='b')
        
        board.add_patch(circle)

        annotation = plt.annotate("", xytext=(x, y), xy=(x+10, y+10), arrowprops=dict(facecolor='r', edgecolor='r', headwidth=6, headlength=6, width=0.1))

        plt.draw()
        plt.pause(0.2)
        circle.remove()
        annotation.remove()
        x += 10
        y += 10

    plt.show()

def teste2():
    labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
    sizes = [15, 30, 45, 10]

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels)
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.show()

def teste3():
    # Fixing random state for reproducibility
    np.random.seed(19680801)

    # Compute pie slices
    N = 1
    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
    radii = 10 * np.random.rand(N)
    #width = np.pi / 4 * np.random.rand(N)
    width = 0.2
    colors = plt.cm.viridis(radii / 10.)

    ax = plt.subplot(projection='polar')
    ax.bar(theta, radii, width=width, bottom=4, color=colors, alpha=0.9)

    plt.show()

def teste4():

    # Set up the figure and polar axis
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2)
    ax.set_yticklabels([])
    
    # Data
    angles = [0, np.pi]  # 0 and 180 degrees in radians
    values = [1, 1]  # Both bars have equal height
    bars = ax.bar(angles, values, width=0.2)
    
    # Function to update the bars
    def update(num):
        angle = 2 * np.pi * (num % 360) / 360
        bars[0].set_x(angle)
        bars[1].set_x((angle + np.pi) % (2 * np.pi))  # 180 degrees apart
        return bars

    # Create animation
    ani = animation.FuncAnimation(fig, update, interval=1, blit=True,cache_frame_data=False)

    # Display the plot
    plt.show()

def testeLineEBar():

    # Dados para o gráfico
    x = [1, 2, 3, 4, 5]
    y1 = [10, 15, 20, 25, 30]
    y2 = [30, 25, 20, 15, 10]

    # Cria uma figura e subplots
    fig, ax = plt.subplots()

    # Adiciona um gráfico de barras
    ax.bar(x, y1, color='b', label='Bar Graph')

    # Adiciona um gráfico de linha no mesmo subplot
    ax.plot(x, y2, color='r', marker='o', label='Line Graph')

    # Adiciona legendas e rótulos
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_title('Bar and Line Graph in the Same Subplot')
    ax.legend()

    # Mostra o gráfico
    plt.show()

def teste5():

    from matplotlib.animation import FuncAnimation

    # Fixing random state for reproducibility
    np.random.seed(19680801)


    # Create new Figure and an Axes which fills it.
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.set_xlim(0, 1), ax.set_xticks([])
    ax.set_ylim(0, 1), ax.set_yticks([])

    # Create rain data
    n_drops = 50
    rain_drops = np.zeros(n_drops, dtype=[('position', float, (2,)),
                                        ('size',     float),
                                        ('growth',   float),
                                        ('color',    float, (4,))])

    # Initialize the raindrops in random positions and with
    # random growth rates.
    rain_drops['position'] = np.random.uniform(0, 1, (n_drops, 2))
    rain_drops['growth'] = np.random.uniform(50, 200, n_drops)

    # Construct the scatter which we will update during animation
    # as the raindrops develop.
    scat = ax.scatter(rain_drops['position'][:, 0], rain_drops['position'][:, 1],
                    s=rain_drops['size'], lw=0.5, edgecolors=rain_drops['color'],
                    facecolors='none')


    def update(frame_number):
        # Get an index which we can use to re-spawn the oldest raindrop.
        current_index = frame_number % n_drops

        # Make all colors more transparent as time progresses.
        rain_drops['color'][:, 3] -= 1.0/len(rain_drops)
        rain_drops['color'][:, 3] = np.clip(rain_drops['color'][:, 3], 0, 1)

        # Make all circles bigger.
        rain_drops['size'] += rain_drops['growth']

        # Pick a new position for oldest rain drop, resetting its size,
        # color and growth factor.
        rain_drops['position'][current_index] = np.random.uniform(0, 1, 2)
        rain_drops['size'][current_index] = 5
        rain_drops['color'][current_index] = (0, 0, 0, 1)
        rain_drops['growth'][current_index] = np.random.uniform(50, 200)

        # Update the scatter collection, with the new colors, sizes and positions.
        scat.set_edgecolors(rain_drops['color'])
        scat.set_sizes(rain_drops['size'])
        scat.set_offsets(rain_drops['position'])


    # Construct the animation, using the update function as the animation director.
    animation = FuncAnimation(fig, update, interval=1, save_count=100)
    plt.show()

#teste1()
#teste2()
teste3()
