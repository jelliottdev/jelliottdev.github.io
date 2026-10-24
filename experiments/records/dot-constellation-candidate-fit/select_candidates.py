"""Prepare fixed catalogue candidates only. Never reads LP2 centroid coordinates."""
import csv,hashlib,importlib.metadata,json,math,sys
from pathlib import Path
import numpy as np
import astropy
from astropy import units as u
from astropy.coordinates import FK5,SkyCoord,get_constellation
from astropy.time import Time
from astropy.utils import iers
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def policy():
 p=HERE/'candidate-selection-plan.json';assert not p.exists()
 files=['inputs/cds-vizier-v50-all.tsv','inputs/cds-readme.html','inputs/constellation_data_roman87.dat','inputs/constellation_names.dat','inputs/astropy-v8.0.2-utils.py','inputs/astropy-license.rst','astropy-install-report.json','select_candidates.py']
 plan={'scope':'Star candidate input preparation only, frozen before candidate selection; no LP2 matching authorized','catalogue':'CDS V/50/catalog complete VizieR TSV. NASA retained as provenance mirror, not merged.','nonstellar':'Explicitly exclude HR92,95,182,1057,1841,2472,2496,3515,3671,6309,6515,7189,7539,8296, the14 nonstellar retained-number entries identified by catalogue documentation. Also exclude any missing/unparseable/nonfiniteJ2000RA/Dec orVmag; log every row.','photometry':'Source Vmag visual value, flags retained but not silently excluded; no magnitude epoch, variability selection or colour cut. Rank ascending (Vmag,integerHR), exactly5 perconstellation.','membership':'Astropy8.0.2 get_constellation(SkyCoord(FK5(equinox=J2000), catalogueJ2000positions),short_name=True); Roman1987 IAU boundaries with B1875precession insidepinnedlibrary. No manualBayer/Flamsteed suffix membership. Disable IERS downloads. No propermotion or epoch tuning.','duplicates':'Each distinctHR record retained, including binary/multiple components and coincident/nearcoincident coordinates. No angular merge, flux combination or handreplacement; record closepairs and flags so fivecataloguerecords is not represented as fiveunresolvedvisualsources.','projection':'One J2000gnomonic plane perselectedfive, centred on normalized unweighted mean ofJ2000unitvectors. East/north basis fromcentreRA/Dec; x=(v·east)/(v·centre),y=(v·north)/(v·centre). Stop before matching if centreundefined,anydenominator<=0,orzeroRMSradius. No centreoptimization.','validation':'Requireall88 official shortnames andatleast5 eligible rows each. Exact installedRoman/names files must match recoveredtaggedsource bytes. Candidate lists/projections are fixed inputs to later reviewedmatchingplan, not outcomes.','inputs':[{'path':name,'sha256':sha(HERE/name)} for name in files]}
 write(p,plan);print('Candidate policy frozen',sha(p))
