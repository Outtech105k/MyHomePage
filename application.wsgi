"""本番環境用のWSGIファイル"""
import sys
sys.path.insert(0, '/var/www/html/app')

# NOTE: WSGIではこのタイミングでapplicationをインポートする必要があるが、pep8に違反する
from app import app	as application # noqa F401
