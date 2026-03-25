# freecad --console < c.py
import FreeCAD, Part, ObjectsFem, femmesh.gmshtools, femtools.ccxtools as ccx
from FreeCAD import Vector
import numpy as np
from types import SimpleNamespace
import os
import subprocess

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
    V N/2
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
    V 2*N+M-N/2
    z
""", "groove.pdf")

ensure("Part::Compound", "Compound")
doc.Compound.Links = [doc.tongue_solid,doc.groove_solid,]
doc.FileName = fcstdpath

for n in "MaterialSolid rightSymmetry MeshNetgen Contact Contact001 topFixed bottomDown SolverCcxTools Analysis".split():
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
mesh.Shape = doc.Compound
mesh.Fineness = "Fine"
mesh.SecondOrder = False
mesh.MaxSize = 3
doc.Analysis.addObject(mesh)

ObjectsFem.makeConstraintFixed(doc, "topFixed")
doc.topFixed.References = [(doc.groove_pad, ("Face1",))]

ObjectsFem.makeConstraintDisplacement(doc, "bottomDown")
doc.bottomDown.References = [(doc.tongue_pad, ("Face1",))]
doc.bottomDown.yFree = False
doc.bottomDown.yDisplacement = f"-{ydisp} mm"

ObjectsFem.makeConstraintDisplacement(doc, "rightSymmetry")
doc.rightSymmetry.References = [(doc.tongue_pad, ("Face10",)),(doc.groove_pad, ("Face10",)) ]
doc.rightSymmetry.xFree = False
doc.rightSymmetry.xDisplacement = "0 mm"

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

mat = ObjectsFem.makeMaterialSolid(doc)
mat.Material = {'Author': 'Uwe Stöhr', 'AuthorAndLicense': 'CC-BY-3.0', 'CardName': 'PLA-Generic', 'Density': '1.24e-06 kg/mm^3', 'Description': 'Polylactic acid or polylactide (PLA, Poly) is a biodegradable thermoplastic aliphatic polyester derived from renewable resources, such as corn starch, tapioca roots, chips, starch or sugarcane.', 'Father': 'Thermoplast', 'License': 'CC-BY-3.0', 'Name': 'PLA-Generic', 'PoissonRatio': '0.36', 'ProductURL': 'https://en.wikipedia.org/wiki/Polylactic_acid', 'ReferenceSource': '', 'SourceURL': 'https://www.sd3d.com/wp-content/uploads/2017/06/MaterialTDS-PLA_01.pdf', 'SpecificHeat': '1.8e+09 mm^2/(s^2*K)', 'ThermalConductivity': '130 mm*kg/(s^3*K)', 'ThermalExpansionCoefficient': '4.1e-05 1/K', 'UltimateTensileStrength': '26400 kg/(mm*s^2)', 'YieldStrength': '35900 kg/(mm*s^2)', 'YoungsModulus': '3.64e+06 kg/(mm*s^2)'}

solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
# solver.ModelSpace = u"plane strain" # faster but no longer needed
solver.GeometricalNonlinearity = True
solver.SplitInputWriter = False
solver.AnalysisType = 0
solver.ThermoMechSteadyState = True
solver.IterationsControlParameterTimeUse = False
solver.MatrixSolverType = 3
solver.BeamShellResultOutput3D = False
solver.MaterialNonlinearity = False

doc.Analysis.addObject(mat)
doc.Analysis.addObject(doc.rightSymmetry)
doc.Analysis.addObject(doc.bottomDown)
doc.Analysis.addObject(doc.topFixed)
doc.Analysis.addObject(solver)
doc.recompute()

fea = ccx.FemToolsCcx(doc.Analysis, solver)
fea.update_objects()
fea.setup_working_dir()
fea.setup_ccx()
fea.write_inp_file()

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
