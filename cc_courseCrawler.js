var fs = require('fs');
//var express = require('express');
var request = require('request');
var mysql = require('mysql');

// var app = express();
// app.listen(3000);

//config相關變數
var config = fs.readFileSync("./config.crawler.json", 'utf8');
config = JSON.parse(config);

//宣告config相關變數
var db_config = config.db_js;
var dept_url = config.ncku_cc.dept_url;
var course_url = config.ncku_cc.course_url;
var extra_amout_url = config.ncku_cc.extra_amout_url;

//MySQL連結
conn = mysql.createConnection(db_config);
conn.connect(function (err) {
    if (err) throw err;
    console.log('Connect success!');
})





//測試用本地json檔
var dep_data = fs.readFileSync("./data.json", 'utf8');
dep_data = JSON.parse(dep_data);
//--------執行區--------

// craw_dept();
craw_course();
// craw_extra_amout_amount();


//---------END----------


//request DeptAPI
function craw_dept() {
    //串接API
    let option = {
        url: dept_url,
        method: 'GET',
        json: true,
    };
    request(option, function (error, respond, body) {
        if (!error && respond.statusCode == 200) {
            let value = []
            let keys = Object.keys(body.data);
            keys.forEach(element => {
                let no = body.data[element].dept_no;
                let name = body.data[element].dep_name;
                value.push([no, name]);
            });
            let sql = "INSERT IGNORE INTO cc_department_all (DepPrefix, DepName) VALUES ?";
            conn.query(sql, [value], function (err, result) {
                if (err) throw err;
                console.log("Number of records inserted: " + result.affectedRows);
            });
        } else {
            throw error
        }
    })
}

function craw_course() {
    //串接API
    let option = {
        url: course_url,
        method: 'GET',
        json: true,
    };
    request(option, function (error, respond, body) {
        if (!error && respond.statusCode == 200) {
            var value = [];
            var input = body.data;
            var keys = Object.keys(input);
            keys.forEach(element => {
                let dept_name = input[element].dept_name;
                let dept_code = input[element].dept_code;
                let choosed_code = input[element].dept_code + input[element].serial;
                let course_code = input[element].course_code;
                let class_code = input[element].class_code;
                let attribute_code = input[element].attribute_code;
                let grade = input[element].grade;
                let class_type = input[element].class_type;
                let type = input[element].type;
                let course_name = input[element].course_name;
                let cross_master = "";
                input[element].cross_master.forEach(cross_master_no => {
                    cross_master += cross_master_no + ",";
                });
                cross_master = cross_master.substring(0, cross_master.length - 1);
                let english, expert, moocs; //bool
                input[element].english ? (english = "Y") : (english = "N");
                input[element].expert ? (expert = "是") : (expert = "否");
                input[element].moocs ? (moocs = "是") : (moocs = "否");
                let description = input[element].description;
                let condition = input[element].condition;
                let credit = input[element].credit;
                let subject_type = input[element].subject_type;


                //這邊還要修
                //Error: ER_TRUNCATED_WRONG_VALUE_FOR_FIELD: Incorrect string value: '\xF3\xB9\x98\x95\xE5\xBD...' for column '老師' at row 1398
                let teacher = "";
                input[element].teacher.forEach(teacher_no => {
                    teacher += teacher_no + ","
                });
                teacher = teacher.substring(0, teacher.length - 1);


                let choosed_amount = parseInt(input[element].choosed_amount);
                let extra_amount = parseInt(input[element].extra_amount);
                extra_amount = extra_amount || 0; //若extra_amount是字串("餘額")，praseInt後會變成NaN(Not a Number)，轉為0。詳細查"js NaN to 0"
                let time = "",
                    classroom = "";
                input[element].schedule.forEach(schedule_no => {
                    time += schedule_no.time;
                    classroom = schedule_no.classroom;
                });
                value.push([dept_name, dept_code, choosed_code, course_code, class_code, class_type, grade, type, english, course_name, subject_type, credit, teacher, choosed_amount, extra_amount, time, classroom, description, condition, expert, attribute_code, cross_master, moocs]);
            });
            //更新課程四步驟SQL：1.Truncate清空temp table
            //                  2.將新撈資料放進temp table(暫存到資料庫，讓比對choosed_code運算在SQL主機上)
            //                  3.用temp UPDATE course_new(更新course_new上的舊課程資訊)
            //                  4.將資料INSERT IGNORE INTO course_new(舊課程不動，放入新課程)
            //1.Truncate清空temp table
            var sql_1 = "TRUNCATE TABLE cc_course_new_temp";
            conn.query(sql_1, function (err, result) {
                if (err) throw err;
                console.log("1.Truncate清空temp table，資料行數: " + result.affectedRows);
            });
            //2.將資料INSERT IGNORE INTO course_new
            var sql_2 = "INSERT IGNORE INTO cc_course_new (系所名稱, 系號, 選課序號, 課程碼, 分班碼, 班別, 年級, 類別, 英語授課, 課程名稱, 選必修, 學分, 老師, 已選課人數, 餘額, 時間, 教室, 備註, 限選條件, 業界參與, 屬性碼, 跨領域學分學程, Moocs) VALUES ?";
            conn.query(sql_2, [value], function (err, result) {
                if (err) throw err;
                console.log("2.將資料INSERT IGNORE INTO course_new，資料行數: " + result.affectedRows);
            });
            //3.將新撈資料放進temp table(暫存到資料庫，讓比對choosed_code運算在SQL主機上)
            var sql_3 = "INSERT INTO cc_course_new_temp (系所名稱, 系號, 選課序號, 課程碼, 分班碼, 班別, 年級, 類別, 英語授課, 課程名稱, 選必修, 學分, 老師, 已選課人數, 餘額, 時間, 教室, 備註, 限選條件, 業界參與, 屬性碼, 跨領域學分學程, Moocs) VALUES ?";
            conn.query(sql_3, [value], function (err, result) {
                if (err) throw err;
                console.log("3.將新撈資料放進temp table，資料行數: " + result.affectedRows);
            });
            //4.用temp UPDATE course_new(更新course_new上的舊課程資訊)
            var sql_4 = "UPDATE cc_course_new AS new,cc_course_new_temp AS temp SET ";
            var column_name = ["系所名稱", "系號", "課程碼", "分班碼", "班別", "年級", "類別", "英語授課", "課程名稱", "選必修", "學分", "老師", "已選課人數", "餘額", "時間", "教室", "備註", "限選條件", "業界參與", "屬性碼", "跨領域學分學程", "Moocs"]
            column_name.forEach(element => {
                sql_4 += " new." + element + "=" + "temp." + element + ",";
            });
            sql_4 = sql_4.substring(0, sql_4.length - 1);
            sql_4 += " WHERE new.選課序號=temp.選課序號;";
            conn.query(sql_4, function (err, result) {
                if (err) throw err;
                console.log("4.用temp UPDATE course_new，資料行數: " + result.affectedRows);
            });


        } else {
            throw error
        }
    })
}