def prepare():
 plan=json.loads((HERE/'candidate-selection-plan.json').read_text(encoding='utf-8'))
 amendment=json.loads((HERE/'candidate-selection-amendment.json').read_text())
 assert sha(HERE/'candidate-selection-plan.json')==amendment['original_plan_sha256']
 for item in plan['inputs']:
  if item['path']=='select_candidates.py':
   assert sha(HERE/'select_candidates-initial.py')==item['sha256']
   assert sha(HERE/item['path'])==amendment['updated_script_sha256']
  else:assert sha(HERE/item['path'])==item['sha256']
 assert astropy.__version__=='8.0.2';iers.conf.auto_download=False
 data=Path(astropy.__file__).parent/'coordinates/data'
 for name in ['constellation_data_roman87.dat','constellation_names.dat']:
  assert sha(data/name)==amendment['installed_data_sha256'][name]
  assert (data/name).read_bytes().replace(b'\r\n',b'\n')==(HERE/'inputs'/name).read_bytes().replace(b'\r\n',b'\n')
 text=(HERE/'inputs/cds-vizier-v50-all.tsv').read_text(encoding='utf-8');lines=[line for line in text.splitlines() if line.strip() and not line.startswith('#')];header=next(i for i,line in enumerate(lines) if line.startswith('recno\tHR\t'));reader=csv.DictReader(lines[header+3:],fieldnames=lines[header].split('\t'),delimiter='\t');rows=[];excluded=[];nonstellar={92,95,182,1057,1841,2472,2496,3515,3671,6309,6515,7189,7539,8296}
 for row in reader:
  hr=int(row['HR']);reason=None
  if hr in nonstellar:reason='documented_nonstellar_retained_number'
  else:
   try:
    ra=[float(x) for x in row['RAJ2000'].split()];dec=[float(x) for x in row['DEJ2000'].replace('+','').replace('-','').split()];assert len(ra)==len(dec)==3
    ra_deg=15*(ra[0]+ra[1]/60+ra[2]/3600);dec_deg=(dec[0]+dec[1]/60+dec[2]/3600)*(-1 if row['DEJ2000'].strip().startswith('-') else 1);mag=float(row['Vmag']);assert all(math.isfinite(x) for x in [ra_deg,dec_deg,mag]) and 0<=ra_deg<360 and -90<=dec_deg<=90
   except Exception:reason='missing_or_invalid_coordinate_or_magnitude'
  if reason:excluded.append({'HR':hr,'reason':reason});continue
  rows.append({'HR':hr,'name':row['Name'].strip(),'ra_j2000_deg':ra_deg,'dec_j2000_deg':dec_deg,'Vmag':mag,'n_Vmag':row['n_Vmag'].strip(),'u_Vmag':row['u_Vmag'].strip(),'multiple_flag':row['Multiple'].strip(),'ADS':row['ADS'].strip(),'ADS_component':row['ADScomp'].strip(),'multiple_components':row['MultCnt'].strip()})
 assert len(rows)+len(excluded)==9110 and len({r['HR'] for r in rows})==len(rows)
 coords=SkyCoord(ra=[r['ra_j2000_deg'] for r in rows]*u.deg,dec=[r['dec_j2000_deg'] for r in rows]*u.deg,frame=FK5(equinox=Time('J2000')))
 membership=get_constellation(coords,short_name=True);names={line[:3]:line[4:].strip() for line in (HERE/'inputs/constellation_names.dat').read_text(encoding='utf-8').splitlines() if line and not line.startswith('#')};groups={name:[] for name in names}
 for row,name in zip(rows,membership):row['constellation']=str(name);groups[str(name)].append(row)
 assert len(groups)==88 and min(map(len,groups.values()))>=5
 candidates=[];close=[]
 for name in sorted(groups):
  group=sorted(groups[name],key=lambda r:(r['Vmag'],r['HR']));stars=group[:5];ra=np.radians([r['ra_j2000_deg'] for r in stars]);dec=np.radians([r['dec_j2000_deg'] for r in stars]);vectors=np.column_stack([np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)]);centre=vectors.mean(axis=0);assert np.linalg.norm(centre)>1e-12;centre/=np.linalg.norm(centre);ra0=np.arctan2(centre[1],centre[0]);dec0=np.arcsin(centre[2]);east=np.array([-np.sin(ra0),np.cos(ra0),0]);north=np.array([-np.sin(dec0)*np.cos(ra0),-np.sin(dec0)*np.sin(ra0),np.cos(dec0)]);den=vectors@centre;assert np.all(den>0);plane=np.column_stack([(vectors@east)/den,(vectors@north)/den]);assert np.sum((plane-plane.mean(axis=0))**2)>0
  for i in range(5):
   for j in range(i):
    angle=math.degrees(math.atan2(float(np.linalg.norm(np.cross(vectors[i],vectors[j]))),float(vectors[i]@vectors[j])))*3600
    if angle<60:close.append({'constellation':name,'HRs':[stars[j]['HR'],stars[i]['HR']],'separation_arcsec':angle,'rule':'retained distinctHR entries; flag only, no merge'})
  candidates.append({'constellation':name,'name':names[name],'eligible_members':len(group),'stars':stars,'projection_centre_ra_deg':math.degrees(ra0)%360,'projection_centre_dec_deg':math.degrees(dec0),'gnomonic_xy':plane.tolist()})
 packages={name:importlib.metadata.version(name) for name in ['astropy','astropy-iers-data','numpy','packaging','pyerfa','PyYAML']}
 write(HERE/'catalogue-membership.json',rows);write(HERE/'constellation-candidates.json',candidates)
 write(HERE/'candidate-preparation-receipt.json',{'selection_plan_sha256':sha(HERE/'candidate-selection-plan.json'),'catalogue_sha256':sha(HERE/'inputs/cds-vizier-v50-all.tsv'),'rows':9110,'eligible':len(rows),'excluded':excluded,'constellations':88,'smallest_eligible_group':min(map(len,groups.values())),'selected_HR_count':440,'selected_close_pairs_under60arcsec':close,'runtime_packages':packages,'candidate_sha256':sha(HERE/'constellation-candidates.json'),'membership_sha256':sha(HERE/'catalogue-membership.json'),'target_dot_geometry_loaded':False,'geometry_matching_run':False})
 print('Prepared',len(rows),'eligible rows;',len(excluded),'excluded;88fixedfive-entrycandidates; no dotmatching')
 print('Named candidates',{r['name']:[s['HR'] for s in r['stars']] for r in candidates if r['constellation'] in ['Ori','Aql','Boo']});print('Close selected component pairs',close)
if __name__=='__main__':
 if sys.argv[1]=='freeze':policy()
 elif sys.argv[1]=='prepare':prepare()
 else:raise ValueError('freeze or prepare')
