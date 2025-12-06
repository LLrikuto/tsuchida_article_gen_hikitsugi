from openai import OpenAI
import pandas as pd
import os
import logging
import sys
import datetime
import time

# 実行時刻を取得
now = datetime.datetime.now()

# ここでファイル名を全て管理
target_date = "20251205"

dir_path = f"out/{target_date}/article_gen/"
# ディレクトリが存在しなければ作成
os.makedirs(dir_path, exist_ok=True)

# 入力ファイル名
df = pd.read_csv(f'data/{target_date}.csv')

# ファイル名を「YYYYMMDD_HHMMSS」形式にする
timestamp = now.strftime("%Y%m%d_%H%M%S")
file_time = f"{dir_path}/baseline_zeroshot_{timestamp}"

file_name = f"{file_time}.txt"


logging.basicConfig(
    filename=f"{file_time}.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)
logging.info("ファイル登録開始")

logfile = open(file_name, "w", encoding="utf-8")


class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

# 標準出力をターミナル＋ファイルに同時出力するように差し替え
sys.stdout = Tee(sys.__stdout__, logfile)


client = OpenAI(api_key = "")

# # URLからPDFをダウンロードする（大量にやると規約違反になるので非推奨）
# def url_to_pdf(url, name):
#     # リクエストを送信
#     response = requests.get(url)

#     # ステータス確認
#     if response.status_code == 200:
#         # バイナリモードで保存
#         with open(f"downloaded_{name}.pdf", "wb") as f:
#             f.write(response.content)
#         print(f"PDFを保存しました: downloaded_{name}.pdf")
#     else:
#         print("ダウンロード失敗:", response.status_code)

# 新しい列を追加するためのリスト
generated_texts = []


for meigara, code, two, one, zero in zip(df['銘柄'], df['コード'], df['終値2日前'], df['終値1日前'], df['終値0日前']):
    info="###銘柄の情報\"\"\" ・銘柄名："+str(meigara)+"<"+str(code)+">"+" ・３日間の株価変動："+str(two)+", "+str(one)+", "+str(zero)
    print(info)

    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "system",
            "content": [
                {"type": "input_text",
                "text": "###命令\"\"\"\nあなたはプロの記者です。下記の条件と入力される銘柄の情報、株価変動理由を述べたPDFファイルの情報をもとに、記事を出力してください。\n\"\"\"\n###条件\"\"\"\n・記事は銘柄名、株価の変動を表す用語、簡潔に要約した変動理由からなる\n・箇条書きではなく、文章の形で出力する\n・本文は300文字程度\n・文体は常体\n\"\"\""
                }
                # # 以下はデバッグ用
                # {"type": "input_text",
                # "text": "これから与えるPDFの内容にタイトルをつけてください。出力はタイトルのみで構わないです"+ meigara
                # }
                ]
            },
            {"role": "user",
            "content": [
                {"type": "input_text",
                "text": info
                }
                ]
            },
        ],
        text={"format": {
            "type": "text"
            }
        },
        reasoning={},
        tools=[
            {"type": "file_search",
            "vector_store_ids": [""]
            }
        ],
        tool_choice={
            "type": "file_search"
        },
        temperature=1,
        max_output_tokens=2048,
        top_p=1,
        stream=False,
        store=False
    )

    article_text = response.output_text
    # 新しい列に追加
    generated_texts.append(article_text)

    print(response.output_text)
    time.sleep(2)

# DataFrameに新しい列を追加
df['生成記事'] = generated_texts

# 別ファイルに保存
df.to_csv(f"{file_time}.csv", index=False, encoding="utf-8-sig")
