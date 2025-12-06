import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
import re
import datetime
import time
import unicodedata

# ここでファイル名を全て管理、必ず確認する
target_date = "20251205"

# 出力ディレクトリを指定
dir_path = f"out/{target_date}/scr_result/"
# ディレクトリが存在しなければ作成
os.makedirs(dir_path, exist_ok=True)

# 実行時刻を取得
now = datetime.datetime.now()

# ファイル名を「YYYYMMDD_HHMMSS」形式にする
timestamp = now.strftime("%Y%m%d")
file_time = f"{dir_path}/{target_date}"

# 入力csvファイルの読み込み
input_file = f'data/{target_date}_test.csv'  # 読み込むcsvファイル

output_file = f'{file_time}.csv'  # 書き出すcsvファイル

df = pd.read_csv(input_file)
# ニュース記事の取得関数
def scrape_articles(code_number):
    base_url = f"https://www.nikkei.com/nkd/company/disclose/?scode={code_number}"
    articles = []
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # 記事を表形式で取得する部分（実際のHTML構造に基づく）
        table = pd.read_html(base_url, header = 0)  # 表形式のテーブルを取得

        # 企業発情報のURLを最新のものから順に取得
        i = 0
        for row, article in zip(table[0].itertuples(), soup.find_all(href = re.compile('/nkd/disclosure/tdnr'))):

            title = row[2]  # タイトル
            date_str = row[1]  # 配信日時
            # print(date_str)
            link = article.attrs['href']  # 記事のURL
            # print(link)

            date_obj = datetime.datetime.strptime(date_str, '%y/%m/%d  %H:%M')  # 日付をdatetime型に変換
            now_time = datetime.datetime.strptime(target_date, '%Y%m%d')  # 日付をdatetime型に変換
            # print(date_obj)

            # 一か月以内の記事だけ追加
            delta_days = (now_time - date_obj).days # 今の日付からの差分
            print(delta_days)

            if delta_days <= 20:
                articles.append({'title': title, 'date': date_obj, 'url': link})

            i = i + 1
            if(i == 5):
                break

    except Exception as e:
        print(f"Error scraping {base_url}: {e}")    
    return articles

import unicodedata

def zenkaku_to_hankaku(text: str) -> str:
    # 全角文字を半角文字に変換する関数
    return unicodedata.normalize('NFKC', text)


# 各code_numberに対して処理を行う
output_data = []
extra_data = [] # 追加の3件保存用
counter = 0
for index, row in df.iterrows():
    code_number = row['コード'].strip("<>")  # csvのcode_number列
    meigara = zenkaku_to_hankaku(row['銘柄'])
    price = row['終値0日前']
    title = row['変動記事タイトル']
    article_date = row['記事の日付'] # ここは入力のcsvファイルを作成した日時（株価変動ランキングの日付）

    print("銘柄名："+meigara)

    # ニュース記事を取得し、配信日順にソート
    time.sleep(5) # サーバーに負荷がかかりすぎないように待機
    articles = scrape_articles(code_number)
    articles = sorted(articles, key=lambda x: x['date'], reverse=True)

    # target_date以前の最新記事を取得
    latest_article = None
    for article in articles:
        # print(article)
        if article['date'].strftime("%Y-%m-%d") <= article_date:
            latest_article = article
            break

    # 結果を保存
    if latest_article:
        output_data.append({
            'コード': code_number,
            '銘柄': meigara,
            '変動記事本文': None,
            '変動記事タイトル': title,
            '企業発情報タイトル': latest_article['title'],
            'URL': latest_article['url'],
            '記事の日付': latest_article['date'].strftime('%Y/%m/%d'),
            '終値2日前': None,
            '終値1日前': None,
            '終値0日前': price,
            '生成記事': None
        })
    else:
        output_data.append({
            'コード': code_number,
            '銘柄': meigara,
            '変動記事本文': None,
            '変動記事タイトル': None,
            '企業発情報タイトル': None,
            'URL': None,
            '記事の日付': None,
            '終値2日前': None,
            '終値1日前': None,
            '終値0日前': None,
            '生成記事': None
        })

    # 追加で3件を別ファイルに保存
    number = 0
    for art in articles[1:4]:
        extra_data.append({
            'コード': code_number,
            '銘柄': meigara,
            f'企業発情報タイトル{number}': art['title'],
            f'URL{number}': art['url'],
            '記事の日付': art['date'].strftime('%Y/%m/%d')
        })


    # スクレイピング進捗状況の表示
    counter += 1
    print(f'{counter} /1000 is completed.')

# 結果を新しいcsvファイルに書き出し
output_df = pd.DataFrame(output_data)
df_extra = pd.DataFrame(extra_data)

next3_file = f"out/{target_date}/scr_result/{target_date}_extra.csv"

output_df.to_csv(output_file, index=False, encoding="utf-8-sig")
df_extra.to_csv(next3_file, index=False, encoding="utf-8-sig")

print(f"結果を {output_file} に保存しました。")