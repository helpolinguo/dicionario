import numpy as np
from PIL import Image
def montage(cells, cols=32, zoom=3, sep=1, fond=255):
    n=len(cells); h,w=cells[0].shape
    rows=(n+cols-1)//cols
    W=cols*(w+sep)+sep; H=rows*(h+sep)+sep
    A=np.full((H,W),fond,np.uint8)
    for i,c in enumerate(cells):
        r,cc=divmod(i,cols)
        y=sep+r*(h+sep); x=sep+cc*(w+sep)
        A[y:y+h, x:x+w]=255-c
    im=Image.fromarray(A)
    return im.resize((W*zoom,H*zoom), Image.NEAREST)
