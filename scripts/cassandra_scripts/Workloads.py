import pandas as pd
import numpy as np
from tqdm import tqdm
import time

from sqlalchemy import create_engine
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from sqlalchemy import create_engine


# ------------------- 0. Setting up connections -----------------------

# Setting up cassandra connection
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
cluster = Cluster(['20.228.195.142', '20.124.113.95', '20.51.141.149'], auth_provider=auth_provider)
session = cluster.connect()

# ------------------------- Simple queries -------------------------------
# Simple query by partition (student_id)
replication_factors = [1, 2, 3]
times = []
for replication_factor in replication_factors:
  session.set_keyspace(f'warehouse_{replication_factor}')
  start_time = time.time()
  query = """
    SELECT * FROM grades_fact_student WHERE student_id in (2,6,8,10,15,20,25,30,55);
  """.strip()
  res = session.execute(query)
  end_time = time.time()
  times.append(end_time - start_time)
print("Times simple queries by student (small partition)")
print(query)
print(pd.DataFrame({'replication_factor': replication_factors, 'time': times}))
print("------------------------------")

# Simple query by partition (student_id)
replication_factors = [1, 2, 3]
times = []
for replication_factor in replication_factors:
  session.set_keyspace(f'warehouse_{replication_factor}')
  start_time = time.time()
  query = """
    SELECT * FROM grades_fact_v2 WHERE year in (2021, 2022, 2008, 2010) AND semester=1;
  """
  res = session.execute(query)
  end_time = time.time()
  times.append(end_time - start_time)
print("Times simple queries by student (large partition)")
print(query)
print(pd.DataFrame({'replication_factor': replication_factors, 'time': times}))
print("------------------------------")


# ------------------------------ Aggregations ----------------------------------
replication_factors = [1, 2, 3]
times = []
for replication_factor in replication_factors:
  start_time = time.time()
  session.set_keyspace(f'warehouse_{replication_factor}')
  query = """
    SELECT student_id
      , program_id
      , avg(grades_46_2025972)
      , avg(grades_29_1000048_b)
      , avg(grades_10_1000005_b)
    FROM grades_fact_student GROUP BY student_id, academic_history_id, program_id;
  """
  res = session.execute(query)
  end_time = time.time()
  times.append(end_time - start_time)

print("Times aggregation by student_id, program_id (small partition)")
print(query)
print(pd.DataFrame({'replication_factor': replication_factors, 'time': times}))
print("------------------------------")


replication_factors = [1, 2, 3]
times = []
for replication_factor in replication_factors:
  start_time = time.time()
  session.set_keyspace(f'warehouse_{replication_factor}')
  query = """
    SELECT year
      , semester
      , avg(grades_46_2025972)
      , avg(grades_29_1000048_b)
      , avg(grades_10_1000005_b)
    FROM grades_fact_v2 GROUP BY year, semester;
  """
  res = session.execute(query)
  end_time = time.time()
  times.append(end_time - start_time)

print("Times aggregation by year, semester (large partition)")
print(query)
print(pd.DataFrame({'replication_factor': replication_factors, 'time': times}))
print("------------------------------")
