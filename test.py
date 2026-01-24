import requests
import json
from datetime import datetime, timedelta
import csv
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,zh-HK;q=0.7,en-US;q=0.6,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Connection": "keep-alive",
    "Referer": "https://index.baidu.com/v2/main/index.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0"
}
cookies = {
    "BAIDUID": "75C69745C45E20E010C19DE6204FE1A8:FG=1",
    "BIDUPSID": "75C69745C45E20E062BC2E9C900FB8C9",
    "PSTM": "1768561396",
    "H_PS_PSSID": "63144_65590_66682_66687_66853_66992_67046_67089_67113_67128_67150_66947_67154_67163_67220_67228_67238_67232_67234_67235_67242_67252_67296_67319_67316_67314_67322_67321_67303",
    "ZFY": "3nzMVI:AlONI0RpjdfiR3kd9Avk1qXhN2arhlD92TRIY:C",
    "H_WISE_SIDS": "63145_66581_66675_66677_66851_67050_67088_67110_67130_67149_67152_67158_67182_67204_67230_67262_67232_67233_67243_67268_67284_67252_67292_67319_67317_67314_67323_67320_67302",
    "RT": "\"z=1&dm=baidu.com&si=8bc43375-2c35-4a02-8942-75e86ad98437&ss=mkru3ghf&sl=p&tt=smv&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=1gfuw\"",
    "Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc": "1768799962,1769230396",
    "Hm_up_d101ea4d2a5c67dab98251f0b5de24dc": "%7B%22uid_%22%3A%7B%22value%22%3A%226561208554%22%2C%22scope%22%3A1%7D%7D",
    "BDUSS": "hHYjhvRHlNeXMxd2hnYllYSFBnWTlyTU54NEgzcXlreTZ2QkliQS12RTdUSlZwSUFBQUFBJCQAAAAAAQAAAAEAAADqGBSHQXVyb3JhbDY4NjgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADu~bWk7v21pYW",
    "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1769232768",
    "HMACCOUNT": "03E4B5A62E1C523C",
    "__cas__st__212": "2a2ae794b26c39391cccf15ef04817f582992d3b9f27d0a15c86ac4829bd72b32e1ff48871e9f0cb7e1eceab",
    "__cas__id__212": "69554690",
    "__cas__rn__": "519242844",
    "SIGNIN_UC": "70a2711cf1d3d9b1a82d2f87d633bd8a05192428444m%2FKJPFbLGGd6gx0tDUKjkUgBHtUCg93k5jDzTYy9XiMXwOFW4XAYk035J7aZBm7yGeR1JcnHb7P3XGX5zu5MOV5pFRsRXIIesoFTokJoKhDNBJUfB10mXHqHVrXtMh4fc6vwXZPTWyNr6%2FPW09OcRUFhN2cbr9wh2%2BlyxaFz8u9v0G355moNqHO75flB5S09A0t93ZsgWTqFEEQM12AqhdgE%2F%2FDdF%2BzCn6LRyCyd9DL0FBvJn%2BIrxFNJaYN50aJBJEbBGNK8UzDPhQvbP6CNoQ%3D%3D92417751690049670593117715501371",
    "CPTK_212": "453883945",
    "CPID_212": "69554690",
    "ab_sr": "1.0.1_NzAwYTQwNDliZGFiZTVkZGNhNTkxMjVjZjIyNjIzZGYyYWNhYmVkMGIxNmYyZjcxNGFjMTM4OGU5OWIyOTNlZjRkN2Y5ODU3MjM3ZDliMGViMDk2ODNiOGQ2NGFjNjk2YjdiYjI2OWIxNDNiMjEyYmY3YTYzNDRkZTFhOTUyZjhhZTFkOWJkYTVjYWFhNWM2Mzg4ZDIzMmQ0YTdiYTRkZg==",
    "bdindexid": "hlqbd60d31kvdesh38tgniqti1"
}


url = "https://index.baidu.com/api/WordGraph/multi"

keywords = [
    "成都旅游", "重庆旅游", "成都景点", "重庆景点", 
    "成都美食", "重庆美食", "成都旅游攻略", "重庆旅游攻略", 
    "成都旅游景点", "重庆旅游景点", "成都旅游必去十大景点推荐", 
    "重庆旅游必去十大景点推荐", "磁器口", "重庆磁器口", "街子古镇"
]

start_date = datetime(2025, 1, 26)
end_date = datetime(2026, 1, 18)

csv_file = 'baidu_index_result.csv'
file_exists = False
try:
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        file_exists = True
except FileNotFoundError:
    pass

with open(csv_file, mode='a', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    if not file_exists:
        writer.writerow(['关键词', '时间范围', '数据类型', 'pv', 'ratio', 'sim', '爬取时间'])

    total_iterations = len(keywords) * ((end_date - start_date).days // 7 + 1)
    current_iter = 0

    for keyword in keywords:
        current_date = start_date
        while current_date <= end_date:
            current_iter += 1
            # Baidu Index usually takes week ending date or specific format. 
            # Based on previous valid request "20251214", let's try sending the date formatted as YYYYMMDD
            date_str = current_date.strftime("%Y%m%d")
            
            print(f"[{current_iter}/{total_iterations}] Processing {keyword} for date {date_str}...")

            params = {
                "wordlist[]": keyword,
                "datelist": date_str
            }
            
            try:
                response = requests.get(url, headers=headers, cookies=cookies, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 0:
                        # print('data', data)
                        # Check if data['data'] is empty (e.g. empty string)
                        if not data['data']:
                            print(f"  -> No data available for date {date_str} (Empty data field)")
                        elif not isinstance(data['data'], dict):
                            print(f"  -> Unexpected data format: {type(data['data'])} - {data['data']}")
                        else:
                            result_data = data['data']
                            period_raw = result_data.get('period', '')
                            
                            # Format period: 20250126|20251214 -> 2025-01-26-2025-12-14
                            if '|' in period_raw:
                                p_start = period_raw.split('|')[0]
                                p_end = period_raw.split('|')[1]
                                formatted_period = f"{p_start[:4]}-{p_start[4:6]}-{p_start[6:]}-{p_end[:4]}-{p_end[4:6]}-{p_end[6:]}"
                            else:
                                formatted_period = period_raw # Fallback

                            # wordlist is a list, and we only requested one keyword so index 0
                            if 'wordlist' in result_data and len(result_data['wordlist']) > 0:
                                word_graph_list = result_data['wordlist'][0].get('wordGraph', [])
                                
                                current_crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                for item in word_graph_list:
                                    writer.writerow([
                                        item['keyword'], # This is the related word, not the search keyword
                                        formatted_period,
                                        '周度数据',
                                        item['pv'],
                                        item['ratio'],
                                        item['sim'],
                                        current_crawl_time
                                    ])
                                print(f"  -> Saved {len(word_graph_list)} related words.")
                            else:
                                print("  -> No wordlist data found.")
                    else:
                        print(f"  -> API Error: {data['message']}")
                else:
                    print(f"  -> Request failed: {response.status_code}")
                
            except Exception as e:
                print(f"  -> Exception: {e}")

            # Advance by one week
            current_date += timedelta(days=7)
            time.sleep(1) # Be polite
