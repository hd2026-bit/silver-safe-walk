"""依序執行全部步驟"""
import runpy
for step in ["01_elders", "02_sidewalk_shade", "03_accidents", "04_li_hotspots", "05_build_evidence", "06_lamps_arcade_cool"]:
    print(f"\n===== {step} =====")
    runpy.run_path(f"{step}.py", run_name="__main__")
