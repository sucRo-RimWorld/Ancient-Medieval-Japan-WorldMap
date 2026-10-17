#!/usr/bin/env python3
"""Build a bounded GSI DEMGM-derived research terrain table from an audited Japan land mask.

Does not publish or copy raw GSI tiles into Mod. Not a historical climate model;
no wetlands, rainfall, rivers, coasts or executable Worldbuilder preset inferred.
Only explicit --fetch allows external access; downloaded tiles are transient.
"""
import argparse
import csv
import io
import json
import math
import time
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

Z = 8
CAP = 120
MAX_BYTES = 512000
GSI = 'https://cyberjapandata.gsi.go.jp/xyz/demgm_png/{z}/{x}/{y}.png'
MASK_COLS = ('tile_id','globe_longitude','globe_latitude','gis_longitude','gis_latitude','is_land','island')
BIOME_WARM='AMJ_WarmTemperateForest'
BIOME_COOL='AMJ_CoolTemperateForest'
BIOME_SUB='AMJ_SubalpineForest'
BIOME_ALPINE='AMJ_AlpineZone'
BIOME_NAMES=(BIOME_WARM,BIOME_COOL,BIOME_SUB,BIOME_ALPINE)

def tile_position(lon, lat, zoom=Z):
    if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon < 180 and -85.05 < lat < 85.05):
        raise ValueError('Invalid longitude/latitude')
    n=2**zoom
    u=(lon+180)/360*n
    v=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
    x,y=math.floor(u),math.floor(v)
    return x,y,min(255,int((u-x)*256)),min(255,int((v-y)*256))

def decode_height(rgb):
    r,g,b=rgb[:3];v=(r<<16)|(g<<8)|b
    if v==8388608:return None
    return (v if v<8388608 else v-16777216)*0.01

# Exact monthly mean temperature normals (1991-2020), Jan..Dec in degrees C.
# JMA official station table: https://www.data.jma.go.jp/stats/en/normal/normal.html
# Nine main-table stations plus three official JMA monthly records in
# northern Honshu: Aomori (47575), Morioka (47584), Akita (47582).
# https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?block_no=47575&prec_no=31&view=a2
# https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?block_no=47584&prec_no=33&view=a2
# https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?block_no=47582&prec_no=32&view=a2
# These 12 stations (no Hokkaido/Ryukyu) are modern temperature anchors,
# not monthly observations at every world tile.
JMA_TEMP_STATIONS = (
    ('Aomori', 140.737, 40.822, (-0.9, -0.4, 2.8, 8.5, 13.7, 17.6, 21.8, 23.5, 19.9, 13.5, 7.2, 1.4)),
    ('Morioka', 141.154, 39.703, (-1.6, -0.9, 2.6, 8.7, 14.5, 18.8, 22.4, 23.5, 19.3, 12.6, 6.2, 0.8)),
    ('Akita', 140.102, 39.718, (0.4, 0.8, 4.0, 9.6, 15.2, 19.6, 23.4, 25.0, 21.0, 14.5, 8.3, 2.8)),
    ('Sendai', 140.872, 38.268, (2.0, 2.4, 5.5, 10.7, 15.6, 19.2, 22.9, 24.4, 21.2, 15.7, 9.8, 4.5)),
    ('Niigata', 139.023, 37.903, (2.5, 3.1, 6.2, 11.3, 16.7, 20.9, 24.9, 26.5, 22.5, 16.7, 10.5, 5.3)),
    ('Nagoya', 136.907, 35.182, (4.8, 5.5, 9.2, 14.6, 19.4, 23.0, 26.9, 28.2, 24.5, 18.6, 12.6, 7.2)),
    ('Tokyo', 139.692, 35.690, (5.4, 6.1, 9.4, 14.3, 18.8, 21.9, 25.7, 26.9, 23.3, 18.0, 12.5, 7.7)),
    ('Hiroshima', 132.459, 34.385, (5.4, 6.2, 9.5, 14.8, 19.6, 23.2, 27.2, 28.5, 24.7, 18.8, 12.9, 7.5)),
    ('Osaka', 135.502, 34.694, (6.2, 6.6, 9.9, 15.2, 20.1, 23.6, 27.7, 29.0, 25.2, 19.5, 13.8, 8.7)),
    ('Takamatsu', 134.043, 34.343, (5.9, 6.3, 9.4, 14.7, 19.8, 23.3, 27.5, 28.6, 24.7, 19.0, 13.2, 8.1)),
    ('Fukuoka', 130.402, 33.590, (6.9, 7.8, 10.8, 15.4, 19.9, 23.3, 27.4, 28.4, 24.7, 19.6, 14.2, 9.1)),
    ('Kagoshima', 130.558, 31.597, (8.7, 9.9, 12.8, 17.1, 21.0, 24.0, 28.1, 28.8, 26.3, 21.6, 16.2, 10.9)),
)
TEMPERATURE_LAPSE_C_PER_M = 0.00625

