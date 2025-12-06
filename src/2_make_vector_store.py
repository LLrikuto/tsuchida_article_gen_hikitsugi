from openai import OpenAI
import os
import pandas as pd
import logging
import sys
import datetime

# 実行時刻を取得
now = datetime.datetime.now()

# ここでファイル名を全て管理
target_date = "20251205"

dir_path = f"out/{target_date}/make_store/"
# ディレクトリが存在しなければ作成
os.makedirs(dir_path, exist_ok=True)

# 入力ファイル名を指定
df = pd.read_csv(f'data/{target_date}.csv')

# ファイル名に注意
timestamp = now.strftime("%Y%m%d_%H%M%S")
file_time = f"{dir_path}/{timestamp}"

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

# 空のストアを作成（１度作ったらもう作る必要はなし）
vector_store = client.vector_stores.create(name=f"企業発情報_{target_date}")

store_id = vector_store.id
print(f"ストア作成完了。store_name：企業発情報_{target_date}、ストアID：",store_id)

# ファイルIDをキーにしてメタデータを保持する辞書
metadata_store = {}

# PDF登録用の関数
def register_pdf(store_id: str, file_path: str, metadata: dict):
    """
    1つのPDFを指定したベクトルストアに登録する関数
    """
    with open(file_path, "rb") as f:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=store_id,
            files=[f],
        )

    # 登録後にストア内のファイル一覧を取得
    files = client.vector_stores.files.list(vector_store_id=store_id)
    file_id = files.data[0].id
    file_obj = files.data[0]  # 最新ファイルのオブジェクト


    # ファイルIDとメタデータを紐付けて保存（自前管理）
    metadata_store[file_id] = metadata

    print("\n=== 登録確認 ===")
    print("ファイルID:", file_id)
    print("ファイル名:", file_path)
    print("ステータス:", file_obj.status) 
    print("メタデータ：", metadata_store)
    print("------")



for meigara, code, two, one, zero in zip(df['銘柄'], df['コード'], df['終値2日前'], df['終値1日前'], df['終値0日前']):
    info="###銘柄の情報\"\"\" ・銘柄："+str(meigara)+"<"+str(code)+">"+" ・３日間の株価変動："+str(two)+", "+str(one)+", "+str(zero)

    file_path = f"data/PDF_data/{target_date}/{meigara}_{code}.pdf"

    metadata = {
        "銘柄名": meigara,
        "銘柄コード": str(code),
    }

    # 銘柄ごとのPDFを登録
    register_pdf(store_id, file_path, metadata)


all_files = client.vector_stores.files.list(vector_store_id=store_id)

output_lines = []
print("\n=== 全ファイル確認 ===")
for f in all_files.data:
    print("ファイルID:", f.id)
    print("ステータス:", f.status)


print("\n=== 最終的なメタデータ確認 ===")
print(metadata_store)