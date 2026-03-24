# probably works but not used in SketchSvg yet
import numpy as np

def uncross(verts):
    n = len(verts)
    changed = True
    while changed:
        changed = False
        for i in range(n):
            for j in range(i+2, n):
                a, b = verts[i], verts[(i+1) % n]
                c, d = verts[j], verts[(j+1) % n]
                if _segments_cross(a, b, c, d):
                    # reverse the segment between i+1 and j inclusive
                    verts[i+1:j+1] = verts[i+1:j+1][::-1]
                    changed = True
    return verts

## does a-b cross c-d not just at endpoints
def _segments_cross(a, b, c, d) -> bool:
    a = np.asarray(a)
    b = np.asarray(b)
    c = np.asarray(c)
    d = np.asarray(d)
    m = np.transpose(np.array([b-a, c - d]))
    st = np.linalg.solve(m, c-a)
    return all(st < 1) and all(st > 0)

if __name__ == "__main__":
    print(_segments_cross([0,0], [-1,-1], [0,1],[1,0]))
    print(_segments_cross([0,0], [1,1], [0,1],[1,0]))
