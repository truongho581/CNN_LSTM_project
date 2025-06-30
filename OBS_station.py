
import os
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

client = Client("IRIS")
start_time = UTCDateTime("2014-07-17")
end_time = UTCDateTime("2015-08-27")

# Các thông tin cho trạm OBS
NETWORK = "7D"
CHANNEL = "BHZ"
LOCATION = "--"

#station_data =  [station name, lat, lon, elevation]

# Trạm để lấy data test
#station_data = ["FS10D", 40.4328, -124.6940, -1153.8]  #2014-07-17	2015-08-27
station_data = ["FS13D", 40.4937, -124.8034, -2291.2]
# Trạm để lấy data train/val
#station_data = ["M11B", 42.9320, -125.0171, -1109.0]   #2012-09-02	2013-06-18   58 sự kiện
#station_data = ["M12B", 42.1840, -124.9461, -1045.0]   #2012-09-02	2013-06-18   115 sự kiện
#station_data = ["FS41D", 40.6124, -124.7310, -1079.3]  #2014-07-16	2015-08-28   124 sự kiện
#station_data = ["FS16D", 40.5378, -124.7468, -1080.4]  #2014-07-16	2015-08-28   121 sự kiện

# Hàm lấy danh sách trạm OBS
def get_station_info():
    inv = client.get_stations(
        network=NETWORK,
        station="*",
        channel=CHANNEL,
        starttime=start_time,
        endtime=end_time,
        level="channel"
    )

    stations = []
    network_info = ""
    for net in inv:
        network_info = f"{net.code} - {net.description}"  # ✅ Lấy thông tin mạng
        for sta in net:
            lat = sta.latitude
            lon = sta.longitude
            elev = sta.elevation
            if elev is not None and elev < 0:  
                stations.append((sta.code, lat, lon, elev))

    return network_info, stations


if __name__ == "__main__":
    print(f"📡 Trạm OBS thuộc mạng {NETWORK} có kênh {CHANNEL} trong khu vực:")

    network_info, station_list = get_station_info()
    print("📘 Network Info:", network_info)

    for sta_code, lat, lon, elev in station_list:
        print(f'"{sta_code}", {lat:.4f}, {lon:.4f}, {elev:.1f}')

