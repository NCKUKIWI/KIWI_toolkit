const fs = require('fs');
const mysql  = require('mysql');
const config = JSON.parse(fs.readFileSync('./config.crawler.json'));
const connection = mysql.createConnection({
  	host     : config.db_js.host,
 	user     : config.db_js.user,
 	password : config.db_js.password,
	database : config.db_js.database
});
connection.connect();

// ******* Modify here ********

const currentSemester = "108-1"
const lastSemesterId = "40249"

// ****************************

function insertAllFromNew(cb){
    let allCol = "系所名稱, 系號, 選課序號, 課程碼, 分班碼, 班別, 年級, 類別, 英語授課, 課程名稱, 選必修, 學分, 老師, 餘額, 時間, 教室, 備註, 限選條件, 屬性碼, 跨領域學分學程"
    sql_addcol = `INSERT INTO course_all(${allCol}) SELECT ${allCol} FROM course_new`;
    connection.query(sql_addcol, function (error, results, fields) {
        if (error) throw error;
        console.log("Finish the insert from new to all")
        cb();
    });
}

function updateSemester(){
    sql_addcol = `UPDATE course_all SET semester="${currentSemester}" WHERE id > ${lastSemesterId}`;
    connection.query(sql_addcol, function (error, results, fields) {
        if (error) throw error;
        console.log("Finish updating the new semester")
    });	
}

function deleteCourse(){
    let allCol = "系所名稱, 系號, 選課序號, 課程碼, 分班碼, 班別, 年級, 類別, 英語授課, 課程名稱, 選必修, 學分, 老師, 餘額, 時間, 教室, 備註, 限選條件, 屬性碼, 跨領域學分學程, updateTime"
    sql_addcol = `DELETE FROM course_all WHERE id > ${lastSemesterId}`;
    connection.query( sql_addcol, function (error, results, fields) {
        if (error) throw error;
        console.log("success")
    });	
}

insertAllFromNew(()=>{
    updateSemester();
});
// deleteCourse(lastSemesterId)
