"""示範區圖層：路燈、整平騎樓、涼適點 → output/demo_layers.json

網頁原型（public/index.html）裡的 LAMPS、ARCS、COOLS 就是這支程式的輸出。
路線沿途的路燈盞數、瓦數與騎樓長度，由網頁依這些圖層即時計算
（路線兩側 DEMO_BUFFER_M 公尺內）。
"""
import json
import re
import unicodedata

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from config import (OUT, LAMPS, ARCADES, COOL_PUBLIC, COOL_PRIVATE, COOL_PARTNER,
                    DEMO_BBOX, LAMP_WATT_FILL)

clip = box(*DEMO_BBOX)

# 1. 路燈：TWD97 → WGS84；瓦數缺值記 0，網頁以 LAMP_WATT_FILL 計
lp = pd.read_csv(LAMPS, low_memory=False)
lp["w"] = pd.to_numeric(lp.LightWatt1, errors="coerce")
lg = gpd.GeoDataFrame(lp, geometry=gpd.points_from_xy(lp.X, lp.Y), crs=3826).to_crs(4326)
print(f"路燈全市 {len(lg):,} 盞，資料時間 {lp.UpdDate.min()}")
lg = lg[lg.within(clip)]
lamps = [[round(p.x, 5), round(p.y, 5), int(w) if w == w else 0] for p, w in zip(lg.geometry, lg.w)]
print(f"示範範圍 {len(lamps):,} 盞；瓦數缺值 {int(lg.w.isna().sum())} 盞（以 {LAMP_WATT_FILL} W 計）")

# 2. 騎樓：類型 01（騎樓及人行道）或名稱含「騎樓」的整平區塊；其餘為僅人行道
ag = gpd.read_file(ARCADES)
ag = ag[ag.rname.fillna("").str.contains("騎樓") | (ag.motype == "01")].to_crs(4326)
ag = ag[ag.intersects(clip)]
ag["geometry"] = ag.geometry.intersection(clip).simplify(0.000006)
arcs = []
for geom in ag.geometry:
    for p in ([geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))):
        if p.geom_type == "Polygon" and not p.is_empty:
            arcs.append([[round(x, 5), round(y, 5)] for x, y in p.exterior.coords])
print(f"整平騎樓 {len(ag)} 處")


# 3. 涼適點：三份合併；修正座標中的換行、問號；排除臺北市範圍外的點
def num(v):
    s = re.sub(r"[^0-9.\n]", "", str(v)).split("\n")[0]
    try:
        return float(s)
    except ValueError:
        return None


yn = lambda v: 1 if str(v).strip().upper() in ("Y", "1") else 0
rows = []
a = pd.read_csv(COOL_PUBLIC, encoding="cp950")
for _, r in a.iterrows():
    rows.append(["p", r["名稱"], r["地址"], num(r["經度"]), num(r["緯度"]), r["開放時間"], yn(r["冷氣"]), yn(r["廁所"]),
                 yn(r["座位"]), yn(r["飲水設施（例如：飲水機；直飲台；奉茶點等）"]), yn(r["無障礙座位"]), r["設施地點（戶外或室內）"]])
b = pd.read_csv(COOL_PRIVATE, encoding="cp950")
for _, r in b.iterrows():
    rows.append(["v", r["名稱"], r["地址"], num(r["經度"]), num(r["緯度"]), r["開放時間"], yn(r["冷氣"]), yn(r["廁所"]),
                 yn(r["座位"]), yn(r["飲水設施"]), yn(r["無障礙座位"]), r["設施地點（戶外或室內）"]])
c = pd.read_csv(COOL_PARTNER, encoding="cp950")  # 欄名錯位：datasetid 實為室內／戶外
for _, r in c.iterrows():
    rows.append(["c", r["placename"], r["address"], num(r["longitude"]), num(r["latitude"]), r["openinghours"],
                 int(r["airconditioning"] == 1), int(r["restroom"] == 1), int(r["seats"] == 1),
                 int(r["waterdispenser"] == 1), int(r["isaccessible"] == 1), r["datasetid"]])
C = pd.DataFrame(rows, columns=["t", "n", "addr", "x", "y", "open", "ac", "wc", "seat", "water", "acc", "io"])
ok = C.x.between(121.45, 121.67) & C.y.between(24.95, 25.22)
print(f"涼適點 {len(C)} 處（市府 {len(a)}、民間 {len(b)}、合作 {len(c)}），座標無法使用 {int((~ok).sum())} 處")
C = C[ok & C.x.between(DEMO_BBOX[0], DEMO_BBOX[2]) & C.y.between(DEMO_BBOX[1], DEMO_BBOX[3])]


def label(r):
    n = str(r.n).strip()
    if n in ("全家便利商店", "統一超商"):  # 沒有店名，用地址區分
        ad = unicodedata.normalize("NFKC", str(r.addr)).replace("臺北市", "").replace("大安區", "")
        ad = re.sub(r"^\S*?里(?=\S*[路街])", "", ad).split("號")[0] + "號"
        n = f"{'全家' if n.startswith('全家') else '統一超商'} {ad}"
    return n.replace("大安區行政中心", "大安區行政中心（區公所）")


def hours(v):
    if pd.isna(v):
        return ""
    s = unicodedata.normalize("NFKC", re.sub(r"\s+", " ", str(v)).strip())
    return s.replace("9:0017:00", "9:00-17:00").replace("am9:00~pm15:30", "9:00-15:30").replace(" (例假日及國定假日除外)", "")


cool = [[label(r), r.t, round(r.x, 6), round(r.y, 6), hours(r.open), r.ac, r.wc, r.seat, r.water, r.acc, str(r.io).strip()]
        for r in C.itertuples()]
print(f"示範範圍涼適點 {len(cool)} 處：{C.t.value_counts().to_dict()}")

out = OUT / "demo_layers.json"
out.write_text(json.dumps(dict(lamps=lamps, arcs=arcs, cools=cool), ensure_ascii=False, separators=(",", ":")),
               encoding="utf-8")
print(f"→ {out}")
