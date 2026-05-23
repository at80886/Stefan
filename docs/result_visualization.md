# 结果可视化说明

当前结果显示区域由 `SimulationPlotWidget` 统一管理，并通过选项卡切换三类视图。

## 视图组成

- 温度分布图展示最终时刻温度随空间位置变化，包含坐标轴、刻度和图例。
- 相界面-时间图展示相界面位置随时间变化，包含坐标轴、刻度和图例。
- 温度云图以一维计算域色带展示最终温度状态，并用竖线标注相界面位置。

## 数据来源

- 三类视图统一消费 `SimulationResult`。
- 温度分布图使用 `x_coordinates` 和最终一组 `temperatures`。
- 相界面-时间图使用 `times` 和 `positions`。
- 温度云图使用 `x_coordinates`、最终一组 `temperatures`、`times` 和 `positions`。

## 扩展方向

- 后续可继续增加鼠标悬停读数、缩放、图像保存和导出联动。
