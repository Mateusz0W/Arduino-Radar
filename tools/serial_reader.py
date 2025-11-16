import serial
import time
import csv

class SerialReader:
    def __init__(self, port: str, baudrate: int, timeout: int=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2)

    def save_data_to_csv(self, filename: str) -> None:
        data = []
        print("start reading")
        while True:
            line = self.ser.readline().decode('utf-8').strip()

            if line == "END":
                print("end reading")
                break
            elif line:  
                try:
                    angle_str, dist_str = line.split(",")
                    data.append((float(angle_str), float(dist_str)))

                except ValueError:
                    print("Incorrect data format:", line)


        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)      

        print("data saved in file")          


if __name__ == "__main__":
    ser = SerialReader("COM4", 115200)
    ser.save_data_to_csv("../data/sample_data2.csv")