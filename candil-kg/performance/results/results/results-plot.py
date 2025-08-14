import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import ScalarFormatter

df = pd.DataFrame(pd.read_csv("results.csv"))

df["Kafka_in"] = pd.to_datetime(df["Kafka_in"], unit="ms")
df["Kafka_out"] = pd.to_datetime(df["Kafka_out"], unit="ms")
df["Kafka_latency"] = (df["Kafka_out"] - df["Kafka_in"]).dt.microseconds / 1000

df["End_time"] = pd.to_datetime(df["End_time"], unit="ms")
df["Translator_latency"] = (df["End_time"] - df["Kafka_out"]).dt.microseconds / 1000

# Define the array of values to keep, e.g., routers or interfaces
routers_to_keep = [1, 10, 50, 100, 200, 300]  # only keep these routers

# Filter the DataFrame to keep only rows where 'routers' is in routers_to_keep
df_filtered = df[df['mps'].isin(routers_to_keep)]

interfaces_to_keep = [1,2,3,4]
df_filtered = df_filtered[df_filtered['Subjects'].isin(interfaces_to_keep)]

# Calculate mean latencies grouped by interface and router
mean_latencies = df_filtered.groupby(['Subjects', 'mps'])[['Kafka_latency', 'Translator_latency']].mean().reset_index()

# Extract unique interfaces for creating subplots
interfaces = mean_latencies['Subjects'].unique()
num_interfaces = len(interfaces)

fig, axs = plt.subplots(2, 2, figsize=(12, 10), sharey=False)

axs = axs.flatten()  # Flatten 2x2 array of axes to 1D for easy iteration

# Example y-axis ticks for logarithmic scale
log_ticks = [10, 100, 1000, 10000]

for i, interface in enumerate(interfaces):
    ax = axs[i]
    # Inside your plotting loop per axis, after setting log scale
    ax.set_yscale('log')
    # Set Y limits, top limit at 1 second = 1000 ms
    ax.set_ylim(1, 1000)
    formatter = ScalarFormatter()
    formatter.set_scientific(False)
    ax.yaxis.set_major_formatter(formatter)
    # Optional: set custom ticks if you want control
    ax.set_yticks([5, 10, 50, 100, 500, 1000])
    ax.set_ylabel("Mean Latency (log$_{10}$(ms))")

    data = mean_latencies[mean_latencies['Subjects'] == interface]
    x = range(len(data['mps']))

    # Stacked bars without individual labels for legend
    kafka_bars = ax.bar(x, data['Kafka_latency'], color='C0')
    translator_bars = ax.bar(x, data['Translator_latency'], bottom=data['Kafka_latency'], color='C1')

    ax.set_title(f'Number of Interfaces: {interface}')
    ax.set_xticks(x)
    ax.set_xticklabels(data['mps'])
    ax.set_xlabel('Routers')

# Place a common legend above the plots
# Create a single common legend using handles from the first subplot
handles = [kafka_bars, translator_bars]
labels = ['Kafka Mean Latency', 'Translator Mean Latency']
fig.legend(handles, labels, loc='upper center', ncol=2)
plt.tight_layout(rect=[0, 0, 1, 0.95])
# Save the plot as a PNG file
plt.savefig('translator-chart.png')

# Display the plot
plt.show()
