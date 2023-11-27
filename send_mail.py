# https://gakushikiweblog.com/python-email#toc2

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def sendGMail(
        mail_subject: str = 'NULL subject',
        mail_message: str = 'NULL message'
):
    # SMTPサーバ接続
    smtp_server = 'smtp.gmail.com'
    port = 587
    server = smtplib.SMTP(smtp_server, port)

    # TLS暗号化設定
    server.starttls()

    # SMTPサーバログイン
    login_address = 'techgate01sender@gmail.com'
    login_password = 'ishstpmtmqcihare'
    server.login(login_address, login_password)

    # メッセージ作成・送信
    message = MIMEMultipart()
    message['Subject'] = mail_subject
    message['From'] = 'techgate01sender@gmail.com'
    message['To'] = 'techno510tk@gmail.com'

    text = MIMEText(mail_message)
    message.attach(text)

    server.send_message(message)

    server.quit()


if __name__ == '__main__':
    sendGMail()
