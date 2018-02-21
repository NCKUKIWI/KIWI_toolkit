// 檢查目前的post是否有對應到course

var mysql = require('mysql');
var fs = require('fs');

var config = fs.readFileSync("./config.crawler.json", 'utf8');
config = JSON.parse(config);
var db_config = config.db_js;
var ctr = 0;
con = mysql.createConnection(db_config);

con.query('select * from post', function(err, posts) {
    if (err) console.log(err);

    for (var i in posts) {
        courseName = posts[i].course_name;
        courseTeacher = posts[i].teacher;
        findCourse(courseName, courseTeacher, posts[i].id, posts[i].semester);
    }
})

function findCourse(courseName, courseTeacher, id, year) {
    var sql = 'select * from course_all where course_all.`課程名稱` =' + "\'" + courseName + "\'" + ' and course_all.`老師` = ' + "\'" + courseTeacher + "\'";
    con.query(sql, function(err, results) {
        if (err) console.log(err);
        if (results.length == 0) {
            findCourse2(courseName, courseTeacher, id, year);
        }
    });
}

function findCourse2(courseName, courseTeacher, id, year) {
    var sql = 'select * from course_new where course_new.`課程名稱` =' + "\'" + courseName + "\'" + ' and course_new.`老師` = ' + "\'" + courseTeacher + "\'";
    con.query(sql, function(err, results) {
        if (err) console.log(err);
        if (results.length == 0) {
            console.log("-----------------");
            console.log(sql);
            console.log('number: ' + ++ctr);
            console.log('postid: ' + id);
            console.log('semester: ' + year);
        }
    });
}

////  可能原因
// 1. 課程名稱、老師寫錯
// 2. 多位老師中間的標點符號跟資料庫不同
// 3. 有些課程只有標示很多老師
// 4. 全形半形（ㄧ）、（二）、（ㄧ）（二）同時有的
// 5. 有些課程沒有新增到：要顯示最後更新課程時間
// 6. 之後要打所有的course_all的空格刪掉，改全變形再議
// 7. 有些在課程名稱打不只一堂課，但是同一個老師上

// // 奇怪的
// select * from course_new where course_new.`課程名稱` ='系統系陳長紐系列課程' and course_new.`老師` = '陳長紐'
// number: 152
// postid: 756
// -----------------

// // 104-2
// select * from course_new where course_new.`課程名稱` ='身分法' and course_new.`老師` = '郭書琴'
// number: 163
// postid: 792
// -----------------
// select * from course_new where course_new.`課程名稱` ='打開植物的奧秘' and course_new.`老師` = '郭瑋君'
// number: 181
// postid: 841
// -----------------
// select * from course_new where course_new.`課程名稱` ='法律與正義' and course_new.`老師` = '王效文'
// number: 99
// postid: 597
// -----------------
// select * from course_new where course_new.`課程名稱` ='現代舞與健康體能(女)' and course_new.`老師` = '許春香'
// number: 97
// postid: 591
// -----------------
// select * from course_new where course_new.`課程名稱` ='服務學習(三)-‎國際禮賓大使' and course_new.`老師` = '王筱雯 '
// number: 95
// postid: 578
// -----------------
// select * from course_new where course_new.`課程名稱` ='基礎學術溝通' and course_new.`老師` = '高郁婷'
// number: 94
// postid: 574
// -----------------
// select * from course_new where course_new.`課程名稱` ='大眾健康' and course_new.`老師` = '呂宗學老師 等'
// number: 93
// postid: 572
// -----------------