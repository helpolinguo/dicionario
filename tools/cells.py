"""Cutting a page into cells of the grid + detecting the underlines."""
import numpy as np
from scipy.ndimage import map_coordinates
from page import analyser

CW, CH = 12, 22
ETENDRE   = False      # extension of the block to the LEFT: moves the origin, case by case
ETENDRE_FORCE = 0       # forced widening to the left: see restore_starts.py
PROFONDEUR_MAX = 0.56  # a rule is not looked for lower, in units of leading.
                       # Calibrated on the 1,697 lines surveyed by eye: at 0.52 we lost
                       # 7 true rules and 85.2 % of exact ranges; at 0.56, 3 missing and
                       # 89.6 %. Beyond that the DEFIRS ghosts come back -- 11 at 0.60,
                       # 22 at 0.64.
ETENDRE_D = False      # extension of the block to the RIGHT: tried, set aside.
                       # It recovers a few line ends, but the re-cutting it
                       # entails loses headwords on 145 pages. The gain does not
                       # pay for the breakage.                        # raster of one cell
HAUT, BAS = 0.545, 0.50   # vertical extension of the cell, in fractions of the pitch

def runs_binaire(row, mini):
    out=[]; i=0; n=len(row)
    while i<n:
        if row[i]:
            j=i
            while j<n and row[j]: j+=1
            if j-i>=mini: out.append((i,j))
            i=j
        else: i+=1
    return out

def soulignements(r, lignes, pasv, pash, xg, ncol, couv_min=0.50):
    """Underline rules: horizontal runs, thin and solid, below the baseline.
    The typescript also uses DOUBLE underlines: we therefore survey every row
    of rule in the band, not the best one alone. Returns (rows, ranges of
    columns, coverage)."""
    B = r > 0.32
    mini = int(round(2.2*pash))
    H, W = r.shape
    res = {}
    for k, y in lignes:
        a0=max(int(round(y-0.10*pasv)),0); a1=min(int(round(y+0.45*pasv)),H)
        prof = r[a0:a1].sum(axis=1)
        if len(prof) < 4: res[k]=(None,[],0); continue
        base = a0 + int(np.argmin(np.diff(prof))) + 1
        cands=[]
        for yy in range(base+1, min(base+int(round(0.30*pasv))+2, H)):
            # A rule belongs to the zone of its OWN baseline.
            #
            # The capitals of the DEFIRS notation -- D, E, F, I, R, S -- all have
            # a flat top serif. Set end to end, their tops align into a
            # continuous horizontal bar, which falls into the search window of
            # the PRECEDING line. The detection took it for an underline and
            # referred it to the line above: « sur » in alineo, « lego » in
            # abrogar, « ta » of Voltaire in anakoluto, « kun » in amazono.
            #
            # First remedy, set aside: require white BENEATH the rule. It started
            # from a just observation -- beneath a true rule there is nothing,
            # beneath the top of letters there is the letter -- but it confused a
            # descender with the body of a letter. The « j » of « injektar » goes
            # down below its own underline: the rule was cut off there in
            # mid-word. It was so on **2,235 ranges, in 533 pages**.
            #
            # The right parting is geometric, and it is not fooled by a
            # descender: it is not the depth of a row, it is the depth of the
            # FIRST. A true rule begins between 0.32 and 0.48 of the leading
            # below the baseline -- measured on alineo, informar, injektar,
            # anakoluto. A false one appears only from 0.55, since it belongs to
            # the line below. We therefore stop the search at 0.52.
            if (yy - y) > PROFONDEUR_MAX*pasv: break
            rs=[(a,b) for a,b in runs_binaire(B[yy], 3) if r[yy, a:b].mean() > 0.40]
            # The ribbon wears: a rule breaks over one or two cells without
            # ceasing to be a rule. We reglue the pieces separated by less than
            # one cell before applying the minimum length.
            fus=[]
            for a,b in rs:
                if fus and a-fus[-1][1] <= 0.9*pash: fus[-1]=(fus[-1][0], b)
                else: fus.append((a,b))
            rs=[(a,b) for a,b in fus if b-a >= mini]
            tot=sum(b-a for a,b in rs)
            if tot: cands.append((tot, yy, rs))
        if not cands: res[k]=(None,[],0); continue
        tmax=max(c[0] for c in cands)
        retenus=[c for c in cands if c[0] >= 0.35*tmax]
        rangees=[c[1] for c in retenus]
        plages=set()
        for tot,yy,rs in retenus:
            for a,b in rs:
                if B[yy, a:b].mean() < 0.80: continue
                # A cell is underlined if the rule covers enough of it.
                # That is the direct measurement, cell by cell: it avoids rounding
                # the ends by judgement and letting the rule run over the full stop
                # or onto the next word.
                #
                # The threshold was 60 %. Too strict at the ends: the left edge of a
                # headword's rule is where the ribbon strikes, and its impression
                # there is short. Under « espino », the first cell was covered to
                # 59.9 % -- it fell, the rule then began in the middle of the word,
                # and generate.py threw away the headword's whole underline. Eight
                # headwords in a row went that way on page 155. At 50 %, the count
                # is right.
                j0=int(np.floor((a-xg)/pash))-1; j1=int(np.ceil((b-xg)/pash))+1
                dedans=[]
                for j in range(max(j0,0), min(j1+1, ncol)):
                    g=xg+j*pash; d=g+pash
                    couv=(min(b,d)-max(a,g))/pash
                    if couv >= couv_min: dedans.append(j)
                if not dedans: continue
                # we keep only contiguous runs
                deb=dedans[0]; prev=dedans[0]
                for j in dedans[1:]+[None]:
                    if j is None or j!=prev+1:
                        plages.add((deb, prev)); deb=j if j is not None else 0
                    prev=j if j is not None else prev
        # merging the ranges that overlap
        pl=sorted(plages); fus=[]
        for a,b in pl:
            if fus and a<=fus[-1][1]+1: fus[-1]=(fus[-1][0], max(fus[-1][1],b))
            else: fus.append((a,b))
        res[k]=(rangees, fus, tmax)
    return res