def climate_research(lon, lat, elevation_m):
    """Monthly JMA station IDW -> elevation-cooled monthly means -> Kira WI.

    WI=sum(max(month_mean-5, 0)) over 12 months, in degree-month.
    Interpolation has no geographic orographic/winter-continental correction.
    Missing DEM gets a separately flagged 1m *playable* elevation assumption.
    """
    if not all(math.isfinite(v) for v in (lon, lat, elevation_m)) or elevation_m < 0:
        raise ValueError('Invalid climate coordinates/elevation')
    nearby=[]
    for name, slon, slat, months in JMA_TEMP_STATIONS:
        dx=(lon-slon)*math.cos(math.radians((lat+slat)*0.5))
        dist2=dx*dx+(lat-slat)**2
        nearby.append((dist2, months))
    nearby.sort(key=lambda pair:pair[0])
    nearest=nearby[:4]
    if nearest[0][0]<1e-8:
        base=nearest[0][1]
    else:
        weights=[1.0/(dist2+0.0004) for dist2,_ in nearest]
        total=sum(weights)
        base=tuple(sum(w*m[i] for w,(_,m) in zip(weights,nearest))/total
                   for i in range(12))
    cooling=elevation_m*TEMPERATURE_LAPSE_C_PER_M
    months=tuple(t-cooling for t in base)
    annual_mean=max(-8.0,min(20.0,sum(months)/12))
    warmth_index=sum(max(t-5.0,0.0) for t in months)
    coldness_index=sum(min(t-5.0,0.0) for t in months)
    return annual_mean,warmth_index,coldness_index

def band(warmth_index,coldness_index):
    # Coldness-index eligibility is required for evergreen broad-leaved warm
    # forests. JMA vegetation review suggests CI about -10..-15 degree-month;
    # choose the conservative -10 provisional boundary, NOT a target quota.
    if warmth_index >= 85.0 and coldness_index >= -10.0:return BIOME_WARM
    if warmth_index >= 45.0:return BIOME_COOL
    if warmth_index >= 15.0:return BIOME_SUB
    return BIOME_ALPINE

# JMA station annual rainfall normals, 1991-2020 (mm), NOT medieval climate.
# Approximate observatory coordinates are used solely as interpolation anchors.
# Main source: https://www.data.jma.go.jp/stats/en/normal/normal.html
# Additional annual normals: Kanazawa 2401.5, Matsue 1791.9, Kochi 2666.4.
# Source: JMA official nml_sfc_ym (47605/47741/47893 respectively).
# No precipitation observations are copied or redistributed as a raster.
JMA_RAIN_STATIONS = (
    ('Sendai', 140.872, 38.268, 1276.7),
    ('Niigata', 139.023, 37.903, 1845.9),
    ('Kanazawa', 136.657, 36.562, 2401.5),
    ('Tokyo', 139.692, 35.690, 1598.2),
    ('Nagoya', 136.907, 35.182, 1578.9),
    ('Matsue', 133.051, 35.469, 1791.9),
    ('Osaka', 135.502, 34.694, 1338.3),
    ('Takamatsu', 134.043, 34.343, 1150.1),
    ('Hiroshima', 132.459, 34.385, 1572.2),
    ('Kochi', 133.532, 33.559, 2666.4),
    ('Fukuoka', 130.402, 33.590, 1686.9),
    ('Kagoshima', 130.558, 31.597, 2434.7),
)

def annual_rainfall_research(lon, lat):
    """Provisional four-nearest JMA-station interpolation, *not* gridded rainfall.

    Corrects random-world rainfall; no orographic, seasonal or medieval claims.
    The stations are modern observed anchors, but individual cells are estimates.
    """
    if not all(math.isfinite(v) for v in (lon, lat)):
        raise ValueError('Invalid coordinate for rainfall interpolation')
    weighted = []
    for name, slon, slat, rainfall in JMA_RAIN_STATIONS:
        dx = (lon-slon)*math.cos(math.radians((lat+slat)*0.5))
        dy = lat-slat
        dist2 = dx*dx+dy*dy
        if dist2 < 1e-8:
            return rainfall
        weighted.append((dist2, rainfall))
    weighted.sort(key=lambda pair: pair[0])
    closest = weighted[:4]
    weights = [1.0/(d2 + 0.0004) for d2, _ in closest]
    return sum(w*r for w, (_, r) in zip(weights, closest))/sum(weights)


