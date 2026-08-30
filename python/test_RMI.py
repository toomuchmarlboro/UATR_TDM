import sys
import socket
import struct
import time
import math
import queue
import requests

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QFormLayout, QSpinBox, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRectF, QPointF, QTimer
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QPolygonF, QPainterPath
)

from brping import Ping1D


# ==========================================================
# CONTROL STATION - Helper Functions
# ==========================================================
def calc_checksum(payload):
    """Menghitung XOR checksum sesuai format NMEA."""
    chk = 0
    for c in payload:
        chk ^= ord(c)
    return f"{chk:02X}"


def hex_to_float(hex_str):
    """Mengubah hex unpadded menjadi float IEEE-754 32-bit."""
    try:
        if not hex_str:
            return 0.0
        val = int(hex_str, 16)
        return struct.unpack('>f', struct.pack('>I', val))[0]
    except Exception:
        return 0.0


# ==========================================================
# CONTROL STATION - Custom Instruments
# ==========================================================
class CompassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.yaw = 0.0

    def setYaw(self, yaw):
        self.yaw = yaw
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor(30, 30, 30))

        cx = rect.width() / 2
        cy = rect.height() / 2
        radius = min(cx, cy) - 15

        painter.translate(cx, cy)

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(int(-5), int(-radius + 15), "N")
        painter.drawText(int(-5), int(radius - 5), "S")
        painter.drawText(int(radius - 15), 5, "E")
        painter.drawText(int(-radius + 5), 5, "W")

        painter.save()
        painter.rotate(self.yaw)

        red_poly = QPolygonF([
            QPointF(-5, 0), QPointF(5, 0), QPointF(0, -radius + 20)
        ])
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(red_poly)

        white_poly = QPolygonF([
            QPointF(-5, 0), QPointF(5, 0), QPointF(0, radius - 20)
        ])
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawPolygon(white_poly)
        painter.restore()

        painter.setPen(QColor(255, 255, 0))
        painter.drawText(int(-cx + 5), int(cy - 5), f"Yaw: {self.yaw:.1f}°")


class AttitudeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.roll = 0.0
        self.pitch = 0.0

    def setAttitude(self, roll, pitch):
        self.roll = roll
        self.pitch = pitch
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        cx = rect.width() / 2
        cy = rect.height() / 2
        radius = min(cx, cy) - 10

        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), radius, radius)
        painter.setClipPath(path)

        painter.translate(cx, cy)
        painter.save()
        painter.rotate(-self.roll)
        pitch_offset = self.pitch * 2.0
        painter.translate(0, pitch_offset)

        painter.setBrush(QColor(0, 120, 255))
        painter.drawRect(QRectF(-radius * 2, -radius * 2, radius * 4, radius * 2))

        painter.setBrush(QColor(139, 69, 19))
        painter.drawRect(QRectF(-radius * 2, 0, radius * 4, radius * 2))

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(int(-radius * 2), 0, int(radius * 2), 0)
        painter.restore()

        painter.setPen(QPen(QColor(255, 255, 0), 3))
        painter.drawLine(-30, 0, -10, 0)
        painter.drawLine(10, 0, 30, 0)
        painter.drawPoint(0, 0)

        painter.setClipping(False)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(int(-cx + 5), int(cy - 15), f"R: {self.roll:.1f}°")
        painter.drawText(int(-cx + 5), int(cy - 2), f"P: {self.pitch:.1f}°")


