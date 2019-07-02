var mysql = require('mysql');
var connection;
connection = mysql.createConnection({
    host     : client.DB.host,
    user     : client.DB.user,
    password : client.DB.password,
    database : client.DB.db
});

connection.connect(function(err){
    if(err) throw err;
    console.log('connect succes');
})

function insertCopyFromFollow(){
    return new Promise ((resolve, reject)=>{
        var followColumn = "course_id, fb_id, content, time, serial, teacher, created_at"
        var sql = 'INSERT INTO follow_copy ('+followColumn+') SELECT '+followColumn+' FROM follow'
        connection.query(sql, (err, result, fields)=>{
            if (err) console.log(err)
            console.log("success")
            resolve();
        })
    })
}

function deleteFollow(){
    var sql = "DELETE FROM follow"
    connection.query(sql,(err,result,fields)=>{
        if(err) throw err;
        console.log("success")
    })
}

insertCopyFromFollow().then(()=>{
    deleteFollow()
})
