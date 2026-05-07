# freecad --console < c.py
# https://forum.freecad.org/viewtopic.php?p=886426
# pinch valve
#
# TODO inner contact
# TODO:Leakage detection
#
# leakage means there is a path along the inner wall along the length of tubing
# where contact pressure is below a threshold
#
# ./tube3/SolverCcxTools/msp.py
# parses frd
# networkx's dijkstra on the node graph with 1/contact pressure weights
# three stages to make sure the two half paths go around the tube
# will be improved by
#
# cel file needed to see what contacts what?
#
# *CONTACT FILE, MASTER=INDConstraintContact, SLAVE=DEPConstraintContact, CONTACT ELEMENTS
# COPEN, CSTR, CPRESS
#
# but it's moot because I can't get contact between inner tube faces
# even after splitting the inner tube
# tie constraints are inaccurate
import FreeCAD, Part, ObjectsFem, femmesh.gmshtools, femtools.ccxtools as ccx
import BOPTools.SplitFeatures # to generate BooleanFragments
from FreeCAD import Vector
import numpy as np
import os
import subprocess
import sqlite3

import sys
sys.path += ["."]
import SketchSvg

# ── Parameters ────────────────────────────────────────────────────────────────
p = dict(
    ID=1.5, OD=3.0, # tubing dimensions in xy plane
    t=1, # jaw thickness in xy-plane
    nmandible = 1, # moving teeth low y
    nmaxilla = 2,  # fixed teeth high y
    odgap=0.5, # the tooth touches the tube along three lines if odgap=0,
               # otherwise this makes the tooth wider (x axis)
    tiegap=0.01, # tube is split into utube and ttube
    tooth_pitch = 5, # teeth on a jaw start every tooth_pitch mm in z
    oman = 2.5,      # +z offset for mandible teeth
    tooth_width = 2, # tooth z dimension
    # run ccx multiple times with [ydisp_min, ydisp_min+nydisp .. ydisp_max] displacements
    # nydisp=1 means [ydisp_min]
    ydisp_min=2.0, ydisp_max=3.0, nydisp=1
)

# P_OVERRIDES="A=3,B=3;C=4 D=5" freecad --console < c.py
raw = os.environ.get("P_OVERRIDES", "")
if raw:
    import re
    for match in re.finditer(r"([A-Za-z_]\w*)\s*=\s*([^\s,;]+)", raw):
        key, val = match.group(1), match.group(2)
        if key not in p:
            print(f"Warning: P_OVERRIDES key '{key}' has no default and is being added")
        p[key] = float(val)

