import os
import random
import numpy as np
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from scipy.signal import spectrogram
from OBS_station import start_time, end_time, client, LOCATION, NETWORK, CHANNEL, station_data
from event_info import radius, minmagni

os.makedirs("waveforms", exist_ok=True)
os.makedirs("earthquake", exist_ok=True)
os.makedirs("noise", exist_ok=True)
os.makedirs("full_spectrogram", exist_ok=True)

STATION, lat, lon, elev = station_data

catalog = client.get_events(starttime=start_time,
                            endtime=end_time,
                            latitude=lat,
                            longitude=lon,
                            maxradius=radius,
                            minmagnitude=minmagni)

# Sắp xếp theo thời gian tăng dần
catalog.events.sort(key=lambda e: e.origins[0].time)

print(f"---🔍 Tổng cộng {len(catalog)} sự kiện---")

# Tạo vùng cấm ±10 phút
no_go_intervals = [(e.origins[0].time - 600, e.origins[0].time + 600) for e in catalog]

def is_interval_safe(start, duration=180):
    return all(start + duration < ban_start or start > ban_end for ban_start, ban_end in no_go_intervals)

#Hàm vẽ full spectrogram   
def plot_full_spectrogram(tr, label, index):
    fs = tr.stats.sampling_rate
    # Bên trong hàm plot_full_spectrogram():
    f, t, Sxx = spectrogram(tr.data, fs=fs, nperseg=256, noverlap=128)
    power_db = 10 * np.log10(Sxx + 1e-10)
    f_mask = f <= 10
    f = f[f_mask]
    power_db = power_db[f_mask, :]


    plt.figure(figsize=(12, 5))
    plt.pcolormesh(t, f, power_db, shading='gouraud', cmap='inferno', vmin=-80, vmax=40)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.colorbar(label="Power (dB)")
    plt.title(f"Full Spectrogram - {label} {index}")
    plt.tight_layout()
    plt.savefig(f"full_spectrogram/{STATION}_{label.lower()}_{index:03}_full.png", bbox_inches='tight', pad_inches=0.1)
    plt.close()

# ==== ẢNH ĐỘNG ĐẤT ====
for i, event in enumerate(catalog):
    try:
        origin_time = event.origins[0].time
        print(f"\n🔍 Đang xử lý Event {i}: {origin_time}")

        # Lấy waveform từ 1 phút trước đến 10 phút sau EQ
        st = client.get_waveforms(network=NETWORK, station=STATION, location=LOCATION, channel=CHANNEL,
                                  starttime=origin_time - 60,
                                  endtime=origin_time + 600)

        st.detrend("demean")
        st.filter("bandpass", freqmin=1, freqmax=10)
        st.write(f"waveforms/{STATION}_event_{i:03}.mseed", format="MSEED")

        tr = st[0]
        plot_full_spectrogram(tr, "EQ", i)

        fs = tr.stats.sampling_rate
        segment_samples = int(20 * fs)

        triggered = False
        saved_segments = 0
        max_power = -np.inf

        for j in range(100):  # Tối đa 100 đoạn 20s (tổng cộng 33 phút)
            start_idx = j * segment_samples
            end_idx = start_idx + segment_samples
            if end_idx > len(tr.data):
                break

            segment = tr.data[start_idx:end_idx]
            f, t, Sxx = spectrogram(segment, fs=fs, nperseg=256, noverlap=128)
            power_db = 10 * np.log10(Sxx + 1e-10)
            avg_power = np.mean(power_db)
            max_power = max(max_power, avg_power)

            print(f"[EQ {i}, Segment {j}] Avg Power: {avg_power:.2f} dB")

            if not triggered:
                if avg_power > 0:  # Bắt đầu ghi nếu power tăng
                    triggered = True
                else:
                    continue  # Bỏ qua đoạn trước khi EQ kích hoạt

            if triggered and avg_power < 0:
                print(f"⚠️ Dừng tại segment {j} vì avg_power < 0 dB")
                break

            # Vẽ và lưu ảnh spectrogram
            fig, ax = plt.subplots(figsize=(6, 4))
            t_uniform = np.linspace(0, 20, Sxx.shape[1])
            ax.pcolormesh(t_uniform, f, power_db, shading='gouraud',
                          cmap='inferno', vmin=-80, vmax=40)
            ax.axis('off')
            for spine in ax.spines.values():
                spine.set_visible(False)
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            plt.savefig(f"earthquake/{STATION}_eq_{i:03}_{j:02}.png", bbox_inches='tight', pad_inches=0)
            plt.close()
            saved_segments += 1

        if saved_segments == 0 or max_power < 0:
            print(f"⚠️ Bỏ qua Event {i} vì không đủ năng lượng để phân biệt với noise")
            continue

        print(f"✅ Event {i} xong. Đã lưu {saved_segments} ảnh.")
    except Exception as e:
        print(f"❌ Lỗi với Event {i}: {e}")

