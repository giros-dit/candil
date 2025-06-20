import matplotlib.pyplot as plt
import pandas as pd

df = pd.DataFrame(pd.read_csv("results/results.csv"))

df["Kafka_in"] = pd.to_datetime(df["Kafka_in"], unit="ms")
df["Kafka_out"] = pd.to_datetime(df["Kafka_out"], unit="ms")
df["Kafka_latency"] = (df["Kafka_out"] - df["Kafka_in"]).dt.microseconds / 1000

df["End_time"] = pd.to_datetime(df["End_time"], unit="ms")
df["Translator_latency"] = (df["End_time"] - df["Kafka_out"]).dt.microseconds / 1000

# Take samples above 10 subjects
df = df[df["Triples"] >= 10]

b_plot = df.boxplot(
    by ='Triples', column =['Kafka_latency'],
    vert=True,
    patch_artist=True,
    showfliers = False,
    medianprops = dict(color = "yellow", linewidth = 1.5)
)

b_plot.plot()
plt.xlabel("Number of RDF triples")
plt.ylabel("Latency (milliseconds)")
plt.title("Kafka performance")
plt.suptitle('')
plt.savefig("results-kafka-chart.png", format="png", dpi=1500)
plt.show()

c_plot = df.boxplot(
    by ='Triples', column =['Translator_latency'],
    vert=True,
    patch_artist=True,
    showfliers = False,
    medianprops = dict(color = "yellow", linewidth = 1),
    boxprops = dict(facecolor = "grey")
)

c_plot.plot()
plt.xlabel("Number of RDF triples")
plt.ylabel("Latency (milliseconds)")
plt.title("NGSI-LD Translator performance")
plt.suptitle('')
plt.savefig("results-translator-chart.png", format="png", dpi=1500)
plt.show()
