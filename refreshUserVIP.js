var mysql = require('mysql');
var client = require('./config.crawler.json')   //config
var fs = require('fs');

var connection = mysql.createConnection({
    host: client.db.host,
    user: client.db.user,
    password: client.db.pw,
    database: client.db.database,
    port: client.db.port
});
connection.connect();


// ******* Modify here ********

var currentSemester = "110-1";
var preSemester = "109-2";

// ****************************

//建構Promise
function sqlQuery(sql, values) {
    if (typeof (values) == 'undefined')
        return new Promise(function (resolve, reject) {
            connection.query(sql, function (err, results, fields) {
                if (err) reject(err);
                else resolve(results);
            });
        });
    else //用於一次INSERT多筆資料
        return new Promise(function (resolve, reject) {
            connection.query(sql, [values], function (err, results, fields) {
                if (err) reject(err);
                else resolve(results);
            });
        });
}

//TABLE 'messenger_code_old' 是否存在
var isExist = false;

//把TABLE 'messenger_code' 中semester值為NULL的全改成preSemester
var sqlUpdateNullSemester = "UPDATE messenger_code SET semester='" + preSemester + "' WHERE semester IS NULL;";
sqlQuery(sqlUpdateNullSemester)
    .then(function (results) {
        console.log("Update null semester success, ", "Number of records inserted: " + results.affectedRows);
        
        //刪除前學期沒開通小幫手的資料 = 刪掉TABLE 'messenger_code'中is_used=0的row
        var sqlDel = "DELETE FROM messenger_code WHERE semester='" + preSemester + "' AND is_used = 0";
        return sqlQuery(sqlDel);
    })
    .then(function (results) {
        console.log("Success delete, ", "Number of records affected: " + results.affectedRows);

        //檢查TABLE 'messenger_code_old'是否存在
        var sqlExist = "SHOW TABLES LIKE 'messenger_code_old';";
        return sqlQuery(sqlExist);
    })
    .then(function (results) {
        //如果TABLE 'messenger_code_old'存在
        if (results.length) {
            isExist = true;
            console.log("TABLE: messenger_code_old exist");
        }

        //如果TABLE 'messenger_code_old'不存在，就要建表
        if (!isExist) {
            var sqlCreate = "CREATE TABLE messenger_code_old LIKE messenger_code;";
            return sqlQuery(sqlCreate);
        }
    })
    .then(function(results){    //此時results可能是undefined
        if (!isExist) {
            console.log("TABLE: messenger_code_old has been created successfully");
        }

        //把(包括)preSemester以前的資料全部搬到TABLE 'messenger_code_old'
        var sqlMove = "INSERT  INTO messenger_code_old SELECT * FROM messenger_code;";
        return sqlQuery(sqlMove);
    })
    .then(function (results) {
        console.log("Update TABLE: messenger_code_old success, ", "Number of records affected: " + results.affectedRows);

        //搬完了便清空 TABLE 'messenger_code'
        var sqlDelete = "DELETE FROM messenger_code;";
        return sqlQuery(sqlDelete);
    })
    .then(function (results) {
        console.log("Delete TABLE: messenger_code success, ", "Number of records affected: " + results.affectedRows);

        //將Table `user` 中所有id SELECT出來，為了要當TABLE `messenger_code`的user_id
        var sqlSelectNew = "SELECT id FROM user;";
        return sqlQuery(sqlSelectNew);
    })
    .then(function (results) {
        //為要INSERT至TABLE `messenger_code的每筆user資料生成必要的欄位值，即COL ('code','user_id')
        var newData = [];
        for (i in results) {
            //生成`code`(messenger驗證碼)
            var codeRand = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            var code = 'nckuhub' + codeRand.substring(1, 14);

            //撈出來的user_id
            var user_id = JSON.parse(JSON.stringify(results[i]["id"]));

            //把新的1 row放入newData，等等一次 INSERT
            newData.push([code, user_id]);
        }

        //開始在 TABLE 'messenger_code' INSERT新資料，
        //結果就是每一筆資料的 COL ('code','user_id','semester')有新生成的值，其餘COL為預設值
        var sql_insertAll = "INSERT INTO messenger_code (code, user_id) VALUES ?";
        return sqlQuery(sql_insertAll, newData);
    })
    .then(function (results) {
        console.log("Insert new data success, ", "Number of records inserted: " + results.affectedRows);

        //為了觸發updated_at這欄位的自動更新
        var sqlUpdateSemester = "UPDATE messenger_code SET semester='" + currentSemester + "' WHERE semester IS NULL;";
        return sqlQuery(sqlUpdateSemester);
    })
    .then(function (results) {
        console.log("Update all new data success, ", "Number of records updated: " + results.affectedRows);
    })
    .catch(function (err) {
        throw err;
    });