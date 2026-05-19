FROM apache/spark:3.5.3

USER root
RUN python3 -m pip install --no-cache-dir pandas==2.0.3 pyarrow==17.0.0 PyYAML==6.0.2 scikit-learn==1.3.2 joblib==1.4.2
ENV PYTHONPATH=/opt/spark/python:/opt/spark/python/lib/py4j-0.10.9.7-src.zip:/workspace
WORKDIR /workspace
USER spark
