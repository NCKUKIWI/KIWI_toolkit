// 此為抓選課心得粉專的爬蟲

// var max_post_id = 675 //改成都放心得的
// var max_post_id = 0;
var max_post_id = 675;
var config;
var fs = require('fs');
var request = require('request');
var mysql = require('mysql');

fs.readFile("./config.crawler.json", 'utf8', function(err, data) {
    if (err) throw err;
    config = JSON.parse(data);
});

var db_config = config.db_js;

// FB連結設定
var url = "https://graph.facebook.com/v2.6/" + config.fb.page_id + "?fields=posts.limit(100)&access_token=" + config.fb.app_id + "|" + config.fb.token;

con = mysql.createConnection(db_config);

// var classification = [];
// classification[0] = "通識";
// classification[1] = "體育";
// classification[2] = "基礎國文";
// classification[3] = "英文";
// classification[4] = "選修";
// classification[5] = "必修";
// classification[6] = "公民與歷史";

// var classifiaction_languge = [];

// con.query("select max(post_id) as max from post", function(err, result) {
//   if (err) {
//       console.log(err);
//   }
// FB(url, max_post_id);
// 	// FB(url, Number(0));	
// });
con.query("SELECT MAX(crawl_id) FROM post;", function(err, result) {
    if (err) {
        console.log(err);
    }
    max_post_id = result[0]['MAX(crawl_id)'];
    console.log('max_post_id = ' + max_post_id);
    FB(url, max_post_id);
});

function FB(url, max) {
    var options = {
        url: url,
        method: 'GET',
        headers: { 'Content-Type': 'application/json; charset=UTF-8' },
        json: true,
    };

    request(options, function(error, response, body) {
        if (!error && response.statusCode == 200) {
            var post, next;

            if (body.hasOwnProperty("posts")) {
                post = body.posts.data;
                if (body.posts.paging.hasOwnProperty("next")) {
                    next = body.posts.paging.next;
                    FB(next, max); // 繼續下一個坨資料
                }
            } else {
                post = body.data;
                if (body.hasOwnProperty("paging")) {
                    next = body.paging.next;
                    FB(next, max); // 繼續下一個坨資料
                } else {
                    console.log("FB task success!!");
                    // process.exit();
                }
            }

            for (var i in post) {
                if (!post[i].hasOwnProperty("message")) continue;
                var context = post[i].message;
                // var date = new Date(post[i].created_time); // post的發佈時間
                var target = context.split(" ", 1);
                target = target[0].split("\n", 1);

                if (target[0].match("#")) {
                    var id = target[0].replace("#", "");
                    id = Number(id); // 把id找出來

                    if (id <= max) continue; // 用來更新資料用的

                    // if(id != 409) continue; // 更新單筆用的

                    // 切割資料

                    var obj = makeObj(id, context);
                    console.log(obj);
                    console.log(obj['課程名稱：']);
                    console.log('=======================');
                    new_insert_style(id, obj);
                    // postInDatabase(id, obj);
                }
            }
        }
    });
}

function makeObj(id, rawObj) {
    var context = rawObj
        .replace(/[\uD83C-\uDBFF\uDC00-\uDFFF]+/g, "")
        .replace(/[\u2610-\u26FF\u200d]+/g, "")
        .replace('請注意：新版本採用【五星等第制】！', "")
        .split("**");

    console.log('id: ' + id);
    // console.log(context[0]);

    var after_split = context[0].split(/(\n[\u4e00-\u9fa5]+\：)/);

    var obj = {};
    for (var i = 1; i < after_split.length; i += 2) {
        obj[after_split[i].replace('\n', "")] = after_split[i + 1].replace(/\#|\n/g, "");
    }
    // console.log(obj);

    // var items = after_split.filter(function(e, i){
    // 	if(i % 2 == 1) return true;
    // 	else return false;
    // });
    // console.log(items);
    // console.log(items.length);
    // for (var i = 1; i < after_split.length; i += 2){
    // 	console.log(after_split[i]);
    // }
    return obj;
}

function new_insert_style(id, obj) {
    var sql = "insert into post(";
    sql += "course_name, teacher, semester, catalog, comment, crawl_id) values(";
    sql += "\'" + obj['課程名稱：'] + "\'" + ", " + "\'" + obj['開課老師：'] + "\'" + ", " + "\'" + obj['修課時間：'] + "\'" + ", " + "\'" + obj['課程類別：'] + "\'";

    delete obj['課程名稱：'];
    delete obj['開課老師：'];
    delete obj['修課時間：'];
    delete obj['課程類別：'];

    sql += ", " + "\'";
    for (var i in obj) {
        sql += i + obj[i] + '\n<br><br>';
    }
    sql += "\'" + ", " + id + ");";

    console.log(sql);

    con.query(sql, function(err, result) {
        console.log("add " + id + " in database");
        if (err) {
            console.log("id: " + id + "\n" + err);
            console.log("sql");
            console.log(sql);
        }
        if (id == 1) {
            console.log('Client will end now!!!');
            process.exit();
        }
    });
}

function deleteBr(obj) {
    obj = obj.split("");

    var brf = obj[0] + obj[1] + obj[2] + obj[3];
    var brl = obj[obj.length - 4] + obj[obj.length - 3] + obj[obj.length - 2] + obj[obj.length - 1];

    if (brf == "<br>") {
        for (var i = 0; i < 4; i++) {
            delete obj[i];
        }

        // console.log(obj);
    }
    if (brl == "<br>") {
        for (var i = obj.length - 1; i >= obj.length - 4; i--) {
            delete obj[i];
        }
    }

    obj = obj.join();
    obj = obj.replace(/\,/g, "");

    return obj;
}

function deleteNCKU(obj) {
    var ncku = obj[0] + obj[1] + obj[2] + obj[3];

    if (ncku.toLowerCase() == "ncku") {

        obj = obj.split("");
        for (var i = 0; i < 4; i++) {
            delete obj[i];
        }
        obj = obj.join();
        obj = obj.replace(/\,/g, "");

        return obj;
    } else return obj;
}

function postInDatabase(id, obj) {
    return; // 暫時
    console.log(id);
    console.log(obj);
    var sql = "insert into post(";
    sql += "course_name, teacher, catalog, semester, score_style, course_style, course_need, exam_style, report_hw, comment) values(";

    obj.reverse();
    for (var j in obj) {
        if (j >= 12 || j == 4 || j == 2) continue;
        sql += "\'" + obj[j] + "\'";
        if (j != 11) sql += ", ";
    }
    sql += ");"

    // con.query(sql, function(err, result) {
    // 	console.log("add " + id + "in database");
    //    if (err) {
    //        console.log("id: " + id + "\n" + err);
    //        console.log("sql");
    //        console.log(sql);
    //    }
    //    if (id == 1) {
    //        console.log('Client will end now!!!');
    //        process.exit();
    //    }
    // });
}

function hashtagInDatabase(context, id) {
    context = context[0].split("#");
    for (i in context) {
        if (i < 2) continue;
        var tag = [];
        var sql = "insert into hashtag(post_id, hashtag) values( ";

        tag[0] = id;
        tag[1] = context[i].replace(/\$|\n/g, "");
        tag[1] = deleteNCKU(tag[1]);
        sql += tag[0] + "," + "\'" + tag[1] + "\'";

        sql += ");"

        con.query(sql, function(err, result) {
            if (err) {
                console.log("id: " + id + "\n" + err);
                console.log("sql");
                console.log(sql);
            }
            if (id == 0 && i == context.length - 1) {
                console.log('Client will end now!!!');
                con.end();
                process.exit();
            }
        });

    }
}