def init_db():
    db_path = os.environ.get("DB", "db.sqlite3")
    conn = sqlite3.connect(db_path, timeout=10)
    _= conn.execute("PRAGMA foreign_keys = ON")
    _= conn.execute("PRAGMA journal_mode=WAL")
    p_cols = ", ".join([f"{k} REAL" for k in p.keys()])
    _ = conn.execute(f"""
        CREATE TABLE IF NOT EXISTS p (
            p_id INTEGER PRIMARY KEY AUTOINCREMENT,
            {p_cols},
            tongue_svg BLOB,
            groove_svg BLOB
        )
    """)
    _= conn.execute("""
        CREATE TABLE IF NOT EXISTS q (
            p_id INTEGER NOT NULL,
            ydisp REAL NOT NULL,
            maxvm REAL NOT NULL,
            fx REAL NOT NULL,
            fy REAL NOT NULL,
            fz REAL NOT NULL,
            FOREIGN KEY (p_id) REFERENCES p(p_id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    return conn

conn = init_db()

def insert_p():
    global conn
    cols = ", ".join(p.keys())
    placeholders = ", ".join(["?"] * len(p))
    values = [float(v) for v in p.values()]
    _ = conn.execute(f"INSERT INTO p ({cols}) VALUES ({placeholders})", values)
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

p_id = insert_p()
with open("p_id", "w") as f:
    _ = f.write(str(p_id) + '\n')
    f.close()

def _read_blob(path):
    with open(path, "rb") as f:
        return sqlite3.Binary(f.read())

def update_p_blobs(tongue_svg, groove_svg):
    global conn, p_id
    _= conn.execute(
        """
        UPDATE p
        SET tongue_svg = ?, groove_svg = ?
        WHERE p_id = ?
        """,
        (tongue_svg, groove_svg, p_id),
    )
    conn.commit()

fcstdpath = 'b.FCStd'
if os.path.exists(fcstdpath):
    doc = FreeCAD.openDocument(name=fcstdpath, hidden=True)
    pass
else:
    doc = FreeCAD.newDocument();
    doc.FileName = fcstdpath

def ensure(type, name, parent=None):
    xs = doc.findObjects(type, name)
    if not hasattr(doc, name):
        if parent is None:
            doc.addObject(type, name)
        else:
            parent.newObject(type, name)
    return getattr(doc, name)

# BooleanFragments lets the tube have mat1 / inp file edited to *HYPERELASTIC
if hasattr(doc, "BooleanFragments"):
    doc.removeObject("BooleanFragments")

booleanFragments = BOPTools.SplitFeatures.makeBooleanFragments(name='BooleanFragments')
# also make a compound for fc2stl b.FCStd & f3d --watch b-Compound.stl
ensure("Part::Compound", "Compound")
doc.Compound.Links = []

def addFindBodySketch(base):
    bodyname = base + "_solid"
    sketchname = base + "_sketch"
    padname = base + "_pad"
    body = ensure("PartDesign::Body", bodyname)
    sketch = ensure("Sketcher::SketchObject", sketchname, body)
    pad = ensure('PartDesign::Pad',padname, body)
    pad.Profile = sketch
    body.Visibility = False
    booleanFragments.Objects += [body]
    doc.Compound.Links += [body]

# n = len(doc.man_pad.Shape.Faces)
# max face i*n +1,i*n 2, i*n + 3 contact tube 1
def place_sketch(basei, x=0.0, y = 0.0, z=0.0) :
    doc.getObject(basei + "_sketch").Placement = FreeCAD.Placement(FreeCAD.Vector(x,y,z),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))

addFindBodySketch("ttube")
doc.ttube_sketch.deleteAllGeometry()
doc.ttube_sketch.deleteAllConstraints()
SketchSvg.add(p, doc.ttube_sketch, """
    M OD/2,0
    A OD/2,OD/2,180,0,0,-OD/2,0
    H -ID/2
    A ID/2,ID/2,180,0,1,ID/2,0
    z
""", "ttube.svg")

place_sketch("ttube", 0, p["tiegap"])

addFindBodySketch("utube")
doc.utube_sketch.deleteAllGeometry()
doc.utube_sketch.deleteAllConstraints()
SketchSvg.add(p, doc.utube_sketch, """
    M OD/2,0
    A OD/2,OD/2,180,0,1,-OD/2,0
    H -ID/2
    A ID/2,ID/2,180,0,0,ID/2,0
    z
""", "utube.svg")

doc.ttube_pad.SideType = 1
doc.utube_pad.SideType = 1


manw = p['oman'] + ( p['nmandible'] - 1) * p['tooth_pitch'] + p['tooth_width']
maxw = (p['nmaxilla']-1) * p['tooth_pitch'] + p['tooth_width']
doc.utube_pad.Length = max(manw, maxw) + 1
doc.ttube_pad.Length = max(manw, maxw) + 1
doc.utube_pad.Length2 = "5 mm"
doc.ttube_pad.Length2 = "5 mm"
doc.Compound.Links += [doc.ttube_body, doc.utube_body]
doc.Compound.Visibility = True

def mansk(sk):
    sk.deleteAllGeometry()
    sk.deleteAllConstraints()
    SketchSvg.add(p, sk, """
        M odgap+OD/2,0
        v -OD/2
        h -OD-2*odgap
        v OD/2
        h -t
        v -OD/2-t
        h OD + 2*t + 2*odgap
        v OD/2+t
        z
    """, "man.svg")

## same as mansk but flipped in the y axis
def maxsk(sk):
    sk.deleteAllGeometry()
    sk.deleteAllConstraints()
    SketchSvg.add(p, sk, """
        M odgap+OD/2,0
        v OD/2
        h -OD-2*odgap
        v -OD/2
        h -t
        v OD/2+t
        h OD + 2*t+2*odgap
        v -OD/2-t
        z
    """, "max.svg")

for i in range(p['nmandible']):
    addFindBodySketch(f"man{i}") # mandible
    mansk(doc.getObject(f"man{i}_sketch"))
    doc.getObject(f"man{i}_pad").Length = p['tooth_width']
    place_sketch(f"man{i}", z = p['oman'] + p['tooth_pitch']*i)

for i in range(p['nmaxilla']):
    addFindBodySketch(f"max{i}") # maxilla not happy about the names
    maxsk(doc.getObject(f"max{i}_sketch"))
    doc.getObject(f"max{i}_pad").Length = p['tooth_width']
    place_sketch(f"max{i}", y = p['tiegap'], z = p['tooth_pitch']*i)

booleanFragments.Mode = 'Standard'
booleanFragments.Proxy.execute(booleanFragments)
booleanFragments.purgeTouched()
for obj in booleanFragments.ViewObject.Proxy.claimChildren():
     obj.ViewObject.hide()



doc.recompute()
doc.save()
update_p_blobs( _read_blob("tongue.svg"), _read_blob("groove.svg"),)


ncontact = max(3 * 2 * 3,3*(p['nmaxilla'] + p['nmandible']))
for n in "maxFixed manUpY tubeEnds MaterialSolid MaterialSolid001 MeshNetgen Contact SolverCcxTools Analysis tie1 tie2".split() + [
        f"Contact{i:03d}" for i in range(ncontact) ]:
    try:
        doc.removeObject(n)
    except:
        pass
    try:
        doc.Analysis.removeObject(n)
    except:
        pass


ObjectsFem.makeAnalysis(doc)
mesh = ObjectsFem.makeMeshNetgenLegacy(doc)
mesh.Shape = doc.BooleanFragments
mesh.Fineness = "VeryCoarse"
mesh.SecondOrder = False
mesh.MaxSize = 0.5
doc.Analysis.addObject(mesh)

ObjectsFem.makeConstraintTie(doc, "tie1")
doc.tie1.References = [(doc.utube_pad, ("Face1", )),(doc.ttube_pad, ("Face1", ))]
doc.tie1.Tolerance = p['tiegap']*1.1
ObjectsFem.makeConstraintTie(doc, "tie2")
doc.tie2.References = [(doc.utube_pad, ("Face2", )),(doc.ttube_pad, ("Face2", ))]
doc.tie2.Tolerance = p['tiegap']*1.1

# max{i}_pad.Face6 fixed
ObjectsFem.makeConstraintFixed(doc, "maxFixed")
doc.maxFixed.References = [(doc.getObject(f"max{i}_pad"), ("Face6",)) for i in range(p['nmaxilla'])]

ObjectsFem.makeConstraintFixed(doc, "tubeEnds")
doc.tubeEnds.References = [ (doc.utube_pad, ('Face6',)), (doc.ttube_pad, ('Face6',))] # , (doc.utube_pad, ('Face5',)), (doc.ttube_pad, ('Face6',)), ]

# man{i}_pad.Face6 goes to +y
ObjectsFem.makeConstraintDisplacement(doc, "manUpY")
doc.manUpY.References = [(doc.getObject(f"man{i}_pad"), ("Face6",)) for i in range(p['nmandible'])]
doc.manUpY.yFree = False
doc.manUpY.xFree = False
doc.manUpY.zFree = False
doc.manUpY.yDisplacement = f"1.5 mm"

from collections import deque
import itertools

# contact faces:
# tube face 1, 2 top and bottom
# tube face 3, 4 inside
# tube face 5 low z
# tube face 6 high z
#
# max{i} face 1,2,3 contact tube 1 for i in range(p['nmandible'])
# man{i} face 1,2,3 contact tube 2, i in range(p['nmaxilla'])
#
# after tube split int ttube and utube:
# tube 1 -> t 1
# tube 2 -> u 1
# tube 3 -> t 3
# tube 4 -> u 3
# tube 5 -> t 5 u 5
# tube 6 -> t 6 u 6

def contactPairsMandible(j):
    return ([ (doc.utube_pad, ("Face1",)), (doc.getObject(f"man{i}_pad"), (f"Face{j}",)) ] for i in range(p['nmandible']))

def contactPairsMaxilla(j):
    return ([ (doc.ttube_pad, ("Face1",)), (doc.getObject(f"max{i}_pad"), (f"Face{j}",)) ] for i in range(p['nmaxilla']))

def contactPairsMMj(j) :
    return itertools.chain(contactPairsMandible(j), contactPairsMaxilla(j))

contactPairs= deque(row for j in [1, 2, 3] for row in contactPairsMMj(j))
contactPairs.append([ (doc.ttube_pad, ("Face3", )), (doc.utube_pad, ("Face3", ))])
for n in [ f"Contact{i:03d}" for i in range(1, 3*(p['nmaxilla'] + p['nmandible']) + 1) ]:
    o = ObjectsFem.makeConstraintContact(doc, n)
    o.Slope = "100000.0 GPa/m"
    o.Adjust = p['tiegap']
    o.Friction = False
    o.FrictionCoefficient = 0.500000
    o.StickSlope = "10000.0 GPa/m"
    o.Scale = 1.000000
    o.References = contactPairs.pop()
    doc.Analysis.addObject(o)

mat = ObjectsFem.makeMaterialSolid(doc)
mat.Material = {'Author': 'Uwe Stöhr', 'AuthorAndLicense': 'CC-BY-3.0', 'CardName': 'PLA-Generic', 'Density': '1.24e-06 kg/mm^3', 'Description': 'Polylactic acid or polylactide (PLA, Poly) is a biodegradable thermoplastic aliphatic polyester derived from renewable resources, such as corn starch, tapioca roots, chips, starch or sugarcane.', 'Father': 'Thermoplast', 'License': 'CC-BY-3.0', 'Name': 'PLA-Generic', 'PoissonRatio': '0.36', 'ProductURL': 'https://en.wikipedia.org/wiki/Polylactic_acid', 'ReferenceSource': '', 'SourceURL': 'https://www.sd3d.com/wp-content/uploads/2017/06/MaterialTDS-PLA_01.pdf', 'SpecificHeat': '1.8e+09 mm^2/(s^2*K)', 'ThermalConductivity': '130 mm*kg/(s^3*K)', 'ThermalExpansionCoefficient': '4.1e-05 1/K', 'UltimateTensileStrength': '26400 kg/(mm*s^2)', 'YieldStrength': '35900 kg/(mm*s^2)', 'YoungsModulus': '3.64e+06 kg/(mm*s^2)'}
mat1 = ObjectsFem.makeMaterialSolid(doc)
mat1.Material = {'Author': 'Uwe Stöhr', 'AuthorAndLicense': 'CC-BY-3.0', 'CardName': 'PLA-Generic', 'Density': '1.24e-06 kg/mm^3', 'Description': 'Polylactic acid or polylactide (PLA, Poly) is a biodegradable thermoplastic aliphatic polyester derived from renewable resources, such as corn starch, tapioca roots, chips, starch or sugarcane.', 'Father': 'Thermoplast', 'License': 'CC-BY-3.0', 'Name': 'PLA-Generic', 'PoissonRatio': '0.36', 'ProductURL': 'https://en.wikipedia.org/wiki/Polylactic_acid', 'ReferenceSource': '', 'SourceURL': 'https://www.sd3d.com/wp-content/uploads/2017/06/MaterialTDS-PLA_01.pdf', 'SpecificHeat': '1.8e+09 mm^2/(s^2*K)', 'ThermalConductivity': '130 mm*kg/(s^3*K)', 'ThermalExpansionCoefficient': '4.1e-05 1/K', 'UltimateTensileStrength': '26400 kg/(mm*s^2)', 'YieldStrength': '35900 kg/(mm*s^2)', 'YoungsModulus': '3.64e+06 kg/(mm*s^2)'}
mat1.References = [ doc.ttube_pad, doc.utube_pad ]

solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
solver.GeometricalNonlinearity = True
solver.SplitInputWriter = True
solver.AnalysisType = 0
solver.MaterialNonlinearity = True
solver.DisplaceMesh = False # True?

doc.Analysis.addObject(mat)
doc.Analysis.addObject(mat1)
doc.Analysis.addObject(doc.manUpY)
doc.Analysis.addObject(doc.tubeEnds)
doc.Analysis.addObject(doc.maxFixed)
doc.Analysis.addObject(doc.tie1)
doc.Analysis.addObject(doc.tie2)
doc.Analysis.addObject(solver)
doc.recompute()
doc.save()

fea = ccx.FemToolsCcx(doc.Analysis, solver)
fea.update_objects()
fea.setup_working_dir()
fea.setup_ccx()
fea.write_inp_file()

# Finds
# > ** MaterialSolid001
# > *MATERIAL, NAME=MaterialSolid001
# > *ELASTIC
# > 3640,0.36
# > *EXPANSION, ZERO=0
# > 4.1E-05
#
# turns it into
#
# > *HYPERELASTIC, NEO-HOOKE
# > 0.738,1e3
# > *EXPANSION, ZERO=0
# > 4.1E-05
def set_material():
    cmd=r"""sed '/\*MATERIAL, NAME=MaterialSolid001/{ n; N; c\
*HYPERELASTIC, NEO-HOOKE\
0.738,1e3
}' -i b/SolverCcxTools/MeshNetgen.inp"""
    subprocess.run(cmd, shell=True, text=True)
    print(cmd)

