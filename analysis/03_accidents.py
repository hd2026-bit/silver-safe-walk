"""步驟 3：臺北市行人事故與長者危險路口。輸出 ped_accidents.pkl、elder_hotspots.csv、accident_stats.txt"""
import re, numpy as np, pandas as pd
from config import *

fr = []
for f in ACCIDENTS:
    d = pd.read_csv(f, encoding="utf-8-sig", dtype=str).fillna("")
    d = d[d["發生年度"].isin(YEARS) & d["發生地點"].str.startswith("臺北市")]
    d["cls"] = d["事故類別名稱"].str.extract(r"(A[12])", expand=False).fillna("A1" if "A1" in f.name else "A2")
    fr.append(d)
df = pd.concat(fr, ignore_index=True).drop_duplicates()
df["acc"] = df[["cls", "發生日期", "發生時間", "發生地點", "經度", "緯度"]].agg("|".join, axis=1)

# 行人（排除公車乘客）；一件事故只留一列（取年紀最大的行人）
p = df[df["當事者區分-類別-子類別名稱-車種"] == "行人"].copy()
p["age"] = pd.to_numeric(p["當事者事故發生時年齡"], errors="coerce")
p = p.sort_values("age", ascending=False).drop_duplicates("acc")
p["old"] = p.age >= OLD_AGE
p["lon"], p["lat"] = pd.to_numeric(p["經度"], errors="coerce"), pd.to_numeric(p["緯度"], errors="coerce")
p = p.dropna(subset=["lon", "lat"])

# 加入臺北市警察局 112、113 年明細（車種 H01＝行人；死亡人數 > 0 為 A1）
pf = []
for f in POLICE:
    t = pd.read_csv(f, encoding="utf-8-sig", dtype=str).fillna("")
    t = t[t["車種"] == "H01"].copy()
    t["發生年度"] = (pd.to_numeric(t["發生年度"]) + 1911).astype(str)
    t["發生日期"] = t["發生年度"] + t["發生月"].str.zfill(2) + t["發生日"].str.zfill(2)
    t["發生時間"] = t["發生時-Hours"].str.zfill(2) + t["發生分"].str.zfill(2) + "00"
    t["發生地點"] = "臺北市" + t["肇事地點"]
    t["cls"] = np.where(pd.to_numeric(t["死亡人數"], errors="coerce").fillna(0) > 0, "A1", "A2")
    t["acc"] = t[["cls", "發生日期", "發生時間", "發生地點", "座標-X", "座標-Y"]].agg("|".join, axis=1)
    t["age"] = pd.to_numeric(t["年齡"], errors="coerce")
    t = t.sort_values("age", ascending=False).drop_duplicates("acc")
    t["old"] = t.age >= OLD_AGE
    t["lon"], t["lat"] = pd.to_numeric(t["座標-X"], errors="coerce"), pd.to_numeric(t["座標-Y"], errors="coerce")
    pf.append(t.dropna(subset=["lon", "lat"])[["發生年度", "發生日期", "發生時間", "發生地點", "cls", "acc", "age", "old", "lon", "lat"]])
if pf:
    p = pd.concat([p] + pf, ignore_index=True)
print("各年度行人事故（長者）：", p.groupby("發生年度").agg(全部=("old", "size"), 長者=("old", "sum")).to_dict("index"))

def roads(s):
    out = set()
    for part in s.split("/"):
        part = re.sub(r"^\s*臺北市..區", "", part.strip())
        m = re.match(r"([^\d\s]+?(路|街|大道|巷|弄)(\S*?段)?)", part)
        if m:
            out.add(re.sub(r"[一二三四五六七八九十\d]+段$", "", m.group(1)))
    return out

p["roads"] = p["發生地點"].map(roads)
p.to_pickle(OUT / "ped_accidents.pkl")

