import pandas as pd
import numpy as np
import json
from sqlalchemy import create_engine
from tqdm import tqdm
# from pymongo import MongoClient

# Setting up connection with sql server
sql_uid='root'
sql_pwd='test'
sql_server='127.0.0.1'
sql_connection_string = f"mysql+pymysql://{sql_uid}:{sql_pwd}@{sql_server}"
sql_engine = create_engine(sql_connection_string)

"""
# Setting up connection with mongoDB
mongo_uid = 'root'
mongo_pwd = 'example'
mongo_server = '127.0.0.1'
mongo_connection_string = f'mongodb://{mongo_uid}:{mongo_pwd}@{mongo_server}:27017/?authMechanism=DEFAULT'
"""


# ------------------------------ Student definition ------------------------------------

# Create Student Structure
db_student = pd.read_sql(
    """
    SELECT GF.student_id,
        S.name,
        S.birthdate,
        S.nationality,
        S.gender,
        S.country,
        S.city,
        GF.academic_history_id,
        AH.program_id,
        AH.start_date AS ah_start_date,
        AH.end_date AS ah_end_date,
        AH.status AS ah_status,
        CG.name AS cg_name,
        CG.course_id,
        CG.group_id,
        CG.group_number,
        GF.professor_id,
        CG.credits,
        GF.grade,
        GF.approved
    FROM GradesWarehouse.GradesFact GF
    INNER JOIN GradesWarehouse.Student S ON S.student_id  = GF.student_id 
    INNER JOIN GradesWarehouse.AcademicHistory AH ON AH.academic_history_id = GF.academic_history_id 
    INNER JOIN GradesWarehouse.CourseGroup CG ON CG.course_id = GF.course_id AND CG.group_id = GF.group_id;
    """,
    sql_engine
).astype({'ah_start_date': 'str', 'ah_end_date': 'str', 'birthdate': 'str'})

def student_to_json(G):
    # Get student information
    student_info = G.head(1)[['student_id', 'name', 'birthdate', 'nationality', 'gender', 'country', 'city']]\
        .to_dict(orient='records')[0]
    
    # Get Academic History information
    academic_history_G = G.groupby(['academic_history_id'])
    academic_histories = []
    for academic_history_id, AHG in academic_history_G:
        # Academic history info
        ah_info = AHG.head(1)[['program_id', 'ah_start_date', 'ah_end_date', 'ah_status']]\
            .rename(columns={'ah_start_date': 'start_date', 'ah_end_date': 'end_date', 'ah_status': 'status'})
        ah_info = ah_info.to_dict(orient='records')[0]

        # Grades
        grades = AHG[['cg_name', 'course_id', 'group_id', 'group_number', 'professor_id', 'credits', 'grade', 'approved']]\
            .drop_duplicates(subset=['course_id'])\
            .rename(columns={'cg_name': 'course_name'})\
            .to_dict(orient='records')

        academic_histories.append({
            'academic_history_id': academic_history_id,
            **ah_info,
            'grades': grades
        })

    return {
        **student_info,
        'academic_histories': academic_histories
    }

transformed_students = db_student.groupby(['student_id', 'name', 'birthdate', 'nationality', 'gender', 'country', 'city'])\
    .apply(student_to_json).values.tolist()

print("Writing students to JSON")
with open('../data/students.json', 'w', encoding='utf-8') as f:
    f.writelines(map(lambda x: json.dumps(x, ensure_ascii=False) +'\n', transformed_students))


del db_student, transformed_students

# ------------------------------- Course definition ------------------------------------

db_course = pd.read_sql(
    """
    SELECT CG.course_id,
        CG.sia_code,
        CG.name,
        CG.credits,
        CG.hourly_intensity,
        CG.group_id,
        CG.group_number,
        CG.seats,
        CG.hourly_intensity_am,
        CG.hourly_intensity_pm 
    FROM GradesWarehouse.CourseGroup CG;
    """,
    sql_engine
)


course_G = db_course.groupby('course_id')
transformed_courses = []
for course_id, G in course_G:
    course_info = G.head(1)[['sia_code', 'name', 'credits', 'hourly_intensity']].to_dict(orient='records')[0]

    groups = G[['group_id', 'group_number', 'seats', 'hourly_intensity_am', 'hourly_intensity_pm']].to_dict(orient='records')
    transformed_courses.append({
        'course_id': course_id,
        **course_info,
        'groups': groups
    })

print("Writing courses to JSON")
with open('../data/courses.json', 'w', encoding='utf-8') as f:
    f.writelines(map(lambda x: json.dumps(x, ensure_ascii=False) +'\n', transformed_courses))

del db_course, transformed_courses

# ------------------------------ Professor definition ----------------------------------
db_professor = pd.read_sql(
    """
    SELECT P.professor_id,
        P.name,
        P.birthdate,
        P.nationality,
        P.gender,
        P.status,
        P.entrance_date,
        P.retirement_date
    FROM GradesWarehouse.Professor P
    """,
    sql_engine
).astype({'entrance_date': 'str', 'retirement_date': 'str'})

transformed_professors = db_professor.to_dict(orient='records')

print("Writing professors to JSON")
with open('../data/professors.json', 'w', encoding='utf-8') as f:
    f.writelines(map(lambda x: json.dumps(x, ensure_ascii=False) +'\n', transformed_professors))

del db_professor, transformed_professors

# ------------------------------ Program definition ------------------------------------
db_program = pd.read_sql(
    """
    SELECT 
        program_id,
        sia_code,
        name,
        education_level,
        department,
        faculty,
        campus,
        mandatory_disciplinary_credits,
        mandatory_fundamental_credits,
        optional_disciplinary_credits,
        optional_fundamental_credits,
        free_choice_credits
    FROM GradesWarehouse.Program;
    """,
    sql_engine
)

transformed_programs = db_program.to_dict(orient='records')

print("Writing programs to JSON")
with open('../data/programs.json', 'w', encoding='utf-8') as f:
    f.writelines(map(lambda x: json.dumps(x, ensure_ascii=False) +'\n', transformed_programs))

del db_program, transformed_programs


# ------------------------- Alt Grades definition -----------------------------------

db_student = pd.read_sql(
    """
    SELECT GF.student_id,
        S.name,
        S.birthdate,
        S.nationality,
        S.gender,
        S.country,
        S.city,
        GF.academic_history_id,
        AH.program_id,
        AH.start_date AS history_start_date,
        AH.end_date AS history_end_date,
        AH.status AS history_status,
        CG.name AS course_name,
        CG.course_id,
        CG.group_id,
        CG.group_number,
        GF.professor_id,
        CG.credits,
        GF.grade,
        GF.approved
    FROM GradesWarehouse.GradesFact GF
    INNER JOIN GradesWarehouse.Student S ON S.student_id  = GF.student_id 
    INNER JOIN GradesWarehouse.AcademicHistory AH ON AH.academic_history_id = GF.academic_history_id 
    INNER JOIN GradesWarehouse.CourseGroup CG ON CG.course_id = GF.course_id AND CG.group_id = GF.group_id;
    """,
    sql_engine
).astype({'history_start_date': 'str', 'history_end_date': 'str', 'birthdate': 'str'})

db_student.drop_duplicates(subset=['student_id', 'academic_history_id', 'course_id'], inplace=True)

transformed_students = db_student.to_dict(orient='records')

print("Writing ALT GRADES to JSON")
with open('../data/alt_grades.json', 'w', encoding='utf-8') as f:
    f.writelines(map(lambda x: json.dumps(x, ensure_ascii=False) +'\n', transformed_students))

del db_student, transformed_students
