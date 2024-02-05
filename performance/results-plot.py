import matplotlib.pyplot as plt
import pandas as pd

df = pd.DataFrame(pd.read_csv("results.csv"))

df["Start_time"] = pd.to_datetime(df["Start_time"], unit="ms")
df["End_time"] = pd.to_datetime(df["End_time"], unit="ms")
df["Latency"] = (df["End_time"] - df["Start_time"]).dt.microseconds / 1000

b_plot = df.boxplot(
    by ='Subjects', column =['Latency'],
    vert=True,
    patch_artist=True,
    showfliers = False,
    medianprops = dict(color = "yellow", linewidth = 1.5)
)

b_plot.plot()
plt.xlabel("Number of subjects")
plt.ylabel("Latency (milliseconds)")
plt.title("Translator performance")
plt.savefig("results-chart.png", format="png", dpi=1500)
plt.show()
