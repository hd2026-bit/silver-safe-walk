"""步驟 4：各里指標與高溫熱點里（長者多 × 缺樹蔭）。輸出 li_metrics.gpkg、heat_hotspot_li.csv"""
import pandas as pd, geopandas as gpd, numpy as np
from config import *

g = gpd.read_file(VILLAGES)
li = g.dissolve(by=["SECT_NAME", "LIE_NAME", "LIE_CODE"], as_index=False)[["SECT_NAME", "LIE_NAME", "LIE_CODE", "geometry"]]
li.columns = ["區", "里", "LIE_CODE", "geometry"]
li["area_km2"] = li.area / 1e6
el = pd.read_csv(OUT / "li_elders.csv")
m = li.merge(el[["區", "里", "總計", "p65", "r65", "p75", "r75"]], on=["區", "里"], how="left")
print("里界", len(li), "對到人口", int(m["總計"].notna().sum()))

sw = gpd.read_file(OUT / "sidewalk_shade.geojson").to_crs(3826)
sw["geometry"] = sw.centroid
j = gpd.sjoin(sw, m[["LIE_CODE", "geometry"]], predicate="within")
j["w"] = j["cover"] * j.L
g = j.groupby("LIE_CODE")[["w", "L"]].sum()
m = m.join((g.w / g.L).rename("cover"), on="LIE_CODE").join(g.L.rename("swL"), on="LIE_CODE")
m["short_pct"] = (1 - m["cover"]) * 100   # 供圖表使用：未被樹冠覆蓋的比例

p = pd.read_pickle(OUT / "ped_accidents.pkl")
p = p[p["發生年度"] == STAT_YEAR]
p = gpd.GeoDataFrame(p[["old"]], geometry=gpd.points_from_xy(p.lon, p.lat), crs=4326).to_crs(3826)
a = gpd.sjoin(p, m[["LIE_CODE", "geometry"]], predicate="within").groupby("LIE_CODE").agg(eld=("old", "sum"))
m = m.join(a, on="LIE_CODE"); m["eld"] = m.eld.fillna(0)

m["dens"] = m["總計"] / m.area_km2
ok = m[(m.swL >= MIN_SIDEWALK_M) & (m["總計"] >= MIN_POP) & (m.dens >= MIN_DENSITY)].copy()
# 熱點里（絕對標準）：超高齡（65+ ≥ 20%）且里內人行道估計樹冠覆蓋 < 40%
ok["hot"] = (ok.r65 >= SUPER_AGED) & (ok.cover < COVER_TARGET)
t75 = ok.r75.quantile(PRIORITY_Q)
ok["priority"] = ok.hot & (ok.r75 >= t75)
ok["heat"] = ok.r75.rank(pct=True) + (1 - ok.cover).rank(pct=True)
H = ok[ok.hot].sort_values("heat", ascending=False)
P = ok[ok.priority].sort_values("r75", ascending=False)
m["cat"] = np.select([m.LIE_CODE.isin(P.LIE_CODE), m.LIE_CODE.isin(H.LIE_CODE), m.LIE_CODE.isin(ok.LIE_CODE)],
                     ["hot", "old", "base"], "na")
m = m.merge(ok[["LIE_CODE", "heat"]], on="LIE_CODE", how="left")
m.to_file(OUT / "li_metrics.gpkg", driver="GPKG")
P.drop(columns="geometry").to_csv(OUT / "heat_hotspot_li.csv", index=False, encoding="utf-8-sig")
H.drop(columns="geometry").to_csv(OUT / "superaged_lowshade_li.csv", index=False, encoding="utf-8-sig")
print(f"都市里（≥{MIN_DENSITY} 人/km²）{len(ok)}；超高齡且樹冠覆蓋 < 40%：{len(H)} 里；"
      f"其中 75 歲以上比例前 25%（≥ {t75:.1%}）的優先里：{len(P)} 里，75 歲以上 {int(P.p75.sum())} 人")
print(P.groupby("區").size().sort_values(ascending=False).to_dict())
r = lambda s: s.eld.sum() / s.p65.sum() * 1000
print(f"每千位長者的長者行人事故：優先里 {r(P):.2f}，其他里 {r(ok[~ok.priority]):.2f}")
