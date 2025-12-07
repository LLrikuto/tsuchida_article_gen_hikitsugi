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
target_date = "20251204"

# ここでfewshotを指定する
# method_type = "zeroshot"
method_type = "fewshot"

dir_path = f"out/{target_date}/article_gen/"
# ディレクトリが存在しなければ作成
os.makedirs(dir_path, exist_ok=True)

# 入力ファイル名
df = pd.read_csv(f'data/{target_date}.csv')

# ファイル名を「YYYYMMDD_HHMMSS」形式にする
timestamp = now.strftime("%Y%m%d_%H%M%S")
file_time = f"{dir_path}/twostep_{method_type}_{timestamp}"

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

# 生成された記事を保存する
generated_texts = []

for meigara, code, two, one, zero in zip(df['銘柄'], df['コード'], df['終値2日前'], df['終値1日前'], df['終値0日前']):
    info="###入力文\"\"\"\n ・銘柄名："+str(meigara)+"<"+str(code)+">\n"+" ・３日間の株価変動："+str(two)+", "+str(one)+", "+str(zero)+"\n変動理由となる出来事の情報：\n"
    print(f"銘柄名："+str(meigara)+"<"+str(code)+">")

    if (method_type == "zeroshot"):
        # 中間生成
        response1 = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system",
                "content": [
                    {"type": "input_text",
                    "text": f"###命令\"\"\"\nあなたはプロの金融アナリストです。銘柄名："+str(meigara)+"<"+str(code)+">に関するPDFファイルを参照し、株価変動の原因となり得る内容を抜粋して要約してください。\"\"\"\n"
                    }
                    # # 以下はデバッグ用
                    # {"type": "input_text",
                    # "text": "これから与えるPDFの内容にタイトルをつけてください。出力はタイトルのみで構わないです"+ meigara
                    # }
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

        print("中間生成")
        print(response1.output_text+"\n")

        second_prompt = info + response1.output_text

        print("2段階目のプロンプト")
        print(second_prompt+"\n")

        response2 = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system",
                "content": [
                    {"type": "input_text",
                    "text": "###命令\"\"\"\nあなたはプロの記者です。下記の条件と入力される情報を元に、記事を出力してください。\n\"\"\"\n###条件\"\"\"\n・記事は銘柄名、株価の変動を表す用語、簡潔に要約した変動理由からなる\n・箇条書きではなく、文章の形で出力する\n・本文は300文字程度\n・文体は常体\n\"\"\""
                    }
                    ]
                },
                {"role": "user",
                "content": [
                    {"type": "input_text",
                    "text": second_prompt
                    }
                    ]
                },
            ],
            text={"format": {
                "type": "text"
                }
            },
            reasoning={},
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            stream=False,
            store=False
        )

    elif (method_type == "fewshot"):
        # テキストファイルを読み込む
        with open("out/output_prompt.txt", "r", encoding="utf-8") as f:
            content = f.read()

        response1 = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system",
                "content": [
                    {"type": "input_text",
                    "text": "###命令\"\"\"\nあなたはプロの金融アナリストです。銘柄名："+str(meigara)+"<"+str(code)+">に関するPDFファイルを参照し、株価変動の原因となり得る内容を抜粋して要約してください。\"\"\""
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

        print("中間生成")
        print(response1.output_text+"\n")

        second_prompt = info + response1.output_text

        print("2段階目のプロンプト")
        print(second_prompt+"\n")

        response2 = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system",
                "content": [
                    {"type": "input_text",
                    "text": f"###命令\"\"\"\nあなたはプロの記者です。下記の条件と入力される情報を元に、記事を出力してください。\n\"\"\"\n###条件\"\"\"\n・記事は銘柄名、株価の変動を表す用語、簡潔に要約した変動理由からなる\n・箇条書きではなく、文章の形で出力する\n・本文は300文字程度\n・文体は常体\n\"\"\"例示を渡すので参考にしてください\n{content}\n"
                    }
                    ]
                },
                {"role": "user",
                "content": [
                    {"type": "input_text",
                    "text": second_prompt
                    }
                    ]
                },
            ],
            text={"format": {
                "type": "text"
                }
            },
            reasoning={},
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            stream=False,
            store=False
        )

    article_text = response2.output_text
    # 新しい列に追加
    generated_texts.append(article_text)

    print("出力結果")
    print(response2.output_text)
    time.sleep(1)

# DataFrameに新しい列を追加
df['生成記事'] = generated_texts

# 別ファイルに保存
df.to_csv(f"{file_time}.csv", index=False, encoding="utf-8-sig")