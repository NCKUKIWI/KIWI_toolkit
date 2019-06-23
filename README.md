# Toolkit for NCKU HUB service

### Usage Explanation of Files

* `courseCrawlers.json` - Initial configuration for pm2

* `checkPostByCourse.js` - 確定資料庫中的心得都有對應之課程
* `getPostFromFb.js` - 爬取「成大選課心得分享」粉專之心得
* `courseNewToAll.js` - 將 `course_new` 的課程搬到 `course_all`
    * currentSemester: 目前的學期
    * lastSemeterId: `course_all` 的最後一個 `id` ( 上學期最後一個課程的 `id` )
* `refresh_all.py` - 更新全部課程之餘額，確定有無加開、停開課程
* `update_amount.py` - 更新被追蹤之課程的餘額
* `gsheetCrawler.json` - 爬取選課心得 google sheet 上面的心得
    * START_ROW: 希望從 google sheet 上面的哪個 row 開始爬
