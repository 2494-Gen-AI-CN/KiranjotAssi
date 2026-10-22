"""Draw the desk's tickets as charts"""
import matplotlib.pyplot as plt
from frame import status_table

def status_chart(df,path):
    """Save a bar chart of tickets per status to a specificed filepath"""
    counts = status_table(df)

    #Create a 6x4 figure with one axes(plot) inside it 
    fig, ax = plt.subplots(figsize=(6,4))

    ax.bar(counts.index, counts.values)
    ax.set_title("Tickets per status")
    ax.set_xlabel("Status", labelpad=30)
    ax.set_ylabel("Tickets")

    fig.tight_layout()
    plt.show()

    #This saves my figure to my disk
    fig.savefig(path)

    plt.close(fig) #i can close the figure once the method ends. If I don't
    # do this, the chart window persists until the program ends