# ==== ẢNH NOISE ====
eq_dir = "earthquake"
num_eq_images = len([
    f for f in os.listdir(eq_dir)
    if f.endswith(".png") and STATION in f
])
num_noise_iterations = num_eq_images // 9

print("🔧 Bắt đầu tạo ảnh noise...")

for i in range(num_noise_iterations): #vòng lặp events
    try:
        for _ in range(20):  # ✅ Thử tối đa 20 lần để tìm 1 thời điểm noise hợp lệ
            event = random.choice(catalog)  # 🎲 Chọn 1 sự kiện động đất bất kỳ trong catalog
            origin_time = event.origins[0].time  # ⏱ Lấy thời điểm xảy ra động đất đó
            rand_offset = random.uniform(1200, 2400)  # ⏱ Sinh số ngẫu nhiên từ 1200–2400 giây (20–40 phút)
            rand_time = origin_time + rand_offset  # 📌 Thời điểm noise được chọn = sau EQ 20–40 phút
            if is_interval_safe(rand_time):
                break
        else: #nếu không lấy được trả về 
            print(f"⚠️ Không tìm được noise hợp lệ {i}")
            continue

        st = client.get_waveforms(network=NETWORK, station=STATION, location=LOCATION, channel=CHANNEL,
                                starttime=rand_time,
                                endtime=rand_time + 180)
        
        st.detrend("demean")
        st.filter("bandpass", freqmin=1, freqmax=10)
        tr = st[0]
        fs = tr.stats.sampling_rate
        segment_samples = int(20 * fs)

        for j in range(9): # 🔁 Cắt 3 phút thành 9 đoạn 20 giây
            start_idx = j * segment_samples
            end_idx = start_idx + segment_samples
            if end_idx > len(tr.data):
                break
            segment = tr.data[start_idx:end_idx]

            # 📈 Tính phổ tần và năng lượng
            f, t, Sxx = spectrogram(segment, fs=fs, nperseg=256, noverlap=128)
            power_db = 10 * np.log10(Sxx + 1e-10)
            avg_power = np.mean(power_db)
            print(f"[Noise {i}, Segment {j}] Avg Power: {avg_power:.2f} dB")

            fig, ax = plt.subplots(figsize=(6, 4))

            # Vẽ spectrogram
            t_uniform = np.linspace(0, 20, Sxx.shape[1])
            pcm = ax.pcolormesh(t_uniform, f, power_db, shading='gouraud',
                                cmap='inferno', vmin=-80, vmax=40)

            # Tắt tất cả các thành phần không cần thiết
            ax.axis('off')  # Tắt trục
            for spine in ax.spines.values():
                spine.set_visible(False)

            # Không colorbar, không title, không nhãn trục
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

            # Lưu ảnh không viền trắng
            plt.savefig(f"noise/{STATION}_noise_{i:03}_{j:02}.png", bbox_inches='tight', pad_inches=0)
            plt.close()

        print(f"✅ Noise {i} xong.")
    except Exception as e:
        print(f"⚠️ Bỏ qua noise {i}: {e}")

# Data augmentation