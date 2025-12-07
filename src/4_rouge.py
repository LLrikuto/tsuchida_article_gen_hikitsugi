import MeCab
import os
from rouge_score import rouge_scorer
import pandas as pd
import logging
import sys
import datetime
import csv

# 実行時刻を取得
now = datetime.datetime.now()

# ここでファイル名を全て管理
target_date = "20251204"

dir_path = f"out/{target_date}/rouge_score/"
# ディレクトリが存在しなければ作成
os.makedirs(dir_path, exist_ok=True)

# ファイル名に注意
method_type = "baseline_zeroshot"
# method_type = "baseline_fewshot"
# method_type = "twostep_zeroshot"
# method_type = "twostep_fewshot"

# ファイル名に注意
df = pd.read_csv(f'out/{target_date}/article_gen/{method_type}_20251207_170017.csv')

# ファイル名を「YYYYMMDD_HHMMSS」形式にする
timestamp = now.strftime("%Y%m%d_%H%M%S")
file_time = f"{dir_path}/rouge_{method_type}_{timestamp}"

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

class MeCabTokenizer:
    def tokenize(self, text):
        # 分かち書き
        mecab = MeCab.Tagger("-Owakati -r /etc/mecabrc -d /var/lib/mecab/dic/ipadic-utf8")
        return mecab.parse(text).strip().split()
tokenizer = MeCabTokenizer()
scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=False, tokenizer=tokenizer)

def rouge_to_csv(score_dict, csv_path, meigara=None, code=None, date=None):
    """
    ROUGEスコア辞書をCSVに追記する関数
    
    Parameters
    ----------
    score_dict : dict
        scorer.score() の返り値（例: {'rouge1': Score(...), 'rougeL': Score(...)}）
    csv_path : str
        出力するCSVファイルのパス
    meigara : str, optional
        銘柄名
    code : str/int, optional
        銘柄コード
    date : str, optional
        日付
    """
    # 1行分のデータを作成
    row = [
        meigara if meigara else "",
        date if date else "",
        score_dict["rouge1"].precision,
        score_dict["rouge1"].recall,
        score_dict["rouge1"].fmeasure,
        score_dict["rougeL"].precision,
        score_dict["rougeL"].recall,
        score_dict["rougeL"].fmeasure,
    ]

    # 追記モードで書き込み
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    print(f"ROUGEスコアを {csv_path} に追記しました")


# CSVのヘッダー
headers = ["銘柄", "日付","ROUGE-1,pre", "ROUGE-1,re", "ROUGE-1,F","ROUGE-L,pre", "ROUGE-L,re", "ROUGE-L,F"]
csv_path = file_time+".csv"
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(headers)

for meigara, code, date, article, gen_article in zip(df['銘柄'], df['コード'],df['記事の日付'],df['変動記事本文'],df['生成記事']):
    info="###銘柄の情報\"\"\" ・銘柄名："+str(meigara)+"<"+str(code)+">"+str(date)
    print(info)

    # 実際の株価変動記事
    target = article

    # 生成記事
    prediction = gen_article

    score = scorer.score(target, prediction)


    rouge_to_csv(score,csv_path,meigara,code,date)
    print(score)
