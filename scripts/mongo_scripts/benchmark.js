use unal;
var startTime = new Date();
var x = db.grades.aggregate([{$match:{group_id:1298}}])
var endTime = new Date();
var executionTime = endTime - startTime;
print("Query execution time: " + executionTime + "ms");

use unal;
var startTime = new Date();
var x = db.grades.aggregate([{$match:{academic_history_id:113}}])
var endTime = new Date();
var executionTime = endTime - startTime;
print("Query execution time: " + executionTime + "ms");

use unal;
var startTime = new Date();
var x = db.grades.find({"group_id": 1298}
var endTime = new Date();
var executionTime = endTime - startTime;
print("Query execution time: " + executionTime + "ms");

use unal;
var startTime = new Date();
var x = db.grades.find({"academic_history_id":134})
var endTime = new Date();
var executionTime = endTime - startTime;
print("Query execution time: " + executionTime + "ms");