# 📡 BLE Touch Sensor Logger

This project enables wireless touch detection using an **Arduino Nano 33 BLE** and a **Python data logger** via Bluetooth Low Energy (BLE). It detects touches using a capacitive sensor and logs events in real-time to a CSV file.

---

## 🛠 Hardware & Software

- Arduino Nano 33 BLE
- Capacitive touch sensor (with 10MΩ resistor between send and receive pins)
- PC/Mac with Bluetooth and Python 3.7+
- BLE-enabled host (tested with `bleak` on Linux/macOS)

---

## 📁 Directory Structure

```
ble-touch-logger/
├── ble_touch/
│   └── ble_touch.ino           # Arduino sketch to send BLE touch messages
├──     ble_recieve.py          # Python script to log BLE data and save to CSV
├── README.md                   # Project overview and setup instructions
└── requirements.txt            # Python dependencies
```

---

## 🚀 Getting Started

### 1. Flash the Arduino

- Open `ble_touch/ble_touch.ino` in the Arduino IDE.
- Set board to **Arduino Nano 33 BLE**.
- Connect and upload the sketch.

**Capacitive Sensor Setup:**

View Diagram

---

### 2. Run the Python Logger

Install dependencies:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python ble_recieve.py
```

---

### 3. Controls

| Key | Action                    |
|-----|---------------------------|
| `s` | Start new session         |
| `r` | Toggle recording          |
| `q` | End session & save file   |

CSV files will be saved with timestamps and session names.

---

## ⚙️ BLE UUIDs

Make sure these match in both Arduino and Python files:

```python
MESSAGE_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
MESSAGE_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
```

---

## 📈 Features

- BLE communication from Arduino to host
- Real-time capacitive touch detection
- Toggle-able CSV logging
- Timestamped event data
- Optional plotting using matplotlib

---

## 📦 Python Requirements

Create a `requirements.txt` file with the following:

```
bleak
matplotlib
```

Install via:

```bash
pip install -r requirements.txt
```

---

## 🧠 Future Improvements

- Add real-time plotting
- GUI interface for session control
- Adaptive thresholding or touch calibration UI

---

## 📝 License

MIT License
