from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'lp2-54-55-autokey-reset'))
from engine import main
if __name__ == '__main__':
    main(HERE)
