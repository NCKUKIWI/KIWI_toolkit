/**
 * TODO:
 *     1. Get the new access token at the following website [1]
 *          - Authorize all the APIs in `Google Sheets API v4`
 *     2. Modify the `START_ROW` to the row you want to start crawling
 *          - Check the last row had been crawled in [2]
 * 
 * [1] Get the access token:
 *     https://developers.google.com/oauthplayground/
 * [2] Post google sheet:
 *     https://docs.google.com/spreadsheets/d/1QJvhTWVKJlqvuBHcxNVjyCUfoFMn4ll91bOB4H3gjNc/edit#gid=1992180234
 */

// ******* Modify here ********
// LastRow=588          Update at 2019.06.23
var START_ROW = 589; // The row in google sheet where you want to start crawling. 
// ****************************


var mysql = require('mysql');
var { google } = require('googleapis')
var client = require('./config.crawler.json')
var RANGE = `A${START_ROW}:W`
const FOUR_SPACE = "\xa0\xa0\xa0\xa0";
var connection = mysql.createConnection({
    host: client.DB.host,
    user: client.DB.user,
    password: client.DB.password,
    database: client.DB.db
});
connection.connect();

function authorize(callback) {
    const { client_secret, client_id, redirect_uris } = client.installed;
    const oAuth2Client = new google.auth.OAuth2(
        client_id, client_secret, redirect_uris[0]
    );
    oAuth2Client.setCredentials({
        access_token: client.credential.access,
        refresh_token: client.credential.refresh
    }
    );
    callback(oAuth2Client);
}

authorize(function (auth) {
    var sheets = google.sheets('v4');
    sheets.spreadsheets.values.get({
        spreadsheetId: client.google_sheet_id_origin,
        range: RANGE,
        auth: auth
    }, (err, response) => {
        if (err) {
            console.log('The API returned an error: ' + err);
            return;
        }
        totalData = response.data.values;
        for (let row in totalData) {
            var rowData = {}
            for (let col in totalData[row]) {
                totalData[row][col] = totalData[row][col].replace(/\"|\'|\#|\/\*/g, "")
            }
            rowData['course_name'] = totalData[row][2]
            rowData['teacher'] = totalData[row][3]
            rowData['catalog'] = totalData[row][7]
            rowData['semester'] = totalData[row][4]
            rowData['comment'] = ''

            rowData['comment'] += '[上課教材]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][14]

            rowData['comment'] += '\n\n[教學方法]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][15]

            rowData['comment'] += '\n\n[點名方式]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][16]

            rowData['comment'] += '\n\n[考試方式]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][17]

            rowData['comment'] += '\n\n[報告方式]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][18]

            rowData['comment'] += '\n\n[作業方式]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][19]

            rowData['comment'] += '\n\n[心得]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][20]

            rowData['comment'] += '\n\n[付出]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][21]

            rowData['comment'] += '\n\n[收穫]\n\n' + FOUR_SPACE
            rowData['comment'] += totalData[row][22] + "\n"

            rowData['row_gsheet'] = START_ROW
            rowData['crawl_id'] = regCrawlID(totalData[row][0])
            connection.query(makeInsertSQL(rowData), function (err, res, fields) {
                if (err)
                    console.log(err)
            })
            console.log("Insert row: " + rowData['row_gsheet'])
            START_ROW++;
        }
        console.log("... Finish ...")
    });
})

function regCrawlID(id) {
    let reg = new RegExp('[0-9]+');
    if (reg.test(id)) {
        id = reg.exec(id)[0];
    } else {
        id = -1; //“無效”“？？？” in 發佈column
    }
    return id;
}

function makeInsertSQL(data) {
    let name = ''
    let value = ''
    for (let d in data) {
        name += d
        name += ','
        value += '"'
        value += data[d]
        value += '",'
    }
    name = name.substring(0, name.length - 1)
    value = value.substring(0, value.length - 1)
    let sql = `INSERT INTO post (${name}) VALUES (${value})`
    return sql;
}







