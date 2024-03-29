# Toolkit for NCKU HUB service

## 檔案說明

* `courseCrawlers.json` - Initial configuration for pm2
* `checkPostByCourse.js` - 確定資料庫中的心得都有對應之課程
* `getPostFromFb.js` - 爬取「成大選課心得分享」粉專之心得
* `courseNewToAll.js` - 將 `course_new` 的課程搬到 `course_all`
  * currentSemester: 目前的學期
  * lastSemeterId: `course_all` 的最後一個 `id` ( 上學期最後一個課程的 `id` )
* `refresh_all.py` - 更新全部課程之餘額，確定有無加開、停開課程
* `update_amount.py` - 更新被追蹤之課程的餘額
* `gsheetCrawler.js` - 爬取選課心得 google sheet 上面的心得
  * START_ROW: 希望從 google sheet 上面的哪個 row 開始爬
* `refreshUserVIP.js` - 刪除前學期messenger_code中未開通小幫手服務的user，並初始化新學期的user_code資料
  * currentSemester:新學期
  * preSemester:前學期
* `cc_courseCrawler.js` - 使用串接成大計中提供的課程API服務

## Todo

### 課程爬蟲

* 解決老師中文姓名超出 utf8 編碼、無法儲存進資料庫的問題
* 引入 orm（see: [peewee](https://github.com/coleifer/peewee)）
* 引入 event loop（see: [asyncio](https://www.itread01.com/article/1530932649.html)、[aiohttp](https://aiohttp.readthedocs.io/en/stable/client_quickstart.html)）
