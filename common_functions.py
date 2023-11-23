""" app.py から呼び出される、共通関数を定義する """
import datetime as dt
import sqlite3
import re
import os

from settings import (
    ROOT_PATH,
    LOG_FILE_DIRECTORY_PATH,
    SAWAYAKA_DB_PATH,
    BLOG_DB_PATH
)


def dict_factory(cursor, row):
    """sqlite3の返すテーブル情報の辞書型モデルを定義する"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def trapezoid_area(lower, upper, height):
    '''台形の面積を求める( (下底+上底)*高さ/2 )'''
    return (lower + upper) * height / 2


_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def elapsed_seconds(time1, time2):
    '''`time1`から`time2`の経過秒数を返す'''
    return (
        dt.datetime.strptime(time2, _DATETIME_FORMAT) -
        dt.datetime.strptime(time1, _DATETIME_FORMAT)
    ).total_seconds()


def log(filename, text):
    """ログファイルにテキストを追記する"""
    log_file_path = os.path.join(ROOT_PATH, LOG_FILE_DIRECTORY_PATH, filename)
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(text)


# ここから、webリクエスト処理
def get_articles(article_id=None):
    """ブログ記事の一覧を取得する"""
    db = sqlite3.connect(os.path.join(ROOT_PATH, BLOG_DB_PATH))
    db.row_factory = dict_factory

    # 記事一覧を取得するSQL文を生成
    sql = (
        "SELECT id, title, thumbnail_path, body, "
        "strftime('%Y年%m月%d日 %H:%M', posted_time, 'localtime') AS timestamp "
        "FROM posts "
    )
    if article_id is not None:
        sql += f"WHERE id={article_id} "
    sql += "ORDER BY posted_time DESC;"

    articles_list = db.execute(sql).fetchall()

    # 記事カードにおける冒頭本文のため、HTMLタグを除いて文字数カットしたダイジェスト文を生成
    for article in articles_list:
        article['head'] = re.sub(re.compile('<.*?>'), '', article['body'])
        # TODO: 後々 &エスケープなどを発見した場合、順次手直しを行う

    return articles_list


def get_sawayaka_shops_table():
    """さわやかの店舗一覧を取得する"""
    db = sqlite3.connect(os.path.join(ROOT_PATH, SAWAYAKA_DB_PATH))
    db.row_factory = dict_factory
    shops_table = db.execute(
        "SELECT shop FROM wait_times GROUP BY shop;"
    ).fetchall()
    return shops_table


def get_sawayaka_waiting_data(shop_name, show_datetype, show_datevalue):
    """さわやかの待ち時間データを取得する"""
    db = sqlite3.connect(os.path.join(ROOT_PATH, SAWAYAKA_DB_PATH))
    db.row_factory = dict_factory
    table_data = []
    if show_datetype == 'day':
        # 時間統計
        table_data = db.execute(
            (
                "SELECT "
                "wait_time,DATETIME(checked_time,'localtime') AS checked_time "
                "FROM wait_times "
                f"WHERE shop='{shop_name}' "
                f"AND DATE(checked_time,'localtime')='{show_datevalue}' "
                "ORDER BY checked_time ASC;"
            )
        ).fetchall()
        # Chart.js 折れ線グラフの雛形
        data = {
            'type': 'line',
            'data': {
                'datasets': [{
                    'label': shop_name,
                    'backgroundColor': '#a0a0a0',
                    'borderColor': '#5050ff',
                    'fill': False,
                    'data': []  # 後の処理で代入する
                }]
            },
            'options': {
                'legend': {
                    'display': False
                },
                'maintainAspectRatio': False,
                'scales': {
                    'xAxes': [{
                        'type': 'time',
                        'distribution': 'series',
                        'time': {
                            'unit': 'hour'
                        }
                    }]
                },
                'elements': {
                    'point': {
                        'radius': 3
                    }
                }
            }
        }
        data['data']['datasets'][0]['data'] = [
            {'x': i['checked_time'], 'y': i['wait_time']} for i in table_data
            ]

    elif show_datetype == 'week':
        # 曜日ごとに集計(月1,火2,...,土6,日0)
        chart_dataset = []
        for weekday_id in (1, 2, 3, 4, 5, 6, 0):
            # 店舗における1日の集計データを抽出
            table_data = db.execute(
                (
                    "SELECT "
                    "wait_time,"
                    "DATETIME(checked_time,'localtime') AS checked_time_jst "
                    "FROM wait_times "
                    f"WHERE shop='{shop_name}' "
                    f"AND STRFTIME('%w',checked_time)='{show_datevalue}' "
                    f"AND STRFTIME('%Y-W%W',checked_time)='{weekday_id}' "
                    "ORDER BY checked_time ASC;"
                )
            ).fetchall()
            total_sum = 0.0
            # 1日の待ち時間の折れ線グラフを関数とみなし、台形の面積の累算によって擬似積分する
            for i in range(len(table_data)-1):
                old = table_data[i]
                new = table_data[i+1]
                time_diff = elapsed_seconds(
                    old['checked_time_jst'], new['checked_time_jst']
                    )
                total_sum += trapezoid_area(
                    old['wait_time'], new['wait_time'], time_diff
                    )
            # 最大値と最小値の差を取り、割ることで1日の待ち時間の代表値を算出(積分のみだと、営業時間の差によって不平等になる)
            extreme_data = db.execute(
                (
                    "SELECT "
                    "DATETIME(MAX(checked_time),'localtime') AS _max,"
                    "DATETIME(MIN(checked_time),'localtime') AS _min "
                    "FROM wait_times "
                    f"WHERE shop='{shop_name}' "
                    "AND STRFTIME('%Y-W%W',DATETIME(checked_time,'localtime'))"
                    f"='{show_datevalue}' "
                    "AND STRFTIME('%w',DATETIME(checked_time,'localtime'))"
                    f"='{weekday_id}' "
                    "GROUP BY shop;"
                )
            ).fetchall()
            if len(extreme_data) == 1:
                chart_dataset.append(
                    sum / elapsed_seconds(
                        extreme_data[0]['_min'], extreme_data[0]['_max']
                        )
                    )
            else:
                chart_dataset.append(0)
        # Chart.js 棒グラフの雛形
        data = {
            'type': 'bar',
            'data': {
                'labels': [],  # 後の処理で代入する
                'datasets': [{
                    'backgroundColor': '#5050ff',
                    'borderColor': '#5050ff',
                    'data': [chart_dataset[i] for i in range(7)]
                }]
            },
            'options': {
                'legend': {
                    'display': False
                },
                'maintainAspectRatio': False,
            }
        }
        for i, j in zip(range(1, 8), ('月', '火', '水', '木', '金', '土', '日')):
            date_label = dt.date.fromisocalendar(
                int(show_datevalue[0:4]), int(show_datevalue[6:8]), i
                )
            label = f'{date_label}({j})'
            data['data']['labels'].append(label)

    return data


# メモ

# select checked_time from wait_times group by checked_time;
# where cast(strftime('%M',checked_time) as integer)%5<>0
# データのサンプリング間隔が一致していないと、平均表示は意味をなさない
# 上のSQL文で現れたレコードはその原因になりうる(5分間隔のサンプリング前提)
