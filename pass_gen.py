import random
import string

# 使用可能な文字のセット（小文字の英字と数字）
valid_characters = string.ascii_lowercase + string.digits + '-_'

# 生成したい文字列の長さ
string_length = 10  # 任意の長さに変更できます

# ランダムな文字列の生成
random_string = ''.join(random.choice(valid_characters) for _ in range(string_length))

print(random_string)