# ==========================================================
# CONTROL STATION - Network Worker
# ==========================================================
class DataFetcherThread(QThread):
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, ip, mode):
        super().__init__()
        self.ip = ip
        self.mode = mode
        self.running = True
        self.tcp_sock = None

    def run(self):
        if self.mode == "TCP Telemetry":
            self._run_tcp()
        else:
            self._run_http()

    def _run_http(self):
        url = f"http://{self.ip}/data"
        http_keys = [
            "leak", "vmon", "depth", "depthTemp", "depthRho",
            "dio", "ahrsRol", "ahrsPit", "ahrsYaw", "ahrsLost",
            "ahrsAge", "depthLost", "depthAge", "core0depth"
        ]

        self.status_changed.emit("Connected / HTTP polling")

        while self.running:
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    data = resp.json()
                    filtered = {k: data.get(k, 0) for k in http_keys}
                    res = {
                        "Leak": filtered.get("leak", 0),
                        "Vmon": filtered.get("vmon", 0),
                        "Depth": filtered.get("depth", 0),
                        "Depth temp": filtered.get("depthTemp", 0),
                        "Roll": filtered.get("ahrsRol", 0),
                        "Pitch": filtered.get("ahrsPit", 0),
                        "Yaw": filtered.get("ahrsYaw", 0),
                        "Digital i/o": filtered.get("dio", 0),
                        "Raw HTTP": str(filtered)
                    }
                    self.data_ready.emit(res)
                else:
                    self.error_occurred.emit(f"HTTP status: {resp.status_code}")
            except Exception as e:
                if self.running:
                    self.error_occurred.emit(f"HTTP Error: {str(e)}")

            for _ in range(5):
                if not self.running:
                    break
                time.sleep(0.1)

    def _run_tcp(self):
        try:
            self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_sock.settimeout(3)
            self.tcp_sock.connect((self.ip, 8080))
            self.status_changed.emit("Connected / TCP 8080")
        except Exception as e:
            if self.running:
                self.error_occurred.emit(f"Gagal konek TCP: {str(e)}")
            return

        buffer = ""
        while self.running:
            try:
                chunk = self.tcp_sock.recv(128)
                if not chunk:
                    if self.running:
                        self.error_occurred.emit("Koneksi ditutup oleh server")
                    break

                buffer += chunk.decode('ascii', errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()

                    if line.startswith('$') and '*' in line:
                        payload, chksum = line[1:].rsplit('*', 1)
                        if calc_checksum(payload) == chksum:
                            parts = payload.split(',')
                            if parts[0] == 'GDAT2' and len(parts) >= 12:
                                res = {
                                    "Leak": hex_to_float(parts[1]),
                                    "Vmon": hex_to_float(parts[2]),
                                    "Depth": hex_to_float(parts[3]),
                                    "Depth temp": hex_to_float(parts[4]),
                                    "Roll": hex_to_float(parts[5]),
                                    "Pitch": hex_to_float(parts[6]),
                                    "Yaw": hex_to_float(parts[7]),
                                    "Digital i/o": int(parts[10], 16)
                                }
                                self.data_ready.emit(res)
            except socket.timeout:
                pass
            except Exception as e:
                if self.running:
                    self.error_occurred.emit(f"TCP Read Error: {str(e)}")
                break

        self._close_socket()

    def send_valve_cmd(self, action):
        cmd_str = "$RMCMD,1*48\r\n" if action == "OPEN" else "$RMCMD,5*4C\r\n"
        try:
            if self.mode == "TCP Telemetry" and self.tcp_sock:
                self.tcp_sock.sendall(cmd_str.encode('ascii'))
            else:
                temp_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_s.settimeout(1)
                temp_s.connect((self.ip, 8080))
                temp_s.sendall(cmd_str.encode('ascii'))
                temp_s.close()
        except Exception as e:
            self.error_occurred.emit(
                f"Gagal mengirim perintah {action}: {str(e)}"
            )

    def _close_socket(self):
        if self.tcp_sock:
            try:
                self.tcp_sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.tcp_sock.close()
            except Exception:
                pass
            self.tcp_sock = None

    def stop(self):
        self.running = False
        self._close_socket()


# ==========================================================
# PING1D - TCP Socket Wrapper
# ==========================================================
class TCPSocketIO:
    def __init__(self, ip, port, timeout=2.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((ip, port))

    def read(self, size):
        data = b''
        try:
            while len(data) < size:
                chunk = self.sock.recv(size - len(data))
                if not chunk:
                    break
                data += chunk
            return data
        except socket.timeout:
            return data
        except Exception:
            return data

    def write(self, data):
        try:
            self.sock.sendall(data)
            return len(data)
        except Exception:
            return 0

    def send(self, data):
        return self.write(data)

    def recv(self, size):
        return self.read(size)

    def flush(self):
        pass

    @property
    def in_waiting(self):
        return 1

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


# ==========================================================
# PING1D - Sensor Worker
# ==========================================================
class PingSensorThread(QThread):
    data_updated = pyqtSignal(int, int)
    status_updated = pyqtSignal(str)
    connection_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ip = ""
        self.port = 0
        self.running = False
        self.ping = None
        self.tcp_io = None
        self.cmd_queue = queue.Queue()

    def connect_sensor(self, ip, port):
        if self.isRunning():
            return
        self.ip = ip
        self.port = int(port)
        self.running = True
        self.start()

    def _close_connection(self):
        # Tutup wrapper TCP lama jika fallback sedang digunakan.
        if self.tcp_io:
            try:
                self.tcp_io.close()
            except Exception:
                pass
            self.tcp_io = None

        # connect_tcp() milik brping membuat iodev sendiri.
        # Tutup juga transport native tersebut saat disconnect/exit.
        if self.ping is not None:
            iodev = getattr(self.ping, "iodev", None)
            if iodev is not None:
                try:
                    iodev.close()
                except Exception:
                    pass

    def disconnect_sensor(self):
        self.running = False
        self._close_connection()
        if self.isRunning():
            self.wait(3000)

    def send_command(self, cmd_type, value):
        if self.running:
            self.cmd_queue.put((cmd_type, value))

    def run(self):
        self.ping = Ping1D()

        try:
            # PENTING:
            # Jangan langsung assign socket ke self.ping.iodev pada brping versi
            # baru. connect_tcp() menyiapkan fungsi transport internal seperti
            # update_input_buffer yang dibutuhkan initialize()/get_distance().
            if hasattr(self.ping, "connect_tcp"):
                self.ping.connect_tcp(self.ip, self.port)
            else:
                # Compatibility fallback untuk brping versi lama yang belum
                # memiliki connect_tcp().
                self.tcp_io = TCPSocketIO(self.ip, self.port)
                self.ping.iodev = self.tcp_io

            # Beri waktu TCP-to-serial converter membuka jalur serial fisik.
            time.sleep(1.0)

            if not self.running:
                self._close_connection()
                return

            if not self.ping.initialize():
                self.connection_error.emit(
                    "Gagal inisialisasi Ping1D. Socket TCP berhasil dibuka, "
                    "tetapi sensor tidak menjawab handshake. Pastikan IP/Port "
                    "benar dan baudrate converter diset 115200."
                )
                self.running = False
                self._close_connection()
                return

            self.status_updated.emit("Terhubung")

        except Exception as e:
            if self.running:
                # Pesan tambahan khusus untuk instalasi brping yang tidak konsisten.
                msg = str(e)
                if "update_input_buffer" in msg:
                    msg += (
                        " | Library brping yang terpasang tampaknya tidak konsisten. "
                        "Coba: python -m pip install --upgrade bluerobotics-ping"
                    )
                self.connection_error.emit(f"Error Koneksi TCP: {msg}")
            self.running = False
            self._close_connection()
            return

        while self.running:
            while not self.cmd_queue.empty():
                cmd, val = self.cmd_queue.get()
                try:
                    if cmd == 'enable':
                        self.ping.set_ping_enable(val)
                    elif cmd == 'gain':
                        self.ping.set_gain_setting(val)
                    elif cmd == 'interval':
                        self.ping.set_ping_interval(val)
                    elif cmd == 'sos':
                        self.ping.set_speed_of_sound(val)
                except Exception:
                    pass

            try:
                data = self.ping.get_distance()
                if data:
                    self.data_updated.emit(
                        data.get("distance", 0),
                        data.get("confidence", 0)
                    )
            except Exception:
                pass

            time.sleep(0.05)

        self._close_connection()
        self.status_updated.emit("Disconnected")


# ==========================================================
# CONTROL STATION PANEL
# ==========================================================
class ControlStationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.last_data_time = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        conn_group = QGroupBox("Control Station Connection")
        conn_layout = QHBoxLayout()
        self.ip_input = QLineEdit("192.168.3.110")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["TCP Telemetry", "HTTP API"])
        self.btn_connect = QPushButton("Connect")
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setEnabled(False)
        self.lbl_status = QLabel("Status: Disconnected")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")

        conn_layout.addWidget(QLabel("Control Station IP:"))
        conn_layout.addWidget(self.ip_input)
        conn_layout.addWidget(QLabel("Mode:"))
        conn_layout.addWidget(self.mode_combo)
        conn_layout.addWidget(self.btn_connect)
        conn_layout.addWidget(self.btn_disconnect)
        conn_layout.addWidget(self.lbl_status)
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        ctrl_group = QGroupBox("Valve Controls - TCP Port 8080")
        ctrl_layout = QHBoxLayout()
        self.btn_open = QPushButton("OPEN Valve (RMCMD_ENABLE_1)")
        self.btn_close = QPushButton("CLOSE Valve (RMCMD_DISABLE_1)")
        self.btn_open.setStyleSheet("background-color: #90EE90;")
        self.btn_close.setStyleSheet("background-color: #FFB6C1;")
        self.btn_open.setEnabled(False)
        self.btn_close.setEnabled(False)
        ctrl_layout.addWidget(self.btn_open)
        ctrl_layout.addWidget(self.btn_close)
        ctrl_group.setLayout(ctrl_layout)
        layout.addWidget(ctrl_group)

        data_layout = QHBoxLayout()

        inst_group = QGroupBox("Visual Instruments")
        inst_layout = QHBoxLayout()
        self.compass_widget = CompassWidget()
        self.attitude_widget = AttitudeWidget()
        inst_layout.addWidget(self.compass_widget)
        inst_layout.addWidget(self.attitude_widget)
        inst_group.setLayout(inst_layout)
        data_layout.addWidget(inst_group, stretch=1)

        text_group = QGroupBox("Telemetry Text Data")
        text_layout = QVBoxLayout()
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet(
            "font-family: Consolas, monospace; background-color: #f4f4f4;"
        )
        text_layout.addWidget(self.output_display)
        text_group.setLayout(text_layout)
        data_layout.addWidget(text_group, stretch=1)

        layout.addLayout(data_layout)

        self.btn_connect.clicked.connect(self.start_connection)
        self.btn_disconnect.clicked.connect(self.stop_connection)
        self.btn_open.clicked.connect(self.open_valve)
        self.btn_close.clicked.connect(self.close_valve)

    def start_connection(self):
        ip = self.ip_input.text().strip()
        mode = self.mode_combo.currentText()

        if not ip:
            QMessageBox.warning(self, "Input Error", "IP Control Station belum diisi.")
            return

        if self.worker:
            self.stop_connection()

        self.output_display.clear()
        self.last_data_time = None
        self.worker = DataFetcherThread(ip, mode)
        self.worker.data_ready.connect(self.update_display)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.status_changed.connect(self.update_status)
        self.worker.start()

        self.btn_connect.setEnabled(False)
        self.ip_input.setEnabled(False)
        self.mode_combo.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.btn_close.setEnabled(True)
        self.update_status("Connecting...")

    def stop_connection(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)
            self.worker = None

        self.btn_connect.setEnabled(True)
        self.ip_input.setEnabled(True)
        self.mode_combo.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.output_display.append("\n--- Disconnected ---")
        self.compass_widget.setYaw(0.0)
        self.attitude_widget.setAttitude(0.0, 0.0)
        self.last_data_time = None
        self.update_status("Disconnected")

    def open_valve(self):
        if self.worker:
            self.worker.send_valve_cmd("OPEN")

    def close_valve(self):
        if self.worker:
            self.worker.send_valve_cmd("CLOSE")

    def update_status(self, msg):
        self.lbl_status.setText(f"Status: {msg}")
        if msg.startswith("Connected"):
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
        elif "Connecting" in msg:
            self.lbl_status.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.lbl_status.setStyleSheet("color: red; font-weight: bold;")

    def update_display(self, data):
        self.last_data_time = time.monotonic()

        roll = data.get("Roll", 0.0)
        pitch = data.get("Pitch", 0.0)
        yaw = data.get("Yaw", 0.0)

        self.compass_widget.setYaw(yaw)
        self.attitude_widget.setAttitude(roll, pitch)

        if "Raw HTTP" in data:
            disp_data = data.copy()
            raw_text = disp_data.pop("Raw HTTP")
            lines = [
                f"{k:<12}: {v:.2f}" if isinstance(v, float)
                else f"{k:<12}: {v}"
                for k, v in disp_data.items()
            ]
            self.output_display.setText(
                "\n".join(lines) + f"\n\n[Full Filtered Data]:\n{raw_text}"
            )
        else:
            lines = [
                f"{k:<12}: {v:.2f}" if isinstance(v, float)
                else f"{k:<12}: {v}"
                for k, v in data.items()
            ]
            self.output_display.setText("\n".join(lines))

    def show_error(self, err_msg):
        self.output_display.append(f"\n[ERROR] {err_msg}")
        self.update_status("Error")

        fatal = (
            "Gagal konek TCP" in err_msg or
            "TCP Read Error" in err_msg or
            "Koneksi ditutup" in err_msg
        )
        if fatal:
            self.stop_connection()

    def shutdown(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)
            self.worker = None


# ==========================================================
# PING1D PANEL
# ==========================================================
class Ping1DPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.last_data_time = None
        self.sensor_thread = PingSensorThread()
        self.sensor_thread.data_updated.connect(self.update_data)
        self.sensor_thread.status_updated.connect(self.update_status)
        self.sensor_thread.connection_error.connect(self.show_error)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        conn_group = QGroupBox("Ping1D TCP / USR Connection")
        conn_layout = QFormLayout()

        self.ip_input = QLineEdit("192.168.3.122")
        self.port_input = QLineEdit("8080")
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.toggle_connection)
        self.lbl_status = QLabel("Status: Disconnected")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")

        conn_layout.addRow("Ping1D IP Address:", self.ip_input)
        conn_layout.addRow("TCP Port:", self.port_input)
        conn_layout.addRow(self.btn_connect)
        conn_layout.addRow(self.lbl_status)
        conn_group.setLayout(conn_layout)

        read_group = QGroupBox("Ping1D Sensor Output")
        read_layout = QVBoxLayout()

        self.lbl_distance = QLabel("Distance: 0 mm")
        self.lbl_distance.setStyleSheet(
            "font-size: 30px; font-weight: bold; color: #0055A4;"
        )
        self.lbl_distance.setAlignment(Qt.AlignCenter)

        self.lbl_confidence = QLabel("Confidence: 0 %")
        self.lbl_confidence.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #007F00;"
        )
        self.lbl_confidence.setAlignment(Qt.AlignCenter)

        read_layout.addWidget(self.lbl_distance)
        read_layout.addWidget(self.lbl_confidence)
        read_group.setLayout(read_layout)

        settings_group = QGroupBox("Ping1D Sensor Settings")
        settings_layout = QFormLayout()

        self.btn_ping_enable = QPushButton("Ping Enabled")
        self.btn_ping_enable.setCheckable(True)
        self.btn_ping_enable.setChecked(True)
        self.btn_ping_enable.setStyleSheet("background-color: lightgreen;")
        self.btn_ping_enable.clicked.connect(self.toggle_ping)

        self.cb_gain = QComboBox()
        self.cb_gain.addItems([
            "0 (0.6)", "1 (1.8)", "2 (5.5)", "3 (12.9)",
            "4 (30.2)", "5 (66.1)", "6 (144.0)"
        ])
        self.cb_gain.setCurrentIndex(3)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(10, 5000)
        self.spin_interval.setValue(50)
        self.spin_interval.setSuffix(" ms")

        self.spin_sos = QSpinBox()
        self.spin_sos.setRange(300000, 2000000)
        self.spin_sos.setSingleStep(1000)
        self.spin_sos.setValue(1500000)
        self.spin_sos.setSuffix(" mm/s")

        self.btn_apply_settings = QPushButton("Apply Settings")
        self.btn_apply_settings.clicked.connect(self.apply_settings)
        self.btn_apply_settings.setEnabled(False)

        settings_layout.addRow("Ping Toggle:", self.btn_ping_enable)
        settings_layout.addRow("Gain:", self.cb_gain)
        settings_layout.addRow("Interval:", self.spin_interval)
        settings_layout.addRow("Sound Velocity:", self.spin_sos)
        settings_layout.addRow(self.btn_apply_settings)
        settings_group.setLayout(settings_layout)

        main_layout.addWidget(conn_group)
        main_layout.addWidget(read_group)
        main_layout.addWidget(settings_group)
        main_layout.addStretch(1)

    def toggle_connection(self):
        if not self.sensor_thread.running:
            ip = self.ip_input.text().strip()
            port_text = self.port_input.text().strip()

            if not ip:
                QMessageBox.warning(self, "Input Error", "IP Ping1D belum diisi.")
                return

            try:
                port = int(port_text)
                if not (1 <= port <= 65535):
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Port Ping1D tidak valid.")
                return

            self.last_data_time = None
            self.update_status("Connecting...")
            self.sensor_thread.connect_sensor(ip, port)
            self.btn_connect.setText("Disconnect")
            self.ip_input.setEnabled(False)
            self.port_input.setEnabled(False)
            self.btn_apply_settings.setEnabled(True)
        else:
            self.sensor_thread.disconnect_sensor()
            self._set_disconnected_ui()

    def _set_disconnected_ui(self):
        self.last_data_time = None
        self.update_status("Disconnected")
        self.btn_connect.setText("Connect")
        self.ip_input.setEnabled(True)
        self.port_input.setEnabled(True)
        self.btn_apply_settings.setEnabled(False)

    def toggle_ping(self):
        if self.btn_ping_enable.isChecked():
            self.btn_ping_enable.setText("Ping Enabled")
            self.btn_ping_enable.setStyleSheet("background-color: lightgreen;")
            self.sensor_thread.send_command('enable', 1)
        else:
            self.btn_ping_enable.setText("Ping Disabled")
            self.btn_ping_enable.setStyleSheet("background-color: lightcoral;")
            self.sensor_thread.send_command('enable', 0)

    def apply_settings(self):
        gain = self.cb_gain.currentIndex()
        interval = self.spin_interval.value()
        sos = self.spin_sos.value()

        self.sensor_thread.send_command('gain', gain)
        self.sensor_thread.send_command('interval', interval)
        self.sensor_thread.send_command('sos', sos)

        QMessageBox.information(
            self,
            "Success",
            "Setting Ping1D telah dikirim melalui TCP."
        )

    def update_data(self, distance, confidence):
        self.last_data_time = time.monotonic()
        self.lbl_distance.setText(f"Distance: {distance} mm")
        self.lbl_confidence.setText(f"Confidence: {confidence} %")

    def update_status(self, msg):
        self.lbl_status.setText(f"Status: {msg}")
        if msg == "Terhubung":
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
        elif "Connecting" in msg:
            self.lbl_status.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.lbl_status.setStyleSheet("color: red; font-weight: bold;")

        if msg == "Disconnected" and not self.sensor_thread.running:
            self.btn_connect.setText("Connect")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.btn_apply_settings.setEnabled(False)

    def show_error(self, err_msg):
        self.sensor_thread.running = False
        self._set_disconnected_ui()
        QMessageBox.critical(self, "Ping1D Connection Error", err_msg)

    def shutdown(self):
        if self.sensor_thread.running or self.sensor_thread.isRunning():
            self.sensor_thread.disconnect_sensor()


