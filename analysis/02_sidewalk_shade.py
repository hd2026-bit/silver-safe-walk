"""步驟 2：每段人行道的樹蔭密度（行道樹＋公園樹木）。輸出 sidewalk_shade.geojson、district_summary.csv"""
import pandas as pd, geopandas as gpd, numpy as np
from config import *

sw = gpd.read_file(SIDEWALKS).to_crs(3826)
sw["gid"] = range(len(sw))
sw["區"] = sw["Town_N"].astype(str).map(DISTRICTS)
sw["L"] = pd.to_numeric(sw["SW_LENG_ItemValue"], errors="coerce")
sw = sw[sw.L > 0]

def trees(path, kind):
    t = pd.read_csv(path, dtype=str)
    t["x"], t["y"] = pd.to_numeric(t.TWD97X, errors="coerce"), pd.to_numeric(t.TWD97Y, errors="coerce")
    t = t.dropna(subset=["x", "y"])
    return gpd.GeoDataFrame(t[["TreeID"]].assign(kind=kind), geometry=gpd.points_from_xy(t.x, t.y), crs=3826)

allt = pd.concat([trees(STREET_TREES, "street"), trees(PARK_TREES, "park")])
buf = sw[["gid", "geometry"]].copy()
buf["geometry"] = buf.buffer(SHADE_BUFFER_M)
j = gpd.sjoin(allt, buf, predicate="within")
sw = sw.join(j.groupby("gid").TreeID.nunique().rename("n"), on="gid")
sw["n"] = sw.n.fillna(0)
sw["per100"] = sw.n / sw.L * 100
# 估計樹冠覆蓋長度比：棵數 × 樹冠寬 ÷ 人行道長度（上限 100%）
sw["cover"] = np.minimum(1, sw.n * CROWN_M / sw.L)
sw["cls"] = np.select([sw.n == 0, sw.cover < COVER_TARGET], ["無樹", "未達40%"], "達40%")

t = sw.groupby("cls").L.sum()
print("全市人行道", round(sw.L.sum() / 1000), "km；", (t / t.sum() * 100).round(1).to_dict())
for cw in (5, 8, 10):
    low = np.minimum(1, sw.n * cw / sw.L) < COVER_TARGET
    print(f"  敏感度：樹冠寬 {cw} m → 覆蓋未達 40% 的人行道占 {sw.L[low].sum() / sw.L.sum():.1%}")
d = sw.groupby(["區", "cls"]).L.sum().unstack(fill_value=0)
d = d.div(d.sum(axis=1), axis=0) * 100
d["缺樹蔭%"] = d["無樹"] + d["未達40%"]
el = pd.read_csv(OUT / "li_elders.csv").groupby("區")[["總計", "p65", "p75"]].sum()
el["r65"], el["r75"] = el.p65 / el["總計"] * 100, el.p75 / el["總計"] * 100
m = d[["缺樹蔭%", "達40%"]].join(el[["p65", "r65", "r75"]])
m.round(2).to_csv(OUT / "district_summary.csv", encoding="utf-8-sig")
print(m.round(1).sort_values("r65", ascending=False).to_string())
sw.to_crs(4326)[["ID", "區", "NAME_Road", "PSTART", "PEND", "SW_DIRECT", "L", "n", "per100", "cover", "cls", "geometry"]] \
  .to_file(OUT / "sidewalk_shade.geojson", driver="GeoJSON")
