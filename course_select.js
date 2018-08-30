/**
 * Get access token:
 *     https://developers.google.com/oauthplayground/
 */

var mysql  = require('mysql');
var {google} = require('googleapis')
//var client = require('./client_config.json')
var client = require('./config.crawler.json')

var fs = require('fs');
var client = fs.readFileSync("./config.crawler.json", 'utf8');
client = JSON.parse(client);



var sql_array = [];
var RANGE = 'A2:W' 
var col;

var connection = mysql.createConnection({
  	host     : client.DB.host,
 	user     : client.DB.user,
 	password : client.DB.password,
	database : client.DB.db
});
connection.connect();


function authorize(callback) {
    const {client_secret, client_id, redirect_uris} = client.installed;
    const oAuth2Client = new google.auth.OAuth2(
        client_id, client_secret, redirect_uris[0]
    );
    oAuth2Client.setCredentials({
        access_token: client.credential.access,
        refresh_token: client.credential.refresh}
    );
    callback(oAuth2Client); 
}

authorize( function(auth) {  
    var sheets = google.sheets('v4');
    sheets.spreadsheets.values.get({
      	spreadsheetId: client.google_sheet_id_origin,
      	range: RANGE,
      	auth:auth 
    }, (err, response) => {
    if (err) {
        console.log('The API returned an error: ' + err);
        return;
    } 
    col = response.data.values;
    let tmp_sql_insert = '';
    for(let r in col){
        let ctr = 0;
        for(let cell in col[r]){
            let x = col[r][cell].replace(/[\uD83C-\uDBFF\uDC00-\uDFFF]+/g, "")
            .replace(/[\u2610-\u26FF\u200d]+/g, "")
            .replace(/'/g,"");
            tmp_sql_insert = tmp_sql_insert+',\''+x+'\'';
            ctr++;
        }
        if(ctr==23){
            let sql_insert = tmp_sql_insert.substring(1,tmp_sql_insert.length);
            sql_array.push(sql_insert); 
        }
        tmp_sql_insert = "";
    }
    //console.log(sql_array[0]);
    
    
    /**
     *    For inserting into DB.
     */
    let end = sql_array.length+1;
    
    
    for(let i=1;i<end;i++){
        sql_addcol = `INSERT INTO course_select VALUES ('${i}',`+sql_array[i-1]+")";
        connection.query( sql_addcol, function (error, rows, fields) {
            if (error) throw error;
            console.log('The solution is: ', rows);
        });	
    }
    });
  })



  









