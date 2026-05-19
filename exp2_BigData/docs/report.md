项目概览

  核心技术栈：
  - 数据处理：Spark 3.5.3（Bronze/Silver/Gold 三层数仓架构）
  - 实时流处理：Kafka + Flink SQL（滑动窗口拥堵计算）
  - 机器学习：Spark MLlib（线性回归 + 随机森林）
  - 可视化：ECharts 大屏（离线分析 + 实时流控）
  - 容器化：Docker Compose（Spark、Flink、Kafka、Nginx、FastAPI）
  - 环境：Python + Conda，Windows 平台

  数据规模：
  - 官方数据集：NYC TLC Yellow Taxi 2024年1月数据
  - 原始行数：2,964,624 条
  - 清洗后：2,721,905 条（删除率 8.2%）

  项目架构：
  数据源 → Bronze层(原始落地) → Silver层(清洗+特征) → Gold层(指标表)
                                                      ↓
                                      离线分析 + MLlib预测 + 可视化大屏

  Kafka生产者 → Flink滑动窗口 → 拥堵告警 → FastAPI + WebSocket → 实时大屏

  核心功能模块：

  1. 离线数据处理（Spark）
    - Bronze：统一字段命名
    - Silver：清洗异常值、时间/空间特征工程
    - Gold：6张指标表（小时、日期、热点、OD、支付、预测特征）
  2. 离线分析（6类分析）
    - 时段需求规律、高峰分析、区域热点、距离费用关系、OD路线
  3. 机器学习预测（Spark MLlib）
    - 线性回归基线：RMSE 44.48, R² 0.58
    - 随机森林改进：RMSE 41.59, R² 0.63
  4. 实时流处理（Kafka + Flink）
    - 事件时间 + Watermark
    - 1分钟窗口、10秒滑动步长
    - 拥堵告警计算
  5. 可视化大屏（ECharts）
    - 离线大屏：11类图表（订单趋势、热点、预测对比等）
    - 实时大屏：WebSocket推送 + 3秒轮询

  快速启动：

  只看离线结果（无需Docker）：
  conda env create -f environment.yml
  conda run -n traffic-bigdata python scripts/export_offline_dashboard.py
  conda run -n traffic-bigdata python -m http.server 8088 --directory frontend/public
  # 访问 http://localhost:8088/offline.html

  项目架构：
  数据源 → Bronze层(原始落地) → Silver层(清洗+特征) → Gold层(指标表)
                                                      ↓
                                      离线分析 + MLlib预测 + 可视化大屏

  Kafka生产者 → Flink滑动窗口 → 拥堵告警 → FastAPI + WebSocket → 实时大屏

  核心功能模块：

  1. 离线数据处理（Spark）
    - Bronze：统一字段命名
    - Silver：清洗异常值、时间/空间特征工程
    - Gold：6张指标表（小时、日期、热点、OD、支付、预测特征）
  2. 离线分析（6类分析）
    - 时段需求规律、高峰分析、区域热点、距离费用关系、OD路线
  3. 机器学习预测（Spark MLlib）
    - 线性回归基线：RMSE 44.48, R² 0.58
    - 随机森林改进：RMSE 41.59, R² 0.63
  4. 实时流处理（Kafka + Flink）
    - 事件时间 + Watermark
    - 1分钟窗口、10秒滑动步长
    - 拥堵告警计算
  5. 可视化大屏（ECharts）
    - 离线大屏：11类图表（订单趋势、热点、预测对比等）
    - 实时大屏：WebSocket推送 + 3秒轮询

  快速启动：

  只看离线结果（无需Docker）：
  conda env create -f environment.yml
  conda run -n traffic-bigdata python scripts/export_offline_dashboard.py
  conda run -n traffic-bigdata python -m http.server 8088 --directory frontend/public
  # 访问 http://localhost:8088/offline.html

  演示实时流控（需要Docker Desktop）：
  .\scripts\start_realtime_stack.ps1
  conda run -n traffic-bigdata python scripts/produce_traffic_events.py --events-per-second 60
  # 访问 http://localhost:8080

  项目亮点：
  - ✅ 完整的数据湖仓架构（Bronze/Silver/Gold）
  - ✅ 真实官方数据集（296万+行程记录）
  - ✅ 端到端流水线（数据→分析→预测→可视化）
  - ✅ 实时流处理（Kafka+Flink+WebSocket）
  - ✅ 容器化部署（一键启动全栈）
  - ✅ 完整文档和测试