def nearby_dem_estimate(image, px, py, max_pixel_radius=2):
    """Nearest valid *other* GSI DEMGM pixel, bounded to 2 pixels (~1 km).

    An estimated elevation, never an observed sample at the target coordinate.
    Negative pixels and unavailable DEM remain unresolved if no valid neighbor.
    """
    if image is None:
        return None
    best = None
    for radius in range(1, max_pixel_radius+1):
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                x, y = px+dx, py+dy
                if x < 0 or y < 0 or x > 255 or y > 255:
                    continue
                height = decode_height(image.getpixel((x,y)))
                if height is None or height < 0:
                    continue
                distance2 = dx*dx + dy*dy
                if best is None or (distance2, abs(height)) < (best[0], abs(best[1])):
                    best = (distance2, height, radius)
        if best is not None:
            return best[1], best[2]
    return None

def load_land(path):
    """Require exact ordered native mask shape, count every tile, retain land only."""
    land=[];count=0;sea=0;names=Counter();last=-1
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ())!=MASK_COLS:
            raise ValueError('Incorrect native-mask CSV schema')
        for row in reader:
            i=int(row['tile_id'])
            if i!=last+1:raise ValueError('Native tile IDs must be 0..N-1')
            last=i;count+=1
            if count>1000000:raise ValueError('World grid sample cap exceeded')
            if row['is_land']=='0':
                if row['island']:raise ValueError('Sea tagged with island')
                sea+=1;continue
            if row['is_land']!='1' or not row['island']:raise ValueError('Invalid land tag')
            lon=float(row['gis_longitude']);lat=float(row['gis_latitude'])
            x,y,px,py=tile_position(lon,lat)
            names[row['island']]+=1
            land.append((i,lon,lat,row['island'],x,y,px,py))
    if count==0 or not land:raise ValueError('Empty world mask')
    if len(names)!=13:raise ValueError('Expected precisely 13 included island polygons')
    return land,dict(world_tiles=count,land_tiles=len(land),sea_tiles=sea,islands=dict(names))

def decode_tile(blob):
    if len(blob)>MAX_BYTES or not blob.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('GSI original PNG missing/oversize')
    with Image.open(io.BytesIO(blob)) as im:
        if im.size!=(256,256):raise ValueError('Bad source PNG dimensions')
        return im.convert('RGB').copy()

def tile_images(needed, cache, allow_network, max_fetch, minimum_interval=0.35):
    if len(needed)>CAP or len(needed)>max_fetch:
        raise ValueError('Requested number of different GSI tiles exceeds safety cap')
    found={};hashes={};missing=[];downloads=0
    import hashlib
    last_fetch=None
    for x,y in sorted(needed):
        cached=Path(cache)/f'demgm_png_{Z}_{x}_{y}.png' if cache else None
        blob=cached.read_bytes() if cached and cached.is_file() else None
        if blob is None and allow_network:
            if last_fetch is not None:
                time.sleep(max(0,minimum_interval-(time.monotonic()-last_fetch)))
            last_fetch=time.monotonic()
            url=GSI.format(z=Z,x=x,y=y)
            req=Request(url,headers={'User-Agent':'AMJ-native-research/0.1 (bounded DEM provenance test)'})
            try:
                with urlopen(req,timeout=15) as resp:
                    if resp.status!=200:raise ValueError('Unexpected GSI HTTP status')
                    blob=resp.read(MAX_BYTES+1)
                downloads+=1
            except (OSError,ValueError):
                missing.append([x,y,'unavailable']);continue
        if blob is None:
            missing.append([x,y,'not_in_cache']);continue
        try:
            found[(x,y)]=decode_tile(blob)
        except (OSError,ValueError):
            missing.append([x,y,'invalid_png']);continue
        hashes[f'{x}/{y}']=hashlib.sha256(blob).hexdigest()
    return found,hashes,missing,downloads

# Independent, exact-point higher-resolution GSI DEM10B z12 observations.
# z8 comparison is diagnostic only: different resolution and source products.
ELEVATION_REFERENCE_POINTS = (
    ('Kyushu_lowland', 130.56, 31.60, 4.67),
    ('Northern_Honshu', 140.00, 39.00, 233.39),
    ('Japan_Alps', 137.60, 36.10, 1633.42),
    ('Fuji', 138.727, 35.360, 3740.44),
    ('Ariake_margin', 130.30, 32.87, 8.06),
    ('Oze', 139.25, 36.93, 1440.97),
)

