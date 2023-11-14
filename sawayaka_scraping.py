from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import sqlite3
import datetime
import time

from pprint import pprint

import send_mail
 
CHROMEDRIVER = "/usr/bin/chromedriver"
DB_PATH='/home/outtech105/app/databases/sawayaka.db'
LOG_PATH='/home/outtech105/app/logs/sawayaka_scraping.log'
 
def add_data(data):
	db=sqlite3.connect(DB_PATH)
	sql='INSERT INTO wait_times (shop,wait_time) VALUES ( :name , :time )'
	db.executemany(sql,data)
	db.commit()
	db.close()

def main():
	print(f"STARTED\t{datetime.datetime.now()}")
	try:
		url = "https://www.genkotsu-hb.com/shop/"
			
		#　ブラウザ起動オプションを設定
		options = Options()
		options.add_argument('--headless')

		# ブラウザを起動
		driver = webdriver.Chrome(CHROMEDRIVER, options=options)
			
		# urlにアクセス
		driver.get(url)

		# 待ち時間の表示を待機(5秒ではエラー頻発)
		time.sleep(10)


		# 店舗リスト作成
		shop_names = driver.find_elements_by_css_selector(".shop_info .name")
		shop_names_list=[i.text for i in shop_names]
			
		# 待ち時間リスト作成
		shop_times = driver.find_elements_by_css_selector(
			".shop_info .wait_time .time .num"
		)
		shop_times_list=[i.text for i in shop_times]

		# 挿入データリスト作成
		# 待ち時間が'-'の場合、閉店中or受付終了であるから、記録しない
		# それ以外の場合、エラーとみなし、エラーログおよびメール送信
		# 待ち時間が'--'の場合、airwaitシステムが動作していない可能性あり
		insert_data=[]
		for name,_time in zip(shop_names_list,shop_times_list):
			if _time=='-':
				continue
			insert_data.append({'name':name,'time':int(_time)})

		add_data(insert_data)

	except Exception as e:
		print(f"OCCURED\t{type(e)}")
		print(f"BECAUSE\t{e}")
		print(f"ESCAPED\t{datetime.datetime.now()}")

		scraped_data=''
		for name,_time in zip(shop_names_list,shop_times_list):
			scraped_data+=f'<{name}>\t{_time}\n'

		send_mail.sendGMail(
			'サーバーエラー発生!',
			'SawayakaScrapingでエラーが発生しました。\n'
			'すみやかに対処してください。\n\n'
			'エラー内容:\n'
			f'{type(e)}\n'
			f'{e}\n\n'
			'取得データ:\n'
			f'{scraped_data}'
			'\nIndigo-ubuntu01 ~/app\n'
		)
	else:
		print(f"INSERTED\t{datetime.datetime.now()}")
	finally:
		# ブラウザ停止
		driver.quit()

if __name__ == '__main__':
	main()
