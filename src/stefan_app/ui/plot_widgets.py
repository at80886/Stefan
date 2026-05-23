"""Qt drawing widgets for simulation result visualization."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from stefan_app.models import SimulationResult


class SimulationPlotWidget(QWidget):
    """Tabbed result display for temperature, interface, and cloud map views."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result: SimulationResult | None = None
        self.setMinimumSize(520, 360)
        self.setObjectName("simulationPlot")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget(self)
        self.temperature_plot = TemperatureDistributionPlot(self)
        self.interface_plot = InterfaceTimePlot(self)
        self.cloud_plot = TemperatureCloudPlot(self)
        self.tabs.addTab(self.temperature_plot, "温度分布")
        self.tabs.addTab(self.interface_plot, "相界面-时间")
        self.tabs.addTab(self.cloud_plot, "温度云图")
        layout.addWidget(self.tabs)

    def set_result(self, result: SimulationResult | None) -> None:
        """Store result data and update every visualization tab."""
        self._result = result
        self.temperature_plot.set_result(result)
        self.interface_plot.set_result(result)
        self.cloud_plot.set_result(result)


class _ResultCanvas(QWidget):
    """Common painter helpers for result charts."""

    tick_count = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result: SimulationResult | None = None
        self.setMinimumSize(480, 320)

    def set_result(self, result: SimulationResult | None) -> None:
        """Store result data and repaint the canvas."""
        self._result = result
        self.update()

    def _plot_rect(self) -> QRectF:
        return QRectF(self.rect()).adjusted(92, 46, -34, -76)

    def _prepare_painter(self, painter: QPainter, title: str) -> QRectF:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        painter.setFont(_chart_font(10))
        painter.setPen(QColor("#22313a"))
        title_font = _chart_font(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(QRectF(12, 10, self.width() - 24, 22), Qt.AlignmentFlag.AlignCenter, title)
        painter.setFont(_chart_font(9))
        return self._plot_rect()

    def _draw_empty_message(self, painter: QPainter, plot_rect: QRectF) -> None:
        painter.setPen(QColor("#63717a"))
        painter.drawText(plot_rect, Qt.AlignmentFlag.AlignCenter, "运行仿真后将在此显示结果。")

    def _draw_axes(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        *,
        x_minimum: float,
        x_maximum: float,
        y_minimum: float,
        y_maximum: float,
        x_label: str,
        y_label: str,
    ) -> None:
        x_span = _nonzero_span(x_minimum, x_maximum)
        y_span = _nonzero_span(y_minimum, y_maximum)
        painter.setPen(QPen(QColor("#c8d1d8"), 1))
        for index in range(self.tick_count + 1):
            x = plot_rect.left() + plot_rect.width() * index / self.tick_count
            y = plot_rect.bottom() - plot_rect.height() * index / self.tick_count
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

        painter.setPen(QPen(QColor("#52616b"), 1))
        painter.drawRect(plot_rect)
        for index in range(self.tick_count + 1):
            x_value = x_minimum + x_span * index / self.tick_count
            x = plot_rect.left() + plot_rect.width() * index / self.tick_count
            painter.drawLine(QPointF(x, plot_rect.bottom()), QPointF(x, plot_rect.bottom() + 5))
            painter.drawText(
                QRectF(x - 36, plot_rect.bottom() + 8, 72, 18),
                Qt.AlignmentFlag.AlignCenter,
                _format_tick(x_value),
            )

            y_value = y_minimum + y_span * index / self.tick_count
            y = plot_rect.bottom() - plot_rect.height() * index / self.tick_count
            painter.drawLine(QPointF(plot_rect.left() - 5, y), QPointF(plot_rect.left(), y))
            painter.drawText(
                QRectF(34, y - 9, plot_rect.left() - 44, 18),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                _format_tick(y_value),
            )

        painter.setPen(QColor("#2f3f46"))
        painter.drawText(
            QRectF(plot_rect.left(), self.height() - 30, plot_rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            x_label,
        )
        self._draw_rotated_y_label(painter, plot_rect, y_label)

    def _draw_rotated_y_label(self, painter: QPainter, plot_rect: QRectF, label: str) -> None:
        painter.save()
        painter.setPen(QColor("#2f3f46"))
        painter.translate(18, plot_rect.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot_rect.height() / 2.0, -10, plot_rect.height(), 20),
            Qt.AlignmentFlag.AlignCenter,
            label,
        )
        painter.restore()

    def _map_point(
        self,
        plot_rect: QRectF,
        x_value: float,
        y_value: float,
        *,
        x_minimum: float,
        x_maximum: float,
        y_minimum: float,
        y_maximum: float,
    ) -> QPointF:
        x_ratio = (x_value - x_minimum) / _nonzero_span(x_minimum, x_maximum)
        y_ratio = (y_value - y_minimum) / _nonzero_span(y_minimum, y_maximum)
        return QPointF(
            plot_rect.left() + max(0.0, min(1.0, x_ratio)) * plot_rect.width(),
            plot_rect.bottom() - max(0.0, min(1.0, y_ratio)) * plot_rect.height(),
        )

    def _draw_polyline(self, painter: QPainter, points: list[QPointF], color: QColor, width: int = 2) -> None:
        if len(points) < 2:
            return
        painter.setPen(QPen(color, width))
        for start, end in zip(points, points[1:]):
            painter.drawLine(start, end)

    def _draw_line_legend(self, painter: QPainter, plot_rect: QRectF, color: QColor, label: str) -> None:
        legend_y = plot_rect.top() - 20
        legend_x = plot_rect.right() - 148
        painter.setPen(QPen(color, 2))
        painter.drawLine(QPointF(legend_x, legend_y + 8), QPointF(legend_x + 28, legend_y + 8))
        painter.setPen(QColor("#2f3f46"))
        painter.drawText(QRectF(legend_x + 34, legend_y, 114, 18), Qt.AlignmentFlag.AlignLeft, label)


class TemperatureDistributionPlot(_ResultCanvas):
    """Draw final temperature distribution with axes, ticks, and legend."""

    def paintEvent(self, event) -> None:  # noqa: ANN001 - Qt override signature.
        painter = QPainter(self)
        plot_rect = self._prepare_painter(painter, "温度分布图")
        if self._result is None or not self._result.temperatures or not self._result.x_coordinates:
            self._draw_empty_message(painter, plot_rect)
            return

        temperatures = self._result.temperatures[-1]
        x_coordinates = self._result.x_coordinates
        if len(temperatures) < 2 or len(x_coordinates) < 2:
            self._draw_empty_message(painter, plot_rect)
            return

        y_minimum, y_maximum = _padded_range(temperatures)
        x_minimum, x_maximum = x_coordinates[0], x_coordinates[-1]
        self._draw_axes(
            painter,
            plot_rect,
            x_minimum=x_minimum,
            x_maximum=x_maximum,
            y_minimum=y_minimum,
            y_maximum=y_maximum,
            x_label="位置 x (m)",
            y_label="温度 T (K)",
        )
        points = [
            self._map_point(
                plot_rect,
                x,
                temperature,
                x_minimum=x_minimum,
                x_maximum=x_maximum,
                y_minimum=y_minimum,
                y_maximum=y_maximum,
            )
            for x, temperature in zip(x_coordinates, temperatures)
        ]
        self._draw_polyline(painter, points, QColor("#1f77b4"), 2)
        self._draw_line_legend(painter, plot_rect, QColor("#1f77b4"), "最终温度")


class InterfaceTimePlot(_ResultCanvas):
    """Draw interface position over time with axes, ticks, and legend."""

    def paintEvent(self, event) -> None:  # noqa: ANN001 - Qt override signature.
        painter = QPainter(self)
        plot_rect = self._prepare_painter(painter, "相界面-时间图")
        if self._result is None or len(self._result.times) < 2 or len(self._result.positions) < 2:
            self._draw_empty_message(painter, plot_rect)
            return

        x_minimum, x_maximum = self._result.times[0], self._result.times[-1]
        y_minimum, y_maximum = _padded_range(self._result.positions)
        self._draw_axes(
            painter,
            plot_rect,
            x_minimum=x_minimum,
            x_maximum=x_maximum,
            y_minimum=y_minimum,
            y_maximum=y_maximum,
            x_label="时间 t (s)",
            y_label="界面位置 s (m)",
        )
        points = [
            self._map_point(
                plot_rect,
                time,
                position,
                x_minimum=x_minimum,
                x_maximum=x_maximum,
                y_minimum=y_minimum,
                y_maximum=y_maximum,
            )
            for time, position in zip(self._result.times, self._result.positions)
        ]
        self._draw_polyline(painter, points, QColor("#d45500"), 2)
        self._draw_line_legend(painter, plot_rect, QColor("#d45500"), "相界面位置")


class TemperatureCloudPlot(_ResultCanvas):
    """Draw a colored one-dimensional domain map and mark interface location."""

    def _plot_rect(self) -> QRectF:
        return QRectF(self.rect()).adjusted(86, 70, -126, -102)

    def paintEvent(self, event) -> None:  # noqa: ANN001 - Qt override signature.
        painter = QPainter(self)
        plot_rect = self._prepare_painter(painter, "温度云图")
        if (
            self._result is None
            or len(self._result.times) < 1
            or len(self._result.x_coordinates) < 2
            or len(self._result.temperatures) < 1
        ):
            self._draw_empty_message(painter, plot_rect)
            return

        x_minimum, x_maximum = self._result.x_coordinates[0], self._result.x_coordinates[-1]
        final_temperatures = self._result.temperatures[-1]
        temperature_minimum, temperature_maximum = _plain_range(
            [value for row in self._result.temperatures for value in row]
        )
        domain_rect = QRectF(
            plot_rect.left(),
            plot_rect.top() + plot_rect.height() * 0.18,
            plot_rect.width(),
            max(96.0, plot_rect.height() * 0.42),
        )
        self._draw_cloud_cells(
            painter,
            domain_rect,
            final_temperatures=final_temperatures,
            temperature_minimum=temperature_minimum,
            temperature_maximum=temperature_maximum,
            x_minimum=x_minimum,
            x_maximum=x_maximum,
        )
        self._draw_cloud_annotations(
            painter,
            domain_rect,
            x_minimum=x_minimum,
            x_maximum=x_maximum,
        )
        self._draw_cloud_axis(painter, domain_rect, x_minimum=x_minimum, x_maximum=x_maximum)
        self._draw_color_bar(painter, domain_rect, temperature_minimum, temperature_maximum)

    def _draw_cloud_cells(
        self,
        painter: QPainter,
        domain_rect: QRectF,
        *,
        final_temperatures: tuple[float, ...],
        temperature_minimum: float,
        temperature_maximum: float,
        x_minimum: float,
        x_maximum: float,
    ) -> None:
        assert self._result is not None
        x_values = self._result.x_coordinates
        x_edges = _edges(x_values)
        column_indices = _sample_indices(len(x_values), 360)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        for column_index in column_indices:
            if column_index >= len(final_temperatures):
                continue
            x_left = _map_linear(x_edges[column_index], x_minimum, x_maximum, domain_rect.left(), domain_rect.right())
            x_right = _map_linear(x_edges[column_index + 1], x_minimum, x_maximum, domain_rect.left(), domain_rect.right())
            painter.fillRect(
                QRectF(x_left, domain_rect.top(), max(1.0, x_right - x_left), domain_rect.height()),
                _temperature_color(final_temperatures[column_index], temperature_minimum, temperature_maximum),
            )
        highlight = QLinearGradient(domain_rect.topLeft(), domain_rect.bottomLeft())
        highlight.setColorAt(0.0, QColor(255, 255, 255, 92))
        highlight.setColorAt(0.45, QColor(255, 255, 255, 24))
        highlight.setColorAt(1.0, QColor(0, 0, 0, 28))
        painter.fillRect(domain_rect, QBrush(highlight))
        painter.setPen(QPen(QColor("#24323c"), 1))
        painter.drawRect(domain_rect)

    def _draw_cloud_annotations(
        self,
        painter: QPainter,
        domain_rect: QRectF,
        *,
        x_minimum: float,
        x_maximum: float,
    ) -> None:
        assert self._result is not None
        interface_position = self._result.positions[-1] if self._result.positions else x_minimum
        interface_x = _map_linear(interface_position, x_minimum, x_maximum, domain_rect.left(), domain_rect.right())
        interface_x = max(domain_rect.left(), min(domain_rect.right(), interface_x))

        painter.setPen(QColor("#24323c"))
        painter.drawText(
            QRectF(domain_rect.left(), domain_rect.top() - 34, domain_rect.width(), 22),
            Qt.AlignmentFlag.AlignCenter,
            f"最终时刻 t = {self._result.final_time:.4g} s",
        )
        painter.setPen(QColor("#a83220"))
        painter.drawText(
            QRectF(domain_rect.left(), domain_rect.top() + 12, interface_x - domain_rect.left(), 28),
            Qt.AlignmentFlag.AlignCenter,
            "高温区",
        )
        painter.setPen(QColor("#174a91"))
        painter.drawText(
            QRectF(interface_x, domain_rect.top() + 12, domain_rect.right() - interface_x, 28),
            Qt.AlignmentFlag.AlignCenter,
            "低温区",
        )

        painter.setPen(QPen(QColor("#ffffff"), 5))
        painter.drawLine(QPointF(interface_x, domain_rect.top() - 16), QPointF(interface_x, domain_rect.bottom() + 16))
        painter.setPen(QPen(QColor("#123fbb"), 3))
        painter.drawLine(QPointF(interface_x, domain_rect.top() - 18), QPointF(interface_x, domain_rect.bottom() + 18))
        painter.setPen(QColor("#123fbb"))
        painter.drawText(
            QRectF(interface_x - 72, domain_rect.top() - 62, 144, 22),
            Qt.AlignmentFlag.AlignCenter,
            "相界面 x = s(t)",
        )
        painter.setPen(QPen(QColor("#123fbb"), 1))
        painter.drawLine(QPointF(interface_x, domain_rect.top() - 40), QPointF(interface_x, domain_rect.top() - 18))

    def _draw_cloud_axis(self, painter: QPainter, domain_rect: QRectF, *, x_minimum: float, x_maximum: float) -> None:
        axis_y = domain_rect.bottom() + 30
        painter.setPen(QPen(QColor("#52616b"), 1))
        painter.drawLine(QPointF(domain_rect.left(), axis_y), QPointF(domain_rect.right(), axis_y))
        x_span = _nonzero_span(x_minimum, x_maximum)
        for index in range(self.tick_count + 1):
            x_value = x_minimum + x_span * index / self.tick_count
            x = domain_rect.left() + domain_rect.width() * index / self.tick_count
            painter.drawLine(QPointF(x, axis_y - 5), QPointF(x, axis_y + 5))
            painter.drawText(QRectF(x - 40, axis_y + 8, 80, 18), Qt.AlignmentFlag.AlignCenter, _format_tick(x_value))
        painter.setPen(QColor("#2f3f46"))
        painter.drawText(
            QRectF(domain_rect.left(), axis_y + 34, domain_rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "位置 x (m)",
        )

    def _draw_color_bar(
        self,
        painter: QPainter,
        domain_rect: QRectF,
        temperature_minimum: float,
        temperature_maximum: float,
    ) -> None:
        bar_rect = QRectF(domain_rect.right() + 24, domain_rect.top(), 18, domain_rect.height())
        gradient = QLinearGradient(bar_rect.left(), bar_rect.top(), bar_rect.left(), bar_rect.bottom())
        gradient.setColorAt(0.0, _temperature_color(temperature_maximum, temperature_minimum, temperature_maximum))
        gradient.setColorAt(
            0.35,
            _temperature_color(
                temperature_minimum + 0.65 * (temperature_maximum - temperature_minimum),
                temperature_minimum,
                temperature_maximum,
            ),
        )
        gradient.setColorAt(
            0.65,
            _temperature_color(
                temperature_minimum + 0.35 * (temperature_maximum - temperature_minimum),
                temperature_minimum,
                temperature_maximum,
            ),
        )
        gradient.setColorAt(1.0, _temperature_color(temperature_minimum, temperature_minimum, temperature_maximum))
        painter.fillRect(bar_rect, QBrush(gradient))
        painter.setPen(QPen(QColor("#52616b"), 1))
        painter.drawRect(bar_rect)
        span = _nonzero_span(temperature_minimum, temperature_maximum)
        for index in range(self.tick_count + 1):
            ratio = index / self.tick_count
            y = bar_rect.bottom() - bar_rect.height() * ratio
            value = temperature_minimum + span * ratio
            painter.drawLine(QPointF(bar_rect.right(), y), QPointF(bar_rect.right() + 5, y))
            painter.drawText(
                QRectF(bar_rect.right() + 8, y - 9, 68, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                _format_tick(value),
            )
        painter.drawText(
            QRectF(bar_rect.left() - 10, bar_rect.top() - 26, 92, 18),
            Qt.AlignmentFlag.AlignLeft,
            "温度 (K)",
        )


def _chart_font(point_size: int) -> QFont:
    return QFont("Microsoft YaHei UI", point_size)


def _map_linear(value: float, source_minimum: float, source_maximum: float, target_minimum: float, target_maximum: float) -> float:
    ratio = (value - source_minimum) / _nonzero_span(source_minimum, source_maximum)
    ratio = max(0.0, min(1.0, ratio))
    return target_minimum + ratio * (target_maximum - target_minimum)


def _nonzero_span(minimum: float, maximum: float) -> float:
    return maximum - minimum if abs(maximum - minimum) > 1.0e-12 else 1.0


def _plain_range(values: tuple[float, ...] | list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    minimum = min(values)
    maximum = max(values)
    if abs(maximum - minimum) < 1.0e-12:
        return minimum, minimum + 1.0
    return minimum, maximum


def _padded_range(values: tuple[float, ...] | list[float]) -> tuple[float, float]:
    minimum, maximum = _plain_range(values)
    span = _nonzero_span(minimum, maximum)
    padding = span * 0.08
    return minimum - padding, maximum + padding


def _format_tick(value: float) -> str:
    if abs(value) >= 1000 or (0 < abs(value) < 0.001):
        return f"{value:.2e}"
    if abs(value) >= 10:
        return f"{value:.2f}"
    return f"{value:.4g}"


def _edges(values: tuple[float, ...]) -> list[float]:
    if len(values) == 1:
        return [values[0] - 0.5, values[0] + 0.5]
    edges = [values[0]]
    edges.extend((left + right) / 2.0 for left, right in zip(values, values[1:]))
    edges.append(values[-1])
    return edges


def _sample_indices(count: int, maximum_count: int) -> list[int]:
    if count <= maximum_count:
        return list(range(count))
    return sorted({round(index * (count - 1) / (maximum_count - 1)) for index in range(maximum_count)})


def _temperature_color(value: float, minimum: float, maximum: float) -> QColor:
    ratio = (value - minimum) / _nonzero_span(minimum, maximum)
    ratio = max(0.0, min(1.0, ratio))
    stops = (
        (0.0, QColor("#24499a")),
        (0.35, QColor("#2fb7c7")),
        (0.65, QColor("#f4d35e")),
        (1.0, QColor("#c43c2e")),
    )
    for (left_ratio, left_color), (right_ratio, right_color) in zip(stops, stops[1:]):
        if left_ratio <= ratio <= right_ratio:
            local_ratio = (ratio - left_ratio) / (right_ratio - left_ratio)
            return _interpolate_color(left_color, right_color, local_ratio)
    return stops[-1][1]


def _interpolate_color(left: QColor, right: QColor, ratio: float) -> QColor:
    return QColor(
        round(left.red() + (right.red() - left.red()) * ratio),
        round(left.green() + (right.green() - left.green()) * ratio),
        round(left.blue() + (right.blue() - left.blue()) * ratio),
    )
