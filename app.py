"""Flaskを使ったWebサーバのメインコード"""""
import datetime
import json
from flask import Flask, render_template, request, redirect, url_for, Response

import common_functions as cf

app = Flask(__name__)


@app.route('/home')
def tp_home():
    '''時刻・IPログ記録の後、トップページにリダイレクト'''
    cf.log(
        'access.log',
        f'{datetime.datetime.now()}\t'
        f'{request.environ.get("HTTP_X_REAL_IP",request.remote_addr)}\n'
    )
    return redirect(url_for('render_home'))

# ここからWebサイト表示コード


@app.route('/')
def render_home():
    '''トップページを表示する'''
    return redirect(url_for('render_blogs_list'))


@app.route('/blogs')
def render_blogs_list():
    '''ブログ一覧を表示する'''
    article_list = cf.get_articles()
    return render_template(
        'blog_top.html',
        title='ブログ一覧',
        articles=article_list
    )


@app.route('/blogs/<article_id>')
def article_render(article_id):
    """ブログ記事を表示する"""
    article_data = cf.get_articles(article_id)
    if len(article_data) > 1:
        return Response(status=500)
    return render_template(
        'blog_article.html',
        title=article_data[0]['title'],
        article_data=article_data[0]
    )


@app.route('/tools')
def render_tools_list():
    """ツール一覧を表示する"""
    return Response(
        response=(
            '<script>'
            'alert("申し訳ありません。アクセスしたページは未完成です。");'
            'window.location.href="https://techgate.mydns.jp/";'
            '</script>'
        ),
        status=404
    )


# さわやかに関するもの
@app.route('/tools/sawayaka_waiting')
def render_sawayaka_waiting():
    '''待ち時間をグラフ表示ページ描画'''
    shops_table = cf.get_sawayaka_shops_table()
    return render_template(
        'sawayaka_waiting.html',
        shops=[i['shop'] for i in shops_table],
        title='炭焼きレストランさわやか 待ち時間データベース',
        overview='静岡県の人気ハンバーグレストラン「さわやか」の、過去の待ち時間データを表示しています。',
    )


@app.route('/apis/sawayaka_waiting')
def json_sawayaka_wainting():
    '''さわやかの待ち時間をChart.js対応jsonで返すツール'''
    shop_name = request.args.get('shop_name')
    show_datetype = request.args.get('datetype')
    show_datevalue = request.args.get('datevalue')

    return json.dumps(
        cf.get_sawayaka_waiting_data(shop_name, show_datetype, show_datevalue)
    )


if __name__ == '__main__':
    app.run()
