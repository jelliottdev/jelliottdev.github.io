"""Compare fresh source T0/T1 JSON with the immutable saved outputs; no scan."""
import argparse,json,math
from pathlib import Path
H=Path(__file__).resolve().parent
FLOAT_TOLERANCE=0.001
def differences(expected,actual,path='$'):
    if isinstance(expected,bool) or expected is None or isinstance(expected,str):
        return [] if type(actual) is type(expected) and actual==expected else [path+': value/type differs']
    if type(expected) is int:
        return [] if type(actual) is int and actual==expected else [path+': integer differs']
    if isinstance(expected,float):
        good=type(actual) in (int,float) and math.isfinite(actual) and abs(actual-expected)<=FLOAT_TOLERANCE
        return [] if good else [path+': numeric value differs beyond 0.001']
    if isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected):return [path+': list type/length differs']
        return [error for i,(a,b) in enumerate(zip(expected,actual)) for error in differences(a,b,f'{path}[{i}]')]
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or set(actual)!=set(expected):return [path+': object fields differ']
        return [error for key,value in expected.items() for error in differences(value,actual[key],path+'.'+key)]
    raise TypeError('Unsupported expected value')
def compare(t0,target):
    pairs=[('T0',H/'reproduction/positive_control_T0.json',Path(t0)),('T1',H/'reproduction/scan_results.json',Path(target))]
    errors=[]
    for label,expected,actual in pairs:
        a=json.loads(expected.read_text(encoding='utf-8'));b=json.loads(actual.read_text(encoding='utf-8'))
        errors.extend(label+': '+error for error in differences(a,b))
    return errors
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--t0',required=True,type=Path);p.add_argument('--target',required=True,type=Path);args=p.parse_args()
    errors=compare(args.t0,args.target)
    if errors:
        for error in errors[:20]:print('FAIL:',error)
        if len(errors)>20:print('Further differences:',len(errors)-20)
        raise SystemExit(1)
    print('PASS: fresh T0/T1 fields, text/offset selections and scores agree with saved outputs (float tolerance 0.001). No expected files changed.')
