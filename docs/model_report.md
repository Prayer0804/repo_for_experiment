# 模型训练与评估说明

模型引擎：Spark MLlib。

预测任务：按日期、小时、星期、是否周末、上车区域和历史均值特征预测出租车需求量。

输入表：

- `data/gold/demand_features.parquet`

目标字段：

- `demand`

特征字段：

- `pickup_hour`
- `pickup_weekday`
- `is_weekend`
- `avg_distance`
- `avg_fare`
- `avg_duration_min`
- `pickup_zone`

模型：

- 基线模型：Spark MLlib `LinearRegression`
- 改进模型：Spark MLlib `RandomForestRegressor`

数据划分：

- 训练集：51,574 行
- 测试集：17,322 行

指标：

| 模型 | RMSE | MAE | R2 |
| --- | ---: | ---: | ---: |
| 线性回归基线 | 44.4817 | 27.0715 | 0.5822 |
| 随机森林回归 | 41.5874 | 24.7834 | 0.6348 |

模型产物：

- `outputs/metrics/model_metrics.json`
- `outputs/metrics/demand_predictions.csv`
- `outputs/metrics/spark_models/linear_regression_baseline`
- `outputs/metrics/spark_models/random_forest_regressor`
## 前端展示

模型评估指标和需求预测明细已经导出到 `frontend/public/data/offline_dashboard_data.json`，并由 `frontend/public/offline.html` 展示：

- 线性回归基线与随机森林模型 RMSE、MAE、R2 对比。
- 随机森林预测值 vs 实际小时区域需求对比。
- 预测明细表，包括日期、小时、区域、实际需求、预测需求。
