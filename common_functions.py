import datetime as dt
import sqlite3
from pprint import pprint,pformat
import re
import datetime
import send_mail
from settings import *

# dict_factoryの定義 sqlite3の返すテーブル情報の辞書型モデルを定義する
def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

def trapezoid_area(lower,upper,height):
	'''台形の面積を求める( (下底+上底)*高さ/2 )'''
	return (lower+upper)*height/2

def elapsed_seconds(time1,time2):
	'''`time1`から`time2`の経過秒数を返す'''
	FMT='%Y-%m-%d %H:%M:%S'
	return (dt.datetime.strptime(time2,FMT)-dt.datetime.strptime(time1,FMT)).total_seconds()

def log(filepath,text):
	with open(f'/home/outtech105/app/logs/{filepath}','a',encoding='utf-8') as f:
		f.write(text)

# ここから、webリクエスト処理
def get_articles(id=None):
	db=sqlite3.connect(BLOG_DB_PATH)
	db.row_factory=dict_factory
	sql=f"SELECT id,title,thumbnail_path,body,strftime('%Y年%m月%d日 %H:%M',posted_time,'localtime') AS timestamp FROM posts "+ \
		("" if id is None else f"WHERE id={id} ")+ \
		f"ORDER BY posted_time DESC;"
	articles_list=db.execute(sql).fetchall()

	# 記事カードにおける冒頭本文のため、HTMLタグを除いて文字数カットしたダイジェスト文を生成
	for i in range(len(articles_list)):
		articles_list[i]['head']=re.sub(re.compile('<.*?>'), '',articles_list[i]['body'])
		# 後々 &エスケープなどを発見した場合、順次手直しを行う

	return articles_list

def get_sawayaka_shops_table():
	db=sqlite3.connect(SAWAYAKA_DB_PATH)
	db.row_factory=dict_factory
	shops_table=db.execute(
		f"SELECT shop FROM wait_times GROUP BY shop;"
	).fetchall()
	return shops_table

def get_sawayaka_waiting_data(shop_name,show_datetype,show_datevalue):
	db=sqlite3.connect(SAWAYAKA_DB_PATH)
	db.row_factory=dict_factory
	table_data=[]
	if show_datetype=='day':
		# 時間統計
		table_data=db.execute(
			f"""
			SELECT wait_time,DATETIME(checked_time,'localtime') AS checked_time
			FROM wait_times
			WHERE shop='{shop_name}' AND DATE(checked_time,'localtime')='{show_datevalue}'
			ORDER BY checked_time ASC
			;""",
		).fetchall()
		# Chart.js 折れ線グラフの雛形
		data={
			'type':'line',
			'data':{
				'datasets':[{
					'label':shop_name,
					'backgroundColor':'#a0a0a0',
					'borderColor':'#5050ff',
					'fill':False,
					'data':[{'x':i['checked_time'],'y':i['wait_time']} for i in table_data]
				}]
			},
			'options':{
				'legend':{
					'display':False
				},
				'maintainAspectRatio':False,
				'scales':{
					'xAxes':[{
						'type':'time',
						'distribution':'series',
						'time':{
							'unit':'hour'
						}
					}]
				},
				'elements':{
					'point':{
						'radius':3
					}
				}
			}
		}

	elif show_datetype=='week':
		# 曜日ごとに集計(月1,火2,...,土6,日0)
		chart_dataset=[]
		for weekday_id in (1,2,3,4,5,6,0):
			# 店舗における1日の集計データを抽出
			table_data=db.execute(
				f"""
				SELECT wait_time,DATETIME(checked_time,'localtime') AS checked_time_jst
				FROM wait_times
				WHERE shop='{shop_name}'
				AND STRFTIME('%Y-W%W',checked_time_jst)='{show_datevalue}'
				AND STRFTIME('%w',checked_time_jst)='{weekday_id}'
				ORDER BY checked_time ASC
				;"""
			).fetchall()
			sum=0.0
			# 1日の待ち時間の折れ線グラフを関数とみなし、台形の面積の累算によって擬似積分する
			for i in range(len(table_data)-1):
				old=table_data[i]
				new=table_data[i+1]
				sum+=trapezoid_area(old['wait_time'],new['wait_time'],elapsed_seconds(old['checked_time_jst'],new['checked_time_jst']))
			# 最大値と最小値の差を取り、割ることで1日の待ち時間の代表値を算出(積分のみだと、営業時間の差によって不平等になる)
			extreme_data=db.execute(
				f'''
				SELECT DATETIME(MAX(checked_time),'localtime') AS _max, DATETIME(MIN(checked_time),'localtime') AS _min
				FROM wait_times
				WHERE shop = '{shop_name}'
				AND STRFTIME('%Y-W%W', DATETIME(checked_time, 'localtime')) = '{show_datevalue}'
				AND STRFTIME('%w', DATETIME(checked_time, 'localtime')) = '{weekday_id}'
				GROUP BY shop
				;'''
			).fetchall()
			if len(extreme_data)==1:
				chart_dataset.append(sum/elapsed_seconds(extreme_data[0]['_min'],extreme_data[0]['_max']))
			else:
				chart_dataset.append(0)
		# Chart.js 棒グラフの雛形
		data={
			'type':'bar',
			'data':{
				'labels':[
					# 'xxxx-Wxx'形式のため、スライスする
					f'{dt.date.fromisocalendar(int(show_datevalue[0:4]),int(show_datevalue[6:8]),i)}({j})'
					for i,j in zip(range(1,8),('月','火','水','木','金','土','日'))
				],
				'datasets':[{
					'backgroundColor':'#5050ff',
					'borderColor':'#5050ff',
					'data':[chart_dataset[i] for i in range(7)]
				}]
			},
			'options':{
				'legend':{
					'display':False
				},
				'maintainAspectRatio':False,
			}
		}

	db.close()
	return data

'''
メモ

select checked_time from wait_times where cast(strftime('%M',checked_time) as integer)%5<>0 group by checked_time;
データのサンプリング間隔が一致していないと、平均表示は意味をなさない
上のSQL文で現れたレコードはその原因になりうる(5分間隔のサンプリング前提)
'''