# 長者熱點：半徑內、且路名有交集，串成同一群
o = p[p.old & p["發生年度"].isin(HOTSPOT_YEARS)].reset_index(drop=True)
xy = np.c_[(o.lon - 121.5) * 101700, (o.lat - 25) * 111000]
seen, rows = set(), []
for a in range(len(o)):
    if a in seen:
        continue
    comp, k = [a], 0
    seen.add(a)
    while k < len(comp):
        c = comp[k]; k += 1
        for b in np.where(np.hypot(*(xy - xy[c]).T) <= HOTSPOT_RADIUS_M)[0]:
            if b not in seen and (o.roads[b] & o.roads[c]):
                seen.add(b); comp.append(b)
    if len(comp) >= HOTSPOT_LEVELS[0]:
        s = o.loc[comp]
        rd = set.intersection(*s.roads) or set.union(*s.roads)
        rows.append(dict(n=len(comp), 等級="危險路口" if len(comp) >= HOTSPOT_LEVELS[1] else "觀察名單", 區=s["發生地點"].str[3:6].mode()[0], 路口="／".join(sorted(rd)),
                         lon=round(s.lon.mean(), 6), lat=round(s.lat.mean(), 6)))
H = pd.DataFrame(rows).sort_values("n", ascending=False)
H.to_csv(OUT / "elder_hotspots.csv", index=False, encoding="utf-8-sig")  # 只有位置與件數，不含個別事故

# 全年統計（最近一個完整年）
y = p[p["發生年度"] == STAT_YEAR]
hr = pd.to_numeric(y["發生時間"].str.zfill(6).str[:2])
a = df[(df["發生年度"] == STAT_YEAR) & df["號誌-號誌種類名稱"].str.startswith("行車管制")]
drv = a[~a["當事者區分-類別-大類別名稱-車種"].isin(["人", ""])]
red = set(drv[drv["肇因研判子類別名稱-個別"].str.startswith("闖紅燈")].acc)
u = a.drop_duplicates("acc").copy(); u["red"] = u.acc.isin(red)
uh = pd.to_numeric(u["發生時間"].str.zfill(6).str[:2])
cause = df[df.acc.isin(y[y.old].acc)].drop_duplicates("acc")["肇因研判子類別名稱-主要"].value_counts(normalize=True)
lines = [
    f"{STAT_YEAR} 行人事故 {len(y)} 件，長者 {int(y.old.sum())} 件（{y.old.mean():.1%}）",
    f"{STAT_YEAR} 行人死亡事故（A1）{int((y.cls == 'A1').sum())} 件，長者 {int(((y.cls == 'A1') & y.old).sum())} 件",
    f"{HOTSPOT_YEARS[0]}–{HOTSPOT_YEARS[-1]} 三年：行人事故 {int(p.發生年度.isin(HOTSPOT_YEARS).sum())} 件，長者 {int((p.old & p.發生年度.isin(HOTSPOT_YEARS)).sum())} 件（{p[p.發生年度.isin(HOTSPOT_YEARS)].old.mean():.1%}）；行人死亡 {int(((p.cls == 'A1') & p.發生年度.isin(HOTSPOT_YEARS)).sum())} 件，長者 {int(((p.cls == 'A1') & p.old & p.發生年度.isin(HOTSPOT_YEARS)).sum())} 件",
    f"白天 9–15 點占比：長者 {(hr[y.old].between(9, 15)).mean():.1%}、其他年齡 {(hr[~y.old].between(9, 15)).mean():.1%}",
    f"長者事故單一小時最多：{hr[y.old].value_counts().idxmax()} 點",
    f"長者事故最大肇因：{cause.index[0]}（{cause.iloc[0]:.1%}）",
    f"號誌路口闖紅燈比例：4–6 點 {u[uh.between(4, 6)].red.mean():.1%}，10–15 點 {u[uh.between(10, 15)].red.mean():.1%}",
    f"長者事故路口（{HOTSPOT_YEARS[0]}–{HOTSPOT_YEARS[-1]}，{HOTSPOT_RADIUS_M} 公尺內、路名一致）：危險路口 ≥{HOTSPOT_LEVELS[1]} 件 {int((H.n >= HOTSPOT_LEVELS[1]).sum())} 處；觀察名單 {HOTSPOT_LEVELS[0]}–{HOTSPOT_LEVELS[1]-1} 件 {int(((H.n >= HOTSPOT_LEVELS[0]) & (H.n < HOTSPOT_LEVELS[1])).sum())} 處",
]
(OUT / "accident_stats.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
