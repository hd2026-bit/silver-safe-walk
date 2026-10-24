"""步驟 5：產生網頁「佐證」分頁用的資料。輸出 output/evidence.json"""
import json, pandas as pd, geopandas as gpd
from config import *

m = gpd.read_file(OUT / "li_metrics.gpkg")
m["geometry"] = m.geometry.simplify(30)
x0, y0, x1, y1 = m.total_bounds
W = 460; s = W / (x1 - x0); H = round((y1 - y0) * s)

def path(geom):
    out = ""
    for pg in ([geom] if geom.geom_type == "Polygon" else list(geom.geoms)):
        out += "M" + "L".join(f"{round((x - x0) * s, 1)} {round((y1 - y) * s, 1)}" for x, y in pg.exterior.coords) + "Z"
    return out

nz = lambda v, f: None if pd.isna(v) else f(v)
li = [[r["區"], r["里"], r["cat"], nz(r["r65"], lambda v: round(v * 100, 1)), nz(r["short_pct"], round),
       int(r["eld"]), path(r.geometry)] for _, r in m.iterrows()]
hs = pd.read_csv(OUT / "elder_hotspots.csv")
pts = gpd.GeoDataFrame(hs, geometry=gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(3826)
dots = [[round((g.x - x0) * s, 1), round((y1 - g.y) * s, 1), int(n), a] for g, n, a in zip(pts.geometry, hs.n, hs["路口"])]
dist = pd.read_csv(OUT / "district_summary.csv").sort_values("r65", ascending=False)
dist = [[r["區"], round(r["r65"], 1), round(r["缺樹蔭%"], 1)] for _, r in dist.iterrows()]
top = pd.read_csv(OUT / "heat_hotspot_li.csv").sort_values("r75", ascending=False)
top = [[r["區"], r["里"], round(r["r65"] * 100, 1), round(r["short_pct"]), round(r["r75"] * 100, 1)] for _, r in top.iterrows()]
(OUT / "evidence.json").write_text(json.dumps({"W": W, "H": H, "li": li, "dots": dots, "dist": dist, "top": top},
                                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("evidence.json 完成；網頁中的 const EVI 即為此內容")
