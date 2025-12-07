from openai import OpenAI
import pandas as pd
import time
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate

client = OpenAI(api_key = "")

# 入力ファイル名
df = pd.read_csv(f'data/fewshot_data.csv')

fewshot_examples = []

def build_one_example(meigara: str, code: int, two: int, one: int, zero: int, idx: int, article: str) -> dict:
    info="###銘柄の情報\"\"\" ・銘柄名："+str(meigara)+"<"+str(code)+">"+" ・３日間の株価変動："+str(two)+", "+str(one)+", "+str(zero)
    """
    ベクトルストアから検索して上位1件を取り出し、
    1つのfew-shot例を返す関数
    """

    query = meigara+"、"+code+"の株価変動の原因と補足情報"
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "user", "content": [{"type": "input_text", "text": query}]}
        ],
        tools=[{"type": "file_search", "vector_store_ids": [""]}],
        tool_choice={"type": "file_search"}
    )

    return {
        "input": info +"\n企業発情報："+response.output_text,
        "output": article+"\n-------------------\n"
    }

i = 1
for meigara, code, two, one, zero, article in zip(df['銘柄'], df['コード'], df['終値2日前'], df['終値1日前'], df['終値0日前'], df['変動記事本文']):
    if(i==6):
        break
    info="###銘柄の情報\"\"\" ・銘柄名："+str(meigara)+"<"+str(code)+">"+" ・３日間の株価変動："+str(two)+", "+str(one)+", "+str(zero)
    print(info)

    time.sleep(5)
    example = build_one_example(meigara, code, two, one, zero, i, article)
    i += 1
    fewshot_examples.append(example)  

    # 以下はデバッグ用
    print(example)

example_prompt = PromptTemplate(
input_variables=["input", "output"],
template="-------------\n入力: {input}\n\n出力: {output}"
)

prompt = FewShotPromptTemplate(
    examples=fewshot_examples,
    example_prompt=example_prompt,
    prefix="以下は株価記事生成のfew-shot例です。",
    suffix="",
    input_variables=["input"]
)

final_prompt = prompt.format(input = "以上が記事生成の例です。") 
print("\nプロンプト完成")
print(final_prompt)

# final_prompt に完成したプロンプト文字列が入っている前提
with open("out/output_prompt.txt", "w", encoding="utf-8") as f:
    f.write(final_prompt)
