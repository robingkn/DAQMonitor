import sys
import random
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import pyqtgraph as pg


class LivePlotWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Live Data (time in ms)")
        self.setLabel('left', 'Value')
        self.setLabel('bottom', 'Time (ms)')
        self.showGrid(x=True, y=True)
        self.curve = self.plot(pen='r')

        self.x_data = []
        self.y_data = []

    def update_plot(self, x, y):
        self.x_data.append(x)
        self.y_data.append(y)

        # Keep only the last 10 seconds of data (adjust as needed)
        ten_seconds_ago = x - 10_000
        while self.x_data and self.x_data[0] < ten_seconds_ago:
            self.x_data.pop(0)
            self.y_data.pop(0)

        self.curve.setData(self.x_data, self.y_data)
        self.setXRange(max(0, x - 10_000), x)  # Show last 10 seconds


class LivePlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Plotting with PyQtGraph")
        self.setGeometry(100, 100, 800, 400)

        self.plot_widget = LivePlotWidget()
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.plot_widget)
        self.setCentralWidget(central_widget)

        self.start_time = time.time()  # Record start time

        self.timer = QTimer()
        self.timer.setInterval(50)  # update every 50 ms
        self.timer.timeout.connect(self.update_data)
        self.timer.start()

    def update_data(self):
        now = time.time()
        elapsed_ms = (now - self.start_time) * 1000  # relative time in ms
        new_value = random.uniform(0, 10)
        self.plot_widget.update_plot(elapsed_ms, new_value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LivePlotWindow()
    window.show()
    sys.exit(app.exec_())
