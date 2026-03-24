# freecad --console < c.py
import FreeCAD, Part, ObjectsFem, femmesh.gmshtools, femtools.ccxtools as ccx
from FreeCAD import Vector
import numpy as np
from types import SimpleNamespace
import os

import sys
sys.path += ["."]
import SketchSvg

# ── Parameters ────────────────────────────────────────────────────────────────
p = dict(
    W=40, M=30, N=20, L=60,   # outer envelope
    A=12,  # tongue side lengths
    B=8,
    C=4,
    D=12,
    E=4,
    F=4,
    H=0.2,       # uniform gap between tongue and groove on contact faces
    depth=10.0,  # extrusion depth (z)
    ydisp_min = 0.21,
    ydisp_max = 0.6,
    nydisp = 4,
)
ydisp = 0.4 # initial value replaced by set_ydisp() before actually running


raw = os.environ.get("P_OVERRIDES", "")
if raw:
    import re
    for match in re.finditer(r"([A-Za-z_]\w*)\s*=\s*([^\s,;]+)", raw):
        key, val = match.group(1), match.group(2)
        if key not in p:
            print(f"Warning: P_OVERRIDES key '{key}' has no default and is being added")
        p[key] = float(val)

fcstdpath = 'b.FCStd'
if os.path.exists(fcstdpath):
    doc = FreeCAD.openDocument(name=fcstdpath, hidden=True)
    pass
else:
    doc = FreeCAD.newDocument();

def ensure(type, name, parent=None):
    xs = doc.findObjects(type, name)
    if not hasattr(doc, name):
        if parent is None:
            doc.addObject(type, name)
        else:
            parent.newObject(type, name)
    return getattr(doc, name)


def addFindBodySketch(base):
    bodyname = base + "_solid"
    sketchname = base + "_sketch"
    padname = base + "_pad"
    body = ensure("PartDesign::Body", bodyname)
    sketch= ensure("Sketcher::SketchObject", sketchname, body)
    pad = ensure('PartDesign::Pad',padname, body)
    pad.Profile = sketch
    pad.Visibility = True # https://github.com/FreeCAD/FreeCAD/issues/28555
    body.Visibility = True

addFindBodySketch("tongue")
addFindBodySketch("groove")

doc.tongue_sketch.deleteAllGeometry()
doc.tongue_sketch.deleteAllConstraints()
SketchSvg.add(p, doc.tongue_sketch, """
    h -W/2
    v N+B
    h A
    v -B
    h C
    v D
    h -E
    v F
    H 0
    V 1
    z
""", "tongue.pdf")
#
doc.groove_sketch.deleteAllGeometry()
doc.groove_sketch.deleteAllConstraints()
SketchSvg.add(p, doc.groove_sketch, """
    M 0,2*N+M
    h -W/2
    v B+H-N-M
    h A+H
    v -B
    h C-2*H
    v D-2*H
    h -E
    v F+2*H
    H 0
    V 2*N+M-1
    z
""", "groove.pdf")

ensure("Part::Compound", "Compound")
doc.Compound.Links = [doc.tongue_solid,doc.groove_solid,]
doc.FileName = fcstdpath

for n in "Contact Contact001 ConstraintFixed ConstraintDisplacement ConstraintRigidBody SolverCcxTools".split():
    try:
        doc.removeObject(n)
    except:
        pass
    try:
        doc.Analysis.removeObject(n)
    except:
        pass

ObjectsFem.makeConstraintFixed(doc, "ConstraintFixed")
doc.ConstraintFixed.References = [(doc.groove_pad, ("Face1",))]
ObjectsFem.makeConstraintDisplacement(doc, "ConstraintDisplacement")
doc.ConstraintDisplacement.References = [(doc.tongue_pad, ("Face1",))]
doc.ConstraintDisplacement.yFree = False
doc.ConstraintDisplacement.yDisplacement = f"-{ydisp} mm"

ObjectsFem.makeConstraintRigidBody(doc, "ConstraintRigidBody")
doc.ConstraintRigidBody.References = [(doc.tongue_pad, ("Face10",)),(doc.groove_pad, ("Face10",)) ]
doc.ConstraintRigidBody.TranslationalModeX = "Constraint"

# tongue_pad:Face10 groove_pad:Face10 constrained x=0mm
for n in "Contact Contact001".split():
    o = ObjectsFem.makeConstraintContact(doc, n)
    o.Slope = "1000.0 GPa/m"
    o.Adjust = "0.0 mm"
    o.Friction = False
    o.FrictionCoefficient = 0.000000
    o.StickSlope = "10000.0 GPa/m"
    o.Scale = 1.000000
    doc.Analysis.addObject(o)

doc.Contact.References = [(doc.tongue_pad,"Face7"), (doc.groove_pad,"Face7")]
doc.Contact001.References = [(doc.tongue_pad, ("Face4", )), (doc.tongue_pad, ("Face4", ))]

doc.Analysis.addObject(doc.ConstraintDisplacement)
doc.Analysis.addObject(doc.ConstraintFixed)
doc.Analysis.addObject(doc.ConstraintRigidBody)

# can't yet replace FEM_MeshNetgenFromShape
# mesh = ObjectsFem.makeMeshNetgen()
# mesh.Shape = doc.Compound
# mesh.Fineness = "Fine"
# doc.Analysis.addObject(mesh)
solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
solver.ModelSpace = u"plane strain"
solver.GeometricalNonlinearity = True
solver.SplitInputWriter = True
doc.Analysis.addObject(solver)

fea = ccx.FemToolsCcx(doc.Analysis, solver)
fea.update_objects()
fea.setup_working_dir()
fea.setup_ccx()
fea.write_inp_file()
import subprocess

## set displacement
def set_disp(newydisp):
    # is this worth it?
    # I'm having trouble running these in parallel
    # but they are inherently sequential and the caller should just make b1 b2 b3 dirs and run c.py in each with different parameters
    cmd = f"nvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C{newydisp}' +wq b/SolverCcxTools/FEMMeshNetgen.inp"
    subprocess.run(cmd, shell=True, text=True)
    print(cmd)

def step():
    fea.purge_results()
    fea.ccx_run()
    fea.load_results()
    results = doc.getObject("CCX_Results")
    maxvm = float(max(results.vonMises))
    row = [ydisp, maxvm] + [ float(component) for component in subprocess.run("grep -A2 CONSTRAINTFIXED b/SolverCcxTools/FEMMeshNetgen.dat", shell=True, text=True, capture_output=True).stdout.split()[-3:] ]
    if not os.path.exists("output.csv"):
        with open('output.csv', mode='w') as csvfile:
            pheader = ",".join(p.keys())
            csvfile.write(f"ydisp,maxvm,fx,fy,fz,{pheader}\n")
            csvfile.close()
    with open('output.csv', mode='a') as csvfile:
        csvfile.write(",".join(map(str, row) ))
        for v in p.values():
            csvfile.write("," + str(v))
        csvfile.write("\n")


for ydisp in np.linspace(p["ydisp_min"],p["ydisp_max"], int(p["nydisp"])):
    try:
        set_disp(ydisp)
        step()
        print(f"Success with ydisp={ydisp}")
    except Exception as e:
        print(f"Failed with ydisp={ydisp}")
        break

doc.save() # probably already done
