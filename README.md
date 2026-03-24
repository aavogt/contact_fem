# Tongue & Groove parametric optimization

Work in progress plane strain contact problem. 

    c.py         update/generate b.FCStd and output.csv
    b.FCStd
    d.R          will call c.py, read output.csv, decide new parameters
    SketchSvg.py
    Uncross.py   unused

# bugs
## ObjectsFem.makeMeshNetgen

This might fix the next one:

## toponaming issue

I run c.py three times, and the TopoShapeExpansion.cpp(2052) errors happen after the third run

    time P_OVERRIDES="A=8" freecad --console < c.py 
    [FreeCAD Console mode <Use Ctrl-D (i.e. EOF) to exit.>]
    >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... ... ... ... ... >>> >>> >>> >>> >>> ... ... ... ... ... ... ... >>> >>> ... ... ... ... ... Importing project files......
    Postprocessing......    			(100 %)		
    >>> ... ... ... ... ... ... ... ... >>> >>> ... ... ... ... ... ... ... ... ... ... >>> >>> >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... ... ... ... Gtk-Message: 15:45:25.486: Failed to load module "window-decorations-gtk-module"
    Gtk-Message: 15:45:25.486: Failed to load module "colorreload-gtk-module"
    >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... ... ... ... ... Gtk-Message: 15:45:25.648: Failed to load module "window-decorations-gtk-module"
    Gtk-Message: 15:45:25.648: Failed to load module "colorreload-gtk-module"
    >>> >>> <Part::Compound>
    >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... >>> <Fem::ConstraintFixed object>
    >>> >>> <Fem::ConstraintDisplacement object>
    >>> >>> >>> >>> >>> <Fem::ConstraintRigidBody object>
    >>> >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... [<Fem::ConstraintContact object>]
    [<Fem::ConstraintContact object>]
    >>> >>> >>> >>> [<Fem::ConstraintDisplacement object>]
    >>> [<Fem::ConstraintFixed object>]
    >>> [<Fem::ConstraintRigidBody object>]
    >>> >>> >>> >>> >>> >>> [<Fem::FemSolverObjectPython object>]
    >>> >>> >>> >>> >>> >>> >>> 
    Get mesh data for constraints, materials and element geometry...
    [{'ccx_elset': 'Evolumes', 'ccx_elset_name': 'MaterialSolidSolid', 'mat_obj_name': 'MaterialSolid', 'ccx_mat_name': 'PLA-Generic'}]
    ConstraintFixed:
        Type: Fem::ConstraintFixed, Name: ConstraintFixed
        ReferenceShape ... Type: Face, Object name: groove_pad, Object label: groove_pad, Element name: Face1
    ConstraintDisplacement:
        Type: Fem::ConstraintDisplacement, Name: ConstraintDisplacement
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face1
    ConstraintRigidBody:
        Type: Fem::ConstraintRigidBody, Name: ConstraintRigidBody
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face10
        ReferenceShape ... Type: Face, Object name: groove_pad, Object label: groove_pad, Element name: Face10
    Contact:
        Type: Fem::ConstraintContact, Name: Contact
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face7
        ReferenceShape ... Type: Face, Object name: groove_pad, Object label: groove_pad, Element name: Face7
    Contact001:
        Type: Fem::ConstraintContact, Name: Contact001
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face4
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face4
    Getting mesh data time: 0.113 seconds.

    CalculiX solver input writing...
    Input file:b/SolverCcxTools/FEMMeshNetgen.inp
    Split input file.
    Writing time CalculiX input file: 0.022 seconds.
    >>> >>> >>> >>> ... ... ... ... ... ... ... >>> ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... >>> >>> ... ... ... ... ... ... ... ... "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4820B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.21' +wq b/SolverCcxTools/FEMMeshNetgen.inp
    <PropertyLinks> PropertyLinks.cpp(518): b#Contact001.References missing element reference b#tongue_pad ;#14d:43a;:G;XTR;:H2c4:7,F.Face4
    <PropertyLinks> PropertyLinks.cpp(518): b#Contact001.References missing element reference b#tongue_pad ;#14d:43a;:G;XTR;:H2c4:7,F.Face4
    <PropertyLinks> PropertyLinks.cpp(518): b#Contact.References missing element reference b#tongue_pad ;#14d:43d;:G;XTR;:H2c4:7,F.Face7
    <PropertyLinks> PropertyLinks.cpp(518): b#Contact.References missing element reference b#groove_pad ;#39:43d;:G;XTR;:H2cf:7,F.Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    Success with ydisp=0.21
    "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4835B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.33999999999999997' +wq b/SolverCcxTools/FEMMeshNetgen.inp
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    Success with ydisp=0.33999999999999997
    "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4820B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.47' +wq b/SolverCcxTools/FEMMeshNetgen.inp
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    Success with ydisp=0.47
    "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4819B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.6' +wq b/SolverCcxTools/FEMMeshNetgen.inp
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face7
    <Exception> TopoShapeExpansion.cpp(2052): Invalid shape name ?Face4
    Contact: Invalid shape name ?Face7
    Contact001: Invalid shape name ?Face4
    Success with ydisp=0.6
    >>> >>> 
    P_OVERRIDES="A=8" freecad --console < c.py  13.76s user 1.01s system 259% cpu 5.691 total
    ➜  contact_fem time P_OVERRIDES="A=8" freecad --console < c.py
    [FreeCAD Console mode <Use Ctrl-D (i.e. EOF) to exit.>]
    >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... ... ... ... ... >>> >>> >>> >>> >>> ... ... ... ... ... ... ... >>> >>> ... ... ... ... ... Importing project files......
    Postprocessing......    			(100 %)		
    >>> ... ... ... ... ... ... ... ... >>> >>> ... ... ... ... ... ... ... ... ... ... >>> >>> >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... ... ... ... Gtk-Message: 15:45:36.244: Failed to load module "window-decorations-gtk-module"
    Gtk-Message: 15:45:36.245: Failed to load module "colorreload-gtk-module"
    >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... ... ... ... ... Gtk-Message: 15:45:36.405: Failed to load module "window-decorations-gtk-module"
    Gtk-Message: 15:45:36.406: Failed to load module "colorreload-gtk-module"
    >>> >>> <Part::Compound>
    >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... >>> <Fem::ConstraintFixed object>
    >>> >>> <Fem::ConstraintDisplacement object>
    >>> >>> >>> >>> >>> <Fem::ConstraintRigidBody object>
    >>> >>> >>> >>> >>> ... ... ... ... ... ... ... ... ... [<Fem::ConstraintContact object>]
    [<Fem::ConstraintContact object>]
    >>> >>> >>> >>> [<Fem::ConstraintDisplacement object>]
    >>> [<Fem::ConstraintFixed object>]
    >>> [<Fem::ConstraintRigidBody object>]
    >>> >>> >>> >>> >>> >>> [<Fem::FemSolverObjectPython object>]
    >>> >>> >>> >>> >>> >>> >>> 
    Get mesh data for constraints, materials and element geometry...
    [{'ccx_elset': 'Evolumes', 'ccx_elset_name': 'MaterialSolidSolid', 'mat_obj_name': 'MaterialSolid', 'ccx_mat_name': 'PLA-Generic'}]
    ConstraintFixed:
        Type: Fem::ConstraintFixed, Name: ConstraintFixed
        ReferenceShape ... Type: Face, Object name: groove_pad, Object label: groove_pad, Element name: Face1
    ConstraintDisplacement:
        Type: Fem::ConstraintDisplacement, Name: ConstraintDisplacement
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face1
    ConstraintRigidBody:
        Type: Fem::ConstraintRigidBody, Name: ConstraintRigidBody
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face10
        ReferenceShape ... Type: Face, Object name: groove_pad, Object label: groove_pad, Element name: Face10
    Contact:
        Type: Fem::ConstraintContact, Name: Contact
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face7
        ReferenceShape ... Type: Face, Object name: groove_pad, Object label: groove_pad, Element name: Face7
    Contact001:
        Type: Fem::ConstraintContact, Name: Contact001
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face4
        ReferenceShape ... Type: Face, Object name: tongue_pad, Object label: tongue_pad, Element name: Face4
    Getting mesh data time: 0.113 seconds.

    CalculiX solver input writing...
    Input file:b/SolverCcxTools/FEMMeshNetgen.inp
    Split input file.
    Writing time CalculiX input file: 0.022 seconds.
    >>> >>> >>> >>> ... ... ... ... ... ... ... >>> ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... >>> >>> ... ... ... ... ... ... ... ... "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4820B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.21' +wq b/SolverCcxTools/FEMMeshNetgen.inp

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    Success with ydisp=0.21
    "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4835B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.33999999999999997' +wq b/SolverCcxTools/FEMMeshNetgen.inp

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    Success with ydisp=0.33999999999999997
    "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4820B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.47' +wq b/SolverCcxTools/FEMMeshNetgen.inp

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    Success with ydisp=0.47
    "b/SolverCcxTools/FEMMeshNetgen.inp" "b/SolverCcxTools/FEMMeshNetgen.inp" 160L, 4819B writtennvim --clean --headless +'/^ConstraintDisplacement' +'normal zO$T,C0.6' +wq b/SolverCcxTools/FEMMeshNetgen.inp

    CalculiX solver run...
    Everything seems fine. CalculiX ccx will be executed ......
    CalculiX finished without error.				

    CalculiX read results...
    Read ccx results from frd file: b/SolverCcxTools/FEMMeshNetgen.frd
    Read ccx results from dat file: b/SolverCcxTools/FEMMeshNetgen.dat
    Success with ydisp=0.6
    >>> >>> 
    P_OVERRIDES="A=8" freecad --console < c.py  14.71s user 0.99s system 252% cpu 6.227 total

