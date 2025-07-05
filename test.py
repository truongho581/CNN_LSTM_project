import matplotlib.pyplot as plt

# Giả sử bạn lưu avg_power list trong 1 run
avg_power_list = [-30, -25, -20, -22, -15, -5, 2, 5, -18, -12, -8]

plt.hist(avg_power_list, bins=30, color='skyblue')
plt.title('Histogram of Avg Power (dB)')
plt.xlabel('Avg Power (dB)')
plt.ylabel('Count')
plt.axvline(x=-10, color='red', linestyle='--', label='Proposed Threshold')
plt.legend()
plt.show()