def _phase_locale(pv, x0, x1, p):
    """Phase of the Fourier component of period p over [x0,x1]."""
    x = np.arange(x0, x1); s = pv[x0:x1] - pv[x0:x1].mean()
    w = 2*np.pi/p
    return np.arctan2((s*np.sin(w*x)).sum(), (s*np.cos(w*x)).sum())

def raffiner_pas(r, bloc, pash, xg, tours=4):
    """Refines (pitch, phase). Two stages:

    1. minimising the ink falling on the cell boundaries;
    2. correcting the drift: the local phase is measured in windows across
       the block; if it drifts linearly, the pitch is wrong, and the slope
       gives exactly the correction. It is this that straightens the pages
       photographed at another scale.
    """
    y0,y1,x0,x1 = bloc
    pv = r[y0:y1+1].sum(axis=0)
    n = len(pv)
    best=(None,pash,xg)
    for p in np.linspace(pash*0.97, pash*1.03, 241):
        for ph in np.linspace(0, p, 40, endpoint=False):
            idx = np.clip(np.round(np.arange(ph, n, p)).astype(int), 0, n-1)
            s = pv[idx].mean()
            if best[0] is None or s < best[0]: best=(s,p,ph)
    p, ph = best[1], best[2]
    L = x1-x0
    if L > 12*p:
        for _ in range(tours):
            W = max(int(10*p), 60); pas_f = max(W//2, 1)
            cs=[]; phs=[]
            for a in range(x0, x1-W, pas_f):
                seg = pv[a:a+W]
                if seg.max() <= 0: continue
                cs.append(a+W/2); phs.append(_phase_locale(pv, a, a+W, p))
            if len(cs) < 4: break
            cs=np.array(cs); phs=np.unwrap(np.array(phs))
            A=np.vstack([cs, np.ones(len(cs))]).T
            pente,_ = np.linalg.lstsq(A, phs, rcond=None)[0]
            if not np.isfinite(pente) or abs(pente) < 1e-7: break
            inv = 1.0/p - pente/(2*np.pi)
            if inv <= 0: break
            p2 = 1.0/inv
            if abs(p2-p) > 0.05*p: break
            p = p2
        # rephasing on the corrected pitch
        meil=(None, ph)
        for phi in np.linspace(0, p, 200, endpoint=False):
            idx = np.clip(np.round(np.arange(phi, n, p)).astype(int), 0, n-1)
            s = pv[idx].mean()
            if meil[0] is None or s < meil[0]: meil=(s, phi)
        ph = meil[1]
    return p, ph

def extraire(chemin, garder_image=False):
    d = analyser(chemin)
    r = d['norm']; pasv=d['pasv']; pash=d['pash']; xg=d['xg']
    pash, xg = raffiner_pas(r, d['bloc'], pash, xg)
    H, W = r.shape
    xg = xg % pash                       # origin of the lattice brought back to the left edge
    ncol = int(np.floor((W - xg)/pash))
    sou = soulignements(r, d['lignes'], pasv, pash, xg, ncol)
    # image without underlines: horizontal morphological opening on the rule band
    # rc: a copy WITHOUT the underline rules. It serves only to decide which cells
    # are occupied and where column 0 begins; the cells delivered to the grouping
    # keep their underline (cross-check of the rule survey).
    from scipy.ndimage import grey_opening
    rc = r.copy()
    for k,(rangees,plages,tot) in sou.items():
        if not rangees or not plages: continue
        t0=max(min(rangees)-2,0); t1=min(max(rangees)+3,H)
        if t1-t0 < 1: continue
        for c0,c1 in plages:
            a=max(int(round(xg+c0*pash))-3,0); b=min(int(round(xg+(c1+1)*pash))+3,W)
            bande = rc[t0:t1, a:b]
            # A rule is a long horizontal structure: the opening retains it.
            # But a descender (g, p, q, y, j) crosses it; we keep it where there
            # is ink just above AND just below the band, or we gut the letters.
            filet = grey_opening(bande, size=(1,19))
            dessus = rc[max(t0-2,0):t0, a:b].max(axis=0) if t0>0 else np.zeros(b-a, np.float32)
            dessous = rc[t1:min(t1+2,H), a:b].max(axis=0) if t1<H else np.zeros(b-a, np.float32)
            traverse = (dessus > 0.30) & (dessous > 0.30)
            oté = np.clip(bande - filet, 0, 1)
            oté[:, traverse] = bande[:, traverse]
            rc[t0:t1, a:b] = oté
    # A horizontal offset peculiar to each line. The paper has cockled: the
    # grid's phase slides from one line to the next, sometimes by a third of a
    # cell at the foot of a page. We take it up line by line, at constant pitch.
    def phase_ligne(y):
        i0=max(int(round(y-0.45*pasv)),0); i1=min(int(round(y+0.45*pasv)),H)
        if i1-i0 < 4: return 0.0
        pv=r[i0:i1].sum(axis=0)
        if pv.max() <= 0: return 0.0
        n=len(pv); meil=(None,0.0)
        for dxx in np.linspace(-0.45*pash, 0.45*pash, 37):
            idx=np.clip(np.round(np.arange(xg+dxx, n, pash)).astype(int),0,n-1)
            s_=pv[idx].mean()
            if meil[0] is None or s_ < meil[0]: meil=(s_,dxx)
        return meil[1]
    decal = np.array([phase_ligne(y) for k,y in d['lignes']])

    # extraction of the cells
    ky = np.array([y for k,y in d['lignes']])
    kk = np.array([k for k,y in d['lignes']])
    fy = (np.arange(CH)+0.5)/CH*(HAUT+BAS)*pasv - HAUT*pasv
    fx = (np.arange(CW)+0.5)/CW*pash
    nl = len(ky)
    Y = (ky[:,None,None,None] + fy[None,None,:,None] + 0*fx[None,None,None,:])
    X = (xg + decal[:,None,None,None] + np.arange(ncol)[None,:,None,None]*pash
         + fx[None,None,None,:] + 0*fy[None,None,:,None])
    Y = np.broadcast_to(Y,(nl,ncol,CH,CW)).ravel()
    X = np.broadcast_to(X,(nl,ncol,CH,CW)).ravel()
    # rz: the rule's rows are simply whitened, with no opening. It is this
    # version that serves to decide whether a cell is occupied: it cannot
    # amputate a letter, whereas rc can.
    rz = r.copy()
    for k,(rangees,plages,tot) in sou.items():
        if not rangees or not plages: continue
        t0=max(min(rangees)-1,0); t1=min(max(rangees)+2,H)
        for c0,c1 in plages:
            a=max(int(round(xg+c0*pash))-3,0); b=min(int(round(xg+(c1+1)*pash))+3,W)
            rz[t0:t1, a:b]=0.0
    cells = map_coordinates(r,  [Y,X], order=1, mode='constant', cval=0.0).reshape(nl,ncol,CH,CW)
    nues  = map_coordinates(rc, [Y,X], order=1, mode='constant', cval=0.0).reshape(nl,ncol,CH,CW)
    horsf = map_coordinates(rz, [Y,X], order=1, mode='constant', cval=0.0).reshape(nl,ncol,CH,CW)
    # renumbering: column 0 = the page's first inked column
    # A cell is occupied if it carries enough ink AND if that ink is not a
    # mere smudge from the neighbouring character. The smudge criterion (ink
    # pressed against the edge of the cell) is calibrated on the cases
    # surveyed by hand; it allows the ink threshold to be lowered to 5 pixels,
    # which catches the very pale full stops.
    plat = horsf.reshape(nl, ncol, -1)
    encre = (plat > 0.35).sum(-1)
    somme = plat.sum(-1)
    bordg = horsf[:,:,:,:2].sum((2,3)) + horsf[:,:,:,-2:].sum((2,3))
    partbord = bordg/(somme+1e-6)
    bavure = (partbord > 0.55) | ((somme < 12) & (partbord > 0.25))
    occ = (encre >= 5) & ~bavure
    frac = occ.mean(axis=0)
    # a column occupied on nearly every line at the edge of the page is the
    # shadow of the paper's edge, not a column of text: we subtract it.
    bord = frac >= 0.98
    use = occ.sum(axis=0) >= 3
    idx = np.where(use)[0]
    if len(idx):
        g, dte = int(idx.min()), int(idx.max())
        while g < dte and bord[g]: g += 1          # shadow of the left edge
        while dte > g and bord[dte]: dte -= 1      # shadow of the right edge
        while g < dte and not use[g]: g += 1
        while dte > g and not use[dte]: dte -= 1
        # The block is bounded by the columns occupied on at least three lines.
        # That is robust to noise, but it amputates the columns only one line
        # reaches: on page 6, « donacinti » is the only word to touch the
        # margin, and it became « acinti ».
        #
        # Extending the block to every inked column corrects that case -- but
        # destabilises the lattice elsewhere: eight pages of the body lost every
        # one of their headwords, the text coming back interleaved. The
        # extension is therefore case by case, switched on by the flag below for
        # the only pages where it is safe: the front matter, where the text is
        # sparse and there is no headword to lose.
        use1 = occ.sum(axis=0) >= 1
        # On the RIGHT, the extension is safe: it adds columns only after the
        # others, without moving the origin -- the numbering of the columns does
        # not move, so no correction already made is invalidated. It gives back
        # the line ends the block was cutting off: « preciz », « apa », « anon ».
        if ETENDRE_D:
            while dte < ncol-1 and use1[dte+1] and not bord[dte+1]: dte += 1
        # On the LEFT, it moves the origin and shifts everything: it lost eight
        # pages of the body every one of their headwords. Reserved, by the flag
        # below, for the pages where the text is sparse and headword-free.
        if ETENDRE:
            while g > 0 and use1[g-1] and not bord[g-1]: g -= 1
        # FORCED widening to the left, with no condition of use. The rule above
        # requires that a column serve on several lines; but the first letter of
        # a headword begun one cell too early is often alone in its column --
        # « sorgumo », « jorno ». It therefore triggers nothing. This flag is
        # used only by restore_starts.py, which re-cuts in memory and does not
        # touch the corpus: what it brings back in excess is set aside afterwards
        # by the smudge filter and by the decoding, which must return a real
        # character.
        if ETENDRE_FORCE:
            g = max(0, g - int(ETENDRE_FORCE))
        c0, cmax = g, dte
    else:
        c0, cmax = 0, ncol-1
    cells = cells[:, c0:cmax+1]; nues = nues[:, c0:cmax+1]; occ = occ[:, c0:cmax+1]
    ncol = cells.shape[1]
    kk = kk - kk.min()
    sou = {k:(yy,[(a-c0,b-c0) for a,b in pl],t) for k,(yy,pl,t) in sou.items()}
    out = dict(pasv=pasv, pash=pash, xg=xg, col0=c0, angle=d['angle'], bloc=d['bloc'],
               lignes=list(zip(kk.tolist(), ky.tolist())), ncol=ncol, decal=decal,
               cells=cells, nues=nues, occ=occ, sou=sou, shape=(H,W))
    if garder_image: out['norm']=r; out['nettoye']=rc
    return out
