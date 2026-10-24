"""Source normalized quadgram sum, streamed in exact character order."""
import numpy as np
from numba import njit
import engine as e
@njit(cache=False)
def score_paths(paths,dense,letters,lens):
    result=np.empty(len(paths),np.float64)
    for row in range(len(paths)):
        tail=0;size=0;total=0.
        for pos in range(paths.shape[1]):
            rune=paths[row,pos]
            for j in range(lens[rune]):
                code=tail*26+letters[rune,j]
                if size>=3:total+=dense[code]
                tail=code%(26**3);size+=1
        result[row]=total/(size-3) if size>3 else -999.
    return result
def normalized(paths):return score_paths(paths,e.DENSE,e.LETTERS,e.LENGTHS)
