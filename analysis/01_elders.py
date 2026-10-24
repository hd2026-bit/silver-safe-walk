"""步驟 1：各里 65、75 歲以上人口比例。輸出 output/li_elders.csv"""
import pandas as pd
from config import *

d = pd.read_csv(POPULATION, encoding="cp950", dtype=str)
d = d[(d["年份"] == POP_YEAR) & (d["月份"] == POP_MONTH) & (d["性別"] == "計")].drop_duplicates(["區域代碼"])
ages = [c for c in d.columns if c.endswith("歲數量")] + ["100歲以上"]
num = d[ages + ["總計"]].apply(lambda s: pd.to_numeric(s.str.replace(",", ""), errors="coerce"))
age = lambda c: 100 if c == "100歲以上" else int(c.replace("歲數量", ""))
d = pd.concat([d[["區域代碼", "區域別"]], num["總計"],
               num[[c for c in ages if age(c) >= 65]].sum(axis=1).rename("p65"),
               num[[c for c in ages if age(c) >= 75]].sum(axis=1).rename("p75")], axis=1)
d["r65"], d["r75"] = d.p65 / d["總計"], d.p75 / d["總計"]
li = d[d["區域代碼"].str.len() == 11].copy()
li["區"] = li["區域代碼"].str[:8].map(DISTRICTS)
li = li.rename(columns={"區域別": "里"})
li[["區域代碼", "區", "里", "總計", "p65", "r65", "p75", "r75"]].to_csv(OUT / "li_elders.csv", index=False, encoding="utf-8-sig")
city = d[d["區域代碼"] == "63000000"].iloc[0]
print(f"全市 65+ {city.r65:.1%}、75+ {city.r75:.1%}；里數 {len(li)}")
