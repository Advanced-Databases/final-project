import pandas as pd
import numpy as np
from tqdm import tqdm
import time

from sqlalchemy import create_engine
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from sqlalchemy import create_engine

# Params
__TRUNCATE_IF_EXISTS = True
replication_factor = 3
# ------------------- 0. Setting up connections -----------------------

# Setting up cassandra connection
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
cluster = Cluster(['20.228.195.142', '20.124.113.95', '20.51.141.149'], auth_provider=auth_provider)
session = cluster.connect()

# Keyspace creation settings
session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS warehouse_{replication_factor}
    WITH REPLICATION = {{
    'class': 'SimpleStrategy',
    'replication_factor': {replication_factor}
    }};
""")
session.set_keyspace(f'warehouse_{replication_factor}')


# Setting up connection with sql server
sql_uid='root'
sql_pwd='test'
sql_server='127.0.0.1'
sql_connection_string = f"mysql+pymysql://{sql_uid}:{sql_pwd}@{sql_server}"
sql_engine = create_engine(sql_connection_string)

# --------------------1. ETL Transformation -------------------------------
# 1.1. Fact Grades
# Loading courses
course_ids = pd.read_sql(
    """
    SELECT DISTINCT CG.course_id, CG.sia_code
    FROM GradesWarehouse.CourseGroup CG 
    """,
    sql_engine
).values
course_cf = "\n".join([f", grades_{c[0]}_{c[1]} float" for c in course_ids]).replace('-', '_')


# Create table variants
# Program first (partition by program)
cql_query = f"""
    CREATE TABLE IF NOT EXISTS grades_fact_v1 (
        program_id int
        , student_id int
        , academic_history_id int
        , year int
        , semester int
        , group_id int
        {course_cf}
        , PRIMARY KEY (program_id, student_id, academic_history_id, year, semester, group_id)
    );
"""
res = session.execute(cql_query);

# Year first (partition by year)
cql_query = f"""
    CREATE TABLE IF NOT EXISTS grades_fact_v2 (
        program_id int
        , student_id int
        , academic_history_id int
        , year int
        , semester int
        , group_id int
        {course_cf}
        , PRIMARY KEY ((year, semester), program_id, student_id, academic_history_id, group_id)
    );
"""
res = session.execute(cql_query);

# Student first 
cql_query = f"""
    CREATE TABLE IF NOT EXISTS grades_fact_student (
        student_id int
        , academic_history_id int
        , program_id int
        , year int
        , semester int
        , group_id int
        {course_cf}
        , PRIMARY KEY (student_id, academic_history_id, program_id, year, semester)
    );
"""
res = session.execute(cql_query);

# Truncate if exists to reinsert
if __TRUNCATE_IF_EXISTS: # Tho tombstones may be an issue?
    session.execute("TRUNCATE TABLE grades_fact_v1;")
    session.execute("TRUNCATE TABLE grades_fact_v2;")
    session.execute("TRUNCATE TABLE grades_fact_student;")

# ------------------------------- 2. Insert info ---------------------------------
# Query and format data from warehouse
grades_df = pd.read_sql(
    """
    SELECT GF.program_id,
        GF.student_id,
        GF.academic_history_id,
        D.`year`,
        D.semester,
        GF.group_id,
        GF.course_id,
        CG.sia_code,
        GF.grade
    FROM GradesWarehouse.GradesFact GF
    INNER JOIN GradesWarehouse.`Date` D ON GF.grade_date_id = D.date_id 
    INNER JOIN GradesWarehouse.CourseGroup CG ON GF.course_id = CG.course_id AND GF.group_id = CG.group_id 
    """,
    sql_engine
)
grades_df = grades_df.astype({
    'program_id': 'int', 
    'student_id': 'int',
    'academic_history_id': 'int',
    'year': 'int',
    'semester': 'int',
    'group_id': 'int',
    'course_id': 'int',
})
grades_df['new_course_code'] = 'grades_' + grades_df['course_id'].astype(str) + "_" + grades_df['sia_code'].str.replace('-', '_')

pivot_grades_df = grades_df.pivot(
    index=['program_id', 'student_id', 'academic_history_id', 'year', 'semester', 'group_id'],
    columns='new_course_code',
    values='grade'
).reset_index()

# Insert data in table variants
batch_size = 200
queries = []
batch = []
for i, s in tqdm(pivot_grades_df.iterrows(), total=len(pivot_grades_df)):
    s_filtered = s[~s.isna()]
    columns = s_filtered.keys().tolist()
    columns = ", ".join(columns)
    
    values = s_filtered.values.tolist()
    values = [v if i >= 6 else int(v) for i, v in enumerate(values)] # Cast because iterrows does not preserve the datatype
    values = ", ".join([str(v) for v in values])
    batch.append(f"({columns}) VALUES ({values})")

    if len(batch) == batch_size:
        queries.append(batch)
        batch = []

if len(batch) > 0: queries.append(batch)

print("Insertion>>")
start_time = time.time()
for batch in tqdm(queries, total=len(queries)):
    insert_queries = ''
    for table in ['grades_fact_v1', 'grades_fact_v2', 'grades_fact_student']:
        for element in batch:
            insert_queries += f"INSERT INTO {table} {element}\n"
    
    batched_query = f"""
        BEGIN BATCH
        {insert_queries}
        APPLY BATCH;
    """
    session.execute(batched_query)
end_time = time.time()
print("Insert Time:", end_time - start_time)