def reference_resolution_qa(images):
    """Point-vs-point z8/z12 diagnostic; never use as a biome acceptance."""
    results = {}
    for name,lon,lat,reference in ELEVATION_REFERENCE_POINTS:
        x,y,px,py=tile_position(lon,lat)
        image=images.get((x,y))
        value=decode_height(image.getpixel((px,py))) if image else None
        if value is None:
            status='MISSING_Z8'
        elif value<0:
            status='NEGATIVE_Z8'
        else:
            status='COMPARE_ONLY'
        results[name]={
            'gis_longitude':lon,'gis_latitude':lat,
            'reference_dem10b_z12_m':reference,
            'sample_demgm_z8_m':value if status=='COMPARE_ONLY' else None,
            'z8_minus_reference_m':round(value-reference,2) if status=='COMPARE_ONLY' else None,
            'status':status,
        }
    return results

def build(mask, output, report, *, cache=None,fetch=False,max_tiles=CAP):
    points,summary=load_land(mask)
    tiles={(row[4],row[5]) for row in points}
    tiles.update(tile_position(lon,lat)[:2] for _,lon,lat,_ in ELEVATION_REFERENCE_POINTS)
    images,hashes,missing,downloads=tile_images(tiles,cache,fetch,max_tiles)
    stats=Counter();elevation=[];rainfall_values=[];warmth_values=[];coldness_values=[];no_data=0;model_estimated=0;unresolved=0
    missing_sources={(x,y):reason for x,y,reason in missing}
    gap_reasons=Counter();gap_samples=[]
    island_qa={name:{'land_tiles':total,'sampled_elevation_count':0,
                     'missing_elevation_count':0,'negative_gsi_land_conflict_count':0,
                     'proposed_biome_counts':{}} for name,total in sorted(summary['islands'].items())}
    with Path(output).open('w',newline='',encoding='utf-8') as out:
        wr=csv.writer(out)
        wr.writerow(('tile_id','gis_longitude','gis_latitude','island',
                     'elevation_m','annual_mean_c','proposed_biome','gsi_source','quality',
                     'annual_rainfall_mm','warmth_index','coldness_index'))
        for i,lon,lat,island,x,y,px,py in points:
            image=images.get((x,y))
            island_stat=island_qa[island]
            sampled=decode_height(image.getpixel((px,py))) if image else None
            original_gap = sampled is None or sampled < 0
            rainfall=annual_rainfall_research(lon,lat)
            rainfall_values.append(rainfall)
            h=sampled
            source='demgm_png_z8'
            quality='RESEARCH_ONLY'
            if original_gap:
                reason=('SOURCE_'+missing_sources[(x,y)].upper() if image is None else
                        'DEM_PIXEL_NO_DATA' if sampled is None else
                        'NEGATIVE_GSI_LAND_CONFLICT')
                gap_reasons[reason]+=1
                no_data+=1
                if reason=='NEGATIVE_GSI_LAND_CONFLICT':
                    island_stat['negative_gsi_land_conflict_count']+=1
                else:
                    island_stat['missing_elevation_count']+=1
                estimate=nearby_dem_estimate(image,px,py)
                if estimate is not None:
                    h,radius=estimate
                    source=f'demgm_png_z8_nearby_{radius}px'
                    quality='LOCAL_DEM_ESTIMATE'
                    model_estimated+=1
                else:
                    h=None
                    quality='NEGATIVE_GSI_LAND_CONFLICT' if sampled is not None else 'MISSING_ELEVATION'
                    unresolved+=1
                if len(gap_samples)<30:
                    gap_samples.append({'tile_id':i,'island':island,
                                        'gis_longitude':round(lon,7),
                                        'gis_latitude':round(lat,7),
                                        'reason':reason,'resolved_quality':quality,
                                        'next_step':'REVIEW_GSI_HIGH_RES_AND_COAST'})
            else:
                island_stat['sampled_elevation_count']+=1
                elevation.append(h)
            # No elevation observation: retain unknown provenance and the
            # existing 1m gameplay fallback. Do not silently treat it as DEM.
            t,wi,ci=climate_research(lon,lat,h if h is not None else 1.0)
            # Classify the SAME 0.001-degree-month indices that native
            # single-precision Worldbuilder producer validates/consumes.
            wi,ci=round(wi,3),round(ci,3)
            biome=band(wi,ci)
            warmth_values.append(wi)
            coldness_values.append(ci)
            stats[biome]+=1
            island_stat['proposed_biome_counts'][biome]=island_stat['proposed_biome_counts'].get(biome,0)+1
            wr.writerow((i,f'{lon:.7f}',f'{lat:.7f}',island,
                         f'{h:.2f}' if h is not None else '',
                         f'{t:.3f}',biome,source,quality,
                         f'{rainfall:.2f}',f'{wi:.3f}',f'{ci:.3f}'))
    for record in island_qa.values():
        record['coverage_percent']=round(100*record['sampled_elevation_count']/record['land_tiles'],3)
        assert (record['sampled_elevation_count']+record['missing_elevation_count']+
                record['negative_gsi_land_conflict_count']==record['land_tiles'])
    assert sum(r['sampled_elevation_count'] for r in island_qa.values())==len(elevation)
    assert sum(r['missing_elevation_count']+r['negative_gsi_land_conflict_count']
               for r in island_qa.values())==no_data
    qa={**summary,'island_dem_coverage':island_qa,'status':'COMPLETE_RESEARCH' if no_data==0 else 'PARTIAL_RESEARCH',
        'source':'GSI demgm_png z8 / Global Map DEM 2nd edition; modern data',
        'original_pngs_redistributed':False,'hist_wetland_inferred':False,
        'climate_model':'JMA 1991-2020 twelve-station monthly mean temperature, nearest-four IDW, altitude lapse .00625C/m; no historical correction',
        'temperature_monthly_observations_are_per_tile':False,
        'temperature_source':'https://www.data.jma.go.jp/stats/en/normal/normal.html',
        'temperature_northern_honshu_source':'https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php',
        'jma_station_monthly_temperature_c':{name:list(months) for name,lon,lat,months in JMA_TEMP_STATIONS},
        'biome_model':'Kira warmth index sum(max(T-5C,0)); CI=sum(min(T-5C,0)); warm forest also requires CI>=-10 (provisional)',
        'biome_warmth_index_c_month':[85.,45.,15.],
        'warm_temperate_coldness_index_min_c_month':-10.0,
        'modeled_warmth_index_range_c_month':[round(min(warmth_values),3),round(max(warmth_values),3)],
        'modeled_coldness_index_range_c_month':[round(min(coldness_values),3),round(max(coldness_values),3)],
        'missing_dem_biome_uses_playable_1m_fallback':True,
        'requested_source_tiles':len(tiles),'downloaded_source_tiles':downloads,
        'source_sha256_by_tile':hashes,'unavailable_source_tiles':missing,
        'invalid_or_no_data_land_tiles':no_data,'sampled_elevation_count':len(elevation),
        'gap_reason_counts':dict(gap_reasons),'gap_review_sample':gap_samples,
        'gap_sample_truncated':no_data>len(gap_samples),
        'gaps_resolved_by_interpolation':model_estimated,
        'unresolved_dem_land_tiles':unresolved,
        'modeled_dem_estimate_count':model_estimated,
        'rainfall_model':'JMA 1991-2020 annual station normals, nearest-four IDW (modern, no orographic correction)',
        'rainfall_observations_are_per_tile':False,
        'modeled_rainfall_range_mm':[round(min(rainfall_values),2),round(max(rainfall_values),2)],
        'modeled_rainfall_land_cells':len(rainfall_values),
        'rainfall_station_source':'https://www.data.jma.go.jp/stats/en/normal/normal.html',
        'jma_station_annual_normals_mm':{name:rain for name,lon,lat,rain in JMA_RAIN_STATIONS},
        'proposed_biome_counts':dict(stats),
        'national_coverage_percent':round(100*len(elevation)/len(points),3),
        'elevation_resolution_checkpoints':reference_resolution_qa(images),
        'elevation_resolution_checkpoints_acceptance':False,
        'sample_min_elevation_m':min(elevation) if elevation else None,
        'sample_max_elevation_m':max(elevation) if elevation else None,
        'not_rimworld_runtime_test':True,
        'not_approved_climate_or_ecology':True,
        'not_watercourse_or_wetland_data':True,
        'wetlands_inferred':False,
        'not_historic_dem':True}
    Path(report).write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return qa

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--land-mask',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    p.add_argument('--cache',type=Path)
    p.add_argument('--fetch',action='store_true')
    p.add_argument('--max-tiles',type=int,default=CAP)
    a=p.parse_args(argv)
    if not 1<=a.max_tiles<=CAP:raise ValueError('Unsafe tile request cap')
    qa=build(a.land_mask,a.output,a.report,cache=a.cache,fetch=a.fetch,max_tiles=a.max_tiles)
    shown={k:v for k,v in qa.items() if k not in ('source_sha256_by_tile','islands')}
    print(json.dumps(shown,ensure_ascii=False,indent=2))
    return 0 if qa['status']=='COMPLETE_RESEARCH' else 1

if __name__=='__main__':raise SystemExit(main())
