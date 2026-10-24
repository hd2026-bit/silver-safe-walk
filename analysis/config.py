"""輸入檔案位置。請把下載的開放資料放進 data/，檔名照下面設定（或修改這裡）。"""
from pathlib import Path
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

POPULATION = DATA / "population_112.csv"          # 臺北市各里人口數按年齡分「112年迄今」（cp950 編碼，含到最新月份）
POP_YEAR = "115"                                  # 使用的年份（民國）
POP_MONTH = "9"                                   # 使用的月份（最新一期）
STREET_TREES = DATA / "TaipeiTree.csv"            # 臺北市行道樹分布圖
PARK_TREES = DATA / "TaipeiParkTree.csv"          # 臺北市公園樹木
SIDEWALKS = DATA / "TP_SIDEWORK.json"             # 臺北市人行道範圍圖（EPSG:3826）
VILLAGES = DATA / "village" / "G97_A_CALIN_P.shp" # 臺北市村里界圖（鄰級，程式會合併成里）
ACCIDENTS = sorted((DATA / "accidents").glob("*.csv"))  # 警政署 A1、A2 交通事故（114 年度＋115 年即時）
POLICE = sorted((DATA / "accidents_tpe").glob("*.csv"))  # 臺北市警察局「臺北市死傷交通事故明細」（112、113 年，data.taipei）
YEARS = ["2025", "2026"]                          # 警政署檔納入的年度
STAT_YEAR = "2025"                                # 全年統計用的年度（最近一個完整年）

DISTRICTS = {"63000010": "松山區", "63000020": "信義區", "63000030": "大安區", "63000040": "中山區",
             "63000050": "中正區", "63000060": "大同區", "63000070": "萬華區", "63000080": "文山區",
             "63000090": "南港區", "63000100": "內湖區", "63000110": "士林區", "63000120": "北投區"}

# 方法參數：每一項都附依據（詳見 README「門檻與依據」）
SHADE_BUFFER_M = 5          # 樹冠半徑上限：香港 30 種都市樹木，多數樹冠寬 99 百分位約 10 m（Hui, Jim & Zhang 2020）
CROWN_M = 8                 # 估計樹冠寬（假設值，敏感度測試 5 / 8 / 10 m）
COVER_TARGET = 0.40         # 樹冠覆蓋需 > 40% 才有明顯降溫（Ziter et al. 2019, PNAS）
HOTSPOT_RADIUS_M = 76       # 路口影響範圍常用 250 ft ≈ 76 m（FHWA／路口安全研究慣例）
HOTSPOT_LEVELS = (3, 5)     # 三年內 3–4 件＝觀察名單、≥5 件＝危險路口（約每年 1.7 件）；FHWA 建議用 3–5 年資料
HOTSPOT_YEARS = ["2023", "2024", "2025"]  # 判定危險路口用的完整年度（不含未滿一年的 2026）
OLD_AGE = 65                # 老人福利法：年滿 65 歲
SUPER_AGED = 0.20           # 聯合國／國發會：65 歲以上 ≥ 20% 為超高齡
MIN_DENSITY = 1500          # 歐盟統計局 Degree of Urbanisation：都市中心 ≥ 1,500 人／km²
MIN_SIDEWALK_M = 500        # 里內人行道至少 500 m 才計算（避免樣本過小，屬操作性設定）
MIN_POP = 1000              # 里人口至少 1,000 人（同上，操作性設定）
PRIORITY_Q = 0.75           # 優先排序：75 歲以上比例全市前 25%（排序用，非標準；依據：臺北市 113 年老人生活狀況調查指出 75 歲以上未上網比例較高）
WALK_M_PER_S = 0.8          # 步行速率：道路交通標誌標線號誌設置規則第 231 條較低速率 0.8 m/s；交通部 115/3 要求高齡熱點採較低速率

# 示範區圖層（06_lamps_arcade_cool.py）
LAMPS = DATA / "臺北市路燈位置分布圖_nchc_revise.csv"   # 臺北市路燈位置分布圖（公園路燈工程管理處，國網中心清理版，2017-07）
ARCADES = DATA / "arcade" / "park10_202610021741.shp"   # 臺北市騎樓及人行道整平範圍（SHP 全套，EPSG:3826）
COOL_PUBLIC = DATA / "cool" / "臺北市涼適點.csv"          # 臺北市涼適點（公有，cp950）
COOL_PRIVATE = DATA / "cool" / "臺北市民間涼適點.csv"      # 臺北市民間涼適點（cp950）
COOL_PARTNER = DATA / "cool" / "臺北市cooclmap合作涼爽點.csv"  # 環境部 Cool Map 合作涼爽點（臺北市，cp950）
DEMO_BBOX = (121.5245, 25.0232, 121.5455, 25.0362)      # 大安區示範範圍（經緯度）
LAMP_WATT_FILL = 70         # 瓦數缺值以示範範圍中位數計（W）
DEMO_BUFFER_M = 25          # 路線兩側幾公尺內的路燈、騎樓算進來（路線為簡化示意）
LIT_CUT_KW_PER_100M = 0.9   # 每百公尺路燈瓩數低於此值算「較暗」：示範路段第 25 百分位，暫定的相對比較，非照度標準