function craw_extra_amout_amount() {
    //串接API
    let option = {
        url: extra_amout_url,
        method: 'GET',
        json: true,
    };
    request(option, function (error, respond, body) {
        if (!error && respond.statusCode == 200) {
            var value = [];
            var input = body.data;
            var keys = Object.keys(input);
            keys.forEach(element => {
                let choosed_code = input[element].dept_code + input[element].serial;
                let choosed_amount = parseInt(input[element].choosed_amount);
                let extra_amount = parseInt(input[element].extra_amount);
                extra_amount = extra_amount || 0; //若extra_amount是字串("餘額")，praseInt後會變成NaN(Not a Number)，轉為0。詳細查"js NaN to 0"
                value.push([choosed_code, choosed_amount, extra_amount]);
            });
            //更新餘額三步驟SQL：1.Truncate清空 temp
            //                  2.用 temp UPDATE course_new(用temp更新course_new上的餘額資訊)
            //                  3.將新撈餘額INSERT INTO temp
            //1. Truncate清空temp
            var sql_1 = "TRUNCATE TABLE cc_course_choosedamount_temp";
            conn.query(sql_1, function (err, result) {
                if (err) throw err;
                console.log("1.Truncate清空temp table，資料行數: " + result.affectedRows);
            });
            //1.將新撈餘額INSERT INTO temp
            var sql_2 = "INSERT INTO cc_course_choosedamount_temp (選課序號, 已選課人數, 餘額) VALUES ?";
            conn.query(sql_2, [value], function (err, result) {
                if (err) throw err;
                console.log("2.將新撈餘額INSERT INTO temp，資料行數: " + result.affectedRows);
            });
            //3.用 temp UPDATE course_new(用temp更新course_new上的餘額資訊)
            var sql_3 = "UPDATE cc_course_new AS new,cc_course_choosedamount_temp AS temp SET ";
            var column_name = ["已選課人數", "餘額"]
            column_name.forEach(element => {
                sql_3 += " new." + element + "=" + "temp." + element + ",";
            });
            sql_3 = sql_3.substring(0, sql_3.length - 1);
            sql_3 += " WHERE new.選課序號=temp.選課序號;";
            conn.query(sql_3, function (err, result) {
                if (err) throw err;
                console.log("2.用 temp UPDATE course_new，資料行數: " + result.affectedRows);
            });


        } else {
            throw error
        }
    })
}
