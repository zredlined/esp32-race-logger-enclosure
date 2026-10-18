"""Rebuild the race-display assembly: mount parts by partId + the Waveshare STEP model placed on the bosses.
Part IDs change when the FeatureScript regenerates, so delete and recreate the assembly each run."""
import sys, time
sys.path.insert(0, __import__("os").path.dirname(__file__))
import generate_display as g
DISPLAY_PS = "1b50d52324ab1a1aeb765cc9"
m = 1e-3
# STEP frame -> mount frame: X = Xs, Y = -Zs, Z = Ys + Z_STEP_OFF (proper rotation, det +1)
T_DISPLAY = [1, 0, 0, 0,   0, 0, -1, 0,   0, 1, 0, g.Z_STEP_OFF * m,   0, 0, 0, 1]
for e in g.api("GET", f"/documents/d/{g.DID}/w/{g.WID}/elements"):
    if e["elementType"] in ("ASSEMBLY", "BILLOFMATERIALS"):
        try: g.api("DELETE", f"/elements/d/{g.DID}/w/{g.WID}/e/{e['id']}"); print("deleted", e["name"])
        except SystemExit: print("already gone:", e["name"])
parts = g.api("GET", f"/parts/d/{g.DID}/w/{g.WID}/e/{g.PS}")
ASM = g.api("POST", f"/assemblies/d/{g.DID}/w/{g.WID}", {"name": "Display mount assembly"})["id"]; print("new assembly", ASM)
base = f"/assemblies/d/{g.DID}/w/{g.WID}/e/{ASM}"
def instances(): return g.api("GET", base)["rootAssembly"]["instances"]
for p in parts:
    if p["name"] in ("Backpack", "Crown ring", "GoPro puck", "Bench stand"):
        g.api("POST", f"{base}/instances", {"documentId": g.DID, "elementId": g.PS, "partId": p["partId"], "isWholePartStudio": False}); time.sleep(0.5)
print("mount parts inserted:", len(instances()))
before = {i["id"] for i in instances()}
g.api("POST", f"{base}/instances", {"documentId": g.DID, "elementId": DISPLAY_PS, "isWholePartStudio": True, "includePartTypes": ["PARTS"]}); time.sleep(3)
ids = [i["id"] for i in instances() if i["id"] not in before]
for attempt in range(4):
    try: g.api("POST", f"{base}/occurrencetransforms", {"occurrences": [{"path": [i]} for i in ids], "transform": T_DISPLAY, "isRelative": False}); break
    except SystemExit: print("  transform retry", attempt); time.sleep(5)
print(f"placed display: {len(ids)} part instances")
bb = g.api("GET", f"{base}/boundingboxes"); print("bbox mm:", {k: round(v * 1000, 1) for k, v in bb.items()})
print("ASSEMBLY_EID =", ASM)