# ==========================================================
# COMBINED GUI - Single Window Dashboard
# ==========================================================
class CombinedGUI(QMainWindow):
    STREAM_TIMEOUT_S = 2.0

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Station + Ping1D Dashboard")
        self.resize(1350, 760)

        self.control_panel = ControlStationPanel()
        self.ping_panel = Ping1DPanel()

        root = QWidget()
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Kedua GUI tampil bersamaan dalam satu window.
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        content_layout.addWidget(self.control_panel, stretch=3)
        content_layout.addWidget(self.ping_panel, stretch=2)
        main_layout.addLayout(content_layout, stretch=1)

        # Status stream ditempatkan di kiri bawah window.
        status_group = QGroupBox("Stream Status")
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(10, 4, 10, 4)
        status_layout.setSpacing(24)

        self.lbl_cs_stream = QLabel()
        self.lbl_ping_stream = QLabel()
        self.lbl_cs_stream.setMinimumWidth(310)
        self.lbl_ping_stream.setMinimumWidth(310)

        status_layout.addWidget(self.lbl_cs_stream)
        status_layout.addWidget(self.lbl_ping_stream)
        status_layout.addStretch(1)
        main_layout.addWidget(status_group, alignment=Qt.AlignLeft)

        self.setCentralWidget(root)

        # Cek freshness data secara periodik.
        self.stream_timer = QTimer(self)
        self.stream_timer.setInterval(250)
        self.stream_timer.timeout.connect(self.update_stream_status)
        self.stream_timer.start()
        self.update_stream_status()

    @staticmethod
    def _set_stream_label(label, name, ip, state):
        if state == "STREAMING":
            dot = "●"
            color = "#008000"
        elif state == "NO DATA":
            dot = "●"
            color = "#d47b00"
        else:
            dot = "●"
            color = "#c00000"

        label.setText(f"{dot} {name} [{ip}] : {state}")
        label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 12px;"
        )

    def _control_stream_state(self, now):
        panel = self.control_panel

        if panel.worker is None:
            return "DISCONNECTED"

        if panel.last_data_time is not None:
            if (now - panel.last_data_time) <= self.STREAM_TIMEOUT_S:
                return "STREAMING"

        return "NO DATA"

    def _ping_stream_state(self, now):
        panel = self.ping_panel

        if not panel.sensor_thread.running:
            return "DISCONNECTED"

        if panel.last_data_time is not None:
            if (now - panel.last_data_time) <= self.STREAM_TIMEOUT_S:
                return "STREAMING"

        return "NO DATA"

    def update_stream_status(self):
        now = time.monotonic()
        cs_ip = self.control_panel.ip_input.text().strip() or "-"
        ping_ip = self.ping_panel.ip_input.text().strip() or "-"

        self._set_stream_label(
            self.lbl_cs_stream,
            "Control Station",
            cs_ip,
            self._control_stream_state(now)
        )
        self._set_stream_label(
            self.lbl_ping_stream,
            "Ping1D",
            ping_ip,
            self._ping_stream_state(now)
        )

    def closeEvent(self, event):
        self.stream_timer.stop()
        self.control_panel.shutdown()
        self.ping_panel.shutdown()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CombinedGUI()
    window.show()
    sys.exit(app.exec_())