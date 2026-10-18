"""Build a fresh Onshape assembly: enclosure parts (by partId) + real Adafruit board models positioned per the layout.
Part IDs change when the FeatureScript regenerates, so rebuilding is the reliable path: delete the old assembly element, create a new one."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
import generate_onshape as g
BOARD_PS = {"feather": "6877f0117290b2bf75a4a6c1", "adalogger": "942e19b6acd4ea69381d7283", "oled": "b50741c21ad14419b07e3bfd", "gps": "db3de18bc827bab3b55a6698"}
def T(tx, ty, tz, rot90=False):
    m = 1e-3
    return [0, -1, 0, tx*m, 1, 0, 0, ty*m, 0, 0, 1, tz*m, 0, 0, 0, 1] if rot90 else [1, 0, 0, tx*m, 0, 1, 0, ty*m, 0, 0, 1, tz*m, 0, 0, 0, 1]
PLACE = {"feather": T(g.X_STK0, g.Y_STK0, g.STANDOFF), "adalogger": T(g.X_STK0, g.Y_STK0, g.Z_ADA), "oled": T(g.X_STK0, g.Y_STK0, g.Z_OLED),
         "gps": T(g.GPS["x"] + g.GPS["d"], g.GPS["y"], g.Z_GPS_DECK, rot90=True)}
CONFIGS = {"Enclosure v1 (GoPro base)": {"Shell", "Sled", "Universal base (GoPro)"},
           "Enclosure race (bar clamp)": {"Shell", "Sled", "Saddle", "Clamp cap"},
           "Enclosure v2 (analog tray)": {"Shell", "Sled", "Analog tray", "Connector card (2x M12)", "ADS riser frame", "Universal base (GoPro)"}}
# enclosure parts that are emitted away from their assembled position (tray parts sit beside the enclosure in the Part Studio; the base drops by the tray height in v2)
PART_T = {"Enclosure v2 (analog tray)": {"Analog tray": T(-g.TRAY_DX, 0, 0), "Connector card (2x M12)": T(-g.TRAY_DX, 0, 0),
                                         "ADS riser frame": T(-(g.TRAY_DX + g.CARD2_DX), 0, g.Z_ADS1 + g.PCB), "Universal base (GoPro)": T(0, 0, -g.TRAY_H)}}
only = sys.argv[1] if len(sys.argv) > 1 else None   # substring of a config name: rebuild just that assembly, leave the others alone
todo = {k: v for k, v in CONFIGS.items() if not only or only.lower() in k.lower()}
# remove the assemblies being rebuilt (and, when rebuilding everything, the BOM tables)
for e in g.api("GET", f"/documents/d/{g.DID}/w/{g.WID}/elements"):
    if (e["elementType"] == "ASSEMBLY" and e["name"] in todo) or (e["elementType"] == "BILLOFMATERIALS" and not only):
        try: g.api("DELETE", f"/elements/d/{g.DID}/w/{g.WID}/e/{e['id']}"); print("deleted", e["name"])
        except SystemExit: print("already gone:", e["name"])
parts = g.api("GET", f"/parts/d/{g.DID}/w/{g.WID}/e/{g.PS}")
for name, wanted in todo.items():
    ASM = g.api("POST", f"/assemblies/d/{g.DID}/w/{g.WID}", {"name": name})["id"]; print("new assembly", name, ASM)
    base = f"/assemblies/d/{g.DID}/w/{g.WID}/e/{ASM}"
    def instances(): return g.api("GET", base)["rootAssembly"]["instances"]
    def transform(ids, mat):
        for attempt in range(4):
            try: g.api("POST", f"{base}/occurrencetransforms", {"occurrences": [{"path": [i]} for i in ids], "transform": mat, "isRelative": False}); return
            except SystemExit as e: print("  transform retry", attempt); time.sleep(4)
        raise SystemExit("transform failed")
    for p in parts:
        if p["name"] in wanted or (p["name"].startswith("Board envelope") and "v2" not in name):
            before = {i["id"] for i in instances()} if p["name"] in PART_T.get(name, {}) else None
            g.api("POST", f"{base}/instances", {"documentId": g.DID, "elementId": g.PS, "partId": p["partId"], "isWholePartStudio": False}); time.sleep(0.5)
            if before is not None:
                ids = [i["id"] for i in instances() if i["id"] not in before]; transform(ids, PART_T[name][p["name"]]); print(f"  moved {p['name']}")
    print("  enclosure parts inserted:", len(instances()))
    for key, eid in BOARD_PS.items():
        before = {i["id"] for i in instances()}
        g.api("POST", f"{base}/instances", {"documentId": g.DID, "elementId": eid, "isWholePartStudio": True, "includePartTypes": ["PARTS"]}); time.sleep(2)
        ids = [i["id"] for i in instances() if i["id"] not in before]
        transform(ids, PLACE[key]); print(f"  placed {key}: {len(ids)} part instances")
    bb = g.api("GET", f"{base}/boundingboxes"); print("  bbox mm:", {k: round(v*1000, 1) for k, v in bb.items()})
    print("  ASSEMBLY_EID =", ASM)
