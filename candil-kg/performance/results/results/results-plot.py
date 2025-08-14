import matplotlib.pyplot as plt
import pandas as pd

df = pd.DataFrame(pd.read_csv("results.csv"))

df["Kafka_in"] = pd.to_datetime(df["Kafka_in"], unit="ms")
df["Kafka_out"] = pd.to_datetime(df["Kafka_out"], unit="ms")
df["Kafka_latency"] = (df["Kafka_out"] - df["Kafka_in"]).dt.microseconds / 1000

df["End_time"] = pd.to_datetime(df["End_time"], unit="ms")
df["Translator_latency"] = (df["End_time"] - df["Kafka_out"]).dt.microseconds / 1000

# Take samples above 10 subjects
df = df[df["mps"] >= 1]
df = df[df["mps"] <= 140]

# Calculate mean latencies grouped by interface and router
mean_latencies = df.groupby(['Subjects', 'mps'])[['Kafka_latency', 'Translator_latency']].mean().reset_index()

# Extract unique interfaces for creating subplots
interfaces = mean_latencies['Subjects'].unique()
num_interfaces = len(interfaces)

fig, axs = plt.subplots(2, 2, figsize=(12, 10), sharey=True)

axs = axs.flatten()  # Flatten 2x2 array of axes to 1D for easy iteration

for i, interface in enumerate(interfaces):
    ax = axs[i]
    data = mean_latencies[mean_latencies['Subjects'] == interface]
    x = range(len(data['mps']))

    # Stacked bars without individual labels for legend
    kafka_bars = ax.bar(x, data['Kafka_latency'], color='C0')
    translator_bars = ax.bar(x, data['Translator_latency'], bottom=data['Kafka_latency'], color='C1')

    ax.set_title(f'Interfaces: {interface}')
    ax.set_xticks(x)
    ax.set_xticklabels(data['mps'])
    ax.set_xlabel('Routers')
    if i == 0:
        ax.set_ylabel('Mean Latency')

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
