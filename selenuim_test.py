# このプログラムは実用しない

# seleniumの問題は、以下を確認
# https://onl.sc/uT1Eymf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
 
CHROMEDRIVER = "/usr/bin/chromedriver"
 
def get_driver(init_flg):
     
    #　ヘッドレスモードでブラウザを起動
    options = Options()
    options.add_argument('--headless')
 
 
    # ブラウザーを起動
    driver = webdriver.Chrome(CHROMEDRIVER, options=options)
     
    return driver
 
if __name__ == '__main__':
     
    url = "https://example.com/"
     
    #　ヘッドレスモードでブラウザを起動
    options = Options()
    options.add_argument('--headless')
 
    # ブラウザーを起動
    driver = webdriver.Chrome(CHROMEDRIVER, options=options)
     
    # urlにアクセス
    driver.get(url)
     
    title = driver.find_element_by_tag_name("h1")
    print(title.text)
     
    # ブラウザ停止
    driver.quit()