var mysql = require('mysql');
var client = require('./config.crawler.json')
var fs = require('fs');
var connection = mysql.createConnection({
    host: client.DB.host,
    user: client.DB.user,
    password: client.DB.password,
    database: client.DB.db
});
connection.connect();


// ******* Modify here ********

var currentSemester = "108-2";
var preSemester = "108-1";

// ****************************

function deletePrePemesterNotVIP() {
    //刪除前學期沒開通小幫手的資料
    var sqlDel = "DELETE FROM messenger_code WHERE semester='" + preSemester + "' AND is_used = 0";
    connection.query(sqlDel, function (error, results, fields) {
        if (error) throw error;
        console.log("success delete")
    })
}

function refreshUser() {
    //將Table `user` 中所有user拷貝到`messenger_code`
    var sqlAdd = "INSERT INTO messenger_code (user_id) SELECT id FROM user;";
    connection.query(sqlAdd, function (error, results, fields) {
        if (error) throw error;
        console.log("success insert");
    })
    //將上面拷貝來的資料中`currentSemester`設為，程式開頭Modify here的currentSemester
    var sqlSetSemester = "UPDATE messenger_code SET semester='" + currentSemester + "'WHERE is_used!=1";
    connection.query(sqlSetSemester, function (error, results, fields) {
        if (error) throw error;
        console.log("success current");
    })
    //為每一筆user資料生成並insert `code`(messenger驗證碼)
    var sqlSelectNew ="SELECT * FROM messenger_code WHERE semester='"+currentSemester+"'";
    connection.query(sqlSelectNew, function (error, results, fields) {
        if (error) throw error;
        for(i in results){
            var codeRand = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            var code = 'nckuhub' + codeRand.substring(1, 14);
            var sqlSetCode="UPDATE messenger_code SET code ='"+code+"'WHERE id="+results[i]["id"];
            var j=0;
            connection.query(sqlSetCode, function (error, results, fields) {
                if (error) throw error;
                j++;
                console.log("No."+j+" done!(Please wait untill this stop.)");
            })
        }
    })
};



deletePrePemesterNotVIP();
refreshUser();

