import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import nidaqmx
from nidaqmx.constants import AcquisitionType


class LivePlotWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Live Data from NI-DAQ (time in ms)")
        self.setLabel('left', 'Voltage (V)')
        self.setLabel('bottom', 'Time (ms)')
        self.showGrid(x=True, y=True)
        self.curve = self.plot(pen='g')

        self.x_data = []
        self.y_data = []

    def update_plot(self, x_list, y_list):
        self.x_data.extend(x_list)
        self.y_data.extend(y_list)

        # Keep only last 10 seconds of data
        ten_seconds_ago = x_list[-1] - 10_000
        while self.x_data and self.x_data[0] < ten_seconds_ago:
            self.x_data.pop(0)
            self.y_data.pop(0)

        self.curve.setData(self.x_data, self.y_data)
        self.setXRange(max(0, x_list[-1] - 10_000), x_list[-1])


class LivePlotWindow(QMainWindow):
    def __init__(self, channel="Dev1/ai0", sample_rate=1000):
        super().__init__()
        self.setWindowTitle("NI-DAQ Live Plotting with PyQtGraph")
        self.setGeometry(100, 100, 800, 400)

        self.plot_widget = LivePlotWidget()
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.plot_widget)
        self.setCentralWidget(central_widget)

        self.start_time = time.time()

        # Setup NI-DAQmx task for continuous acquisition
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(channel)
        self.task.timing.cfg_samp_clk_timing(rate=sample_rate,
                                             sample_mode=AcquisitionType.CONTINUOUS,
                                             samps_per_chan=1000)  # large buffer

        self.task.start()

        self.sample_rate = sample_rate
        self.timer = QTimer()
        self.timer.setInterval(50)  # check every 50ms
        self.timer.timeout.connect(self.update_data)
        self.timer.start()

    def update_data(self):
        try:
            # Read all available samples without blocking
            values = self.task.read(number_of_samples_per_channel=-1)
            if not values:
                return
            if not isinstance(values, list):
                values = [values]

            now = time.time()
            elapsed_ms_list = [(now - self.start_time) * 1000] * len(values)

            # For better timing, generate relative timestamps spaced by sample period
            sample_period_ms = 1000 / self.sample_rate
            # Adjust timestamps backwards per sample count
            elapsed_ms_list = [elapsed_ms_list[-1] - sample_period_ms * (len(values) - 1 - i) for i in range(len(values))]

            self.plot_widget.update_plot(elapsed_ms_list, values)
        except Exception as e:
            print("Error reading from NI-DAQ:", e)

    def closeEvent(self, event):
        self.task.stop()
        self.task.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LivePlotWindow(channel="Dev1/ai0", sample_rate=1000)
    window.show()

    sys.exit(app.exec_())
