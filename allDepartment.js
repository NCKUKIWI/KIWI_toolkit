
var request = require("request");
var cheerio = require("cheerio");

console.log("???")
request({
    url: "http://course-query.acad.ncku.edu.tw/qry/",
    method: "GET"
}, function(error,response, body) {
    if(!error ) {
        
        const $ = cheerio.load(body);
        let department = [];
        $('.content #dept_list li .tbody .dept').each(function(i, elem) {
            department.push($(this).text());
        })

        for(let d in department){
            let DpNum = department[d].slice(3,5);
            let data = {
                'DepPrefix':DpNum, 
                'DepName':department[d]
            }
            
            console.log(data)

            /**
             * For inserting into DB department_all
             */
            // db.Insert('department_all', data, function (err, results) {});
        }
    }
});