def set_disp(newydisp):
    cmd = rf"sed 's/^\(manUpY,2,2,\).*/\1{newydisp}/' -i b/SolverCcxTools/MeshNetgen.inp"
    subprocess.run(cmd, shell=True, text=True)
    print(cmd)

set_material()
for ydisp in np.linspace(p["ydisp_min"],p["ydisp_max"], int(p["nydisp"])):
    try:
        set_disp(ydisp)
        fea.purge_results()
        fea.ccx_run()
        fea.load_results()
        # separate jaw and tubing stress?
        results = doc.getObject("CCX_Results")
        maxvm = float(max(results.vonMises))
        fx, fy, fz = [
            float(component)
            for component in subprocess.run(
                "grep -A2 MANUPY b/SolverCcxTools/MeshNetgen.dat",
                shell=True,
                text=True,
                capture_output=True,
            ).stdout.split()[-3:]
        ]
        _= conn.execute(
            "INSERT INTO q (p_id, ydisp, maxvm, fx, fy, fz) VALUES (?, ?, ?, ?, ?, ?)",
            (p_id, ydisp, maxvm, fx, fy, fz),
        )
        conn.commit()
        print(f"Success with ydisp={ydisp}")
    except Exception as e:
        print(f"Failed with ydisp={ydisp}")
        break

doc.recompute()
doc.save()
