#!/usr/bin/env python3
"""Synthetic bitmap and land-mask regressions; no GSI calls and no native PASS."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from PIL import Image

spec=importlib.util.spec_from_file_location('terrain',Path(__file__).with_name('BuildJapanRegionalTerrain.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def pixel_height(h):
    v=(round(h*100) if h>=0 else 16777216+round(h*100))
    return ((v>>16)&255,(v>>8)&255,v&255)

NAMES=('Honshu','Shikoku','Kyushu','Sado','Awaji','Oki','Tsushima_North',
       'Tsushima_South','Iki','Amakusa_1','Amakusa_2','Shodoshima','SuoOshima')

class Tests(unittest.TestCase):
    def test_jma_annual_rainfall_and_dem_estimate(self):
        # Station value exact; regional interpolation bounded by the observed normals.
        self.assertAlmostEqual(m.annual_rainfall_research(130.558,31.597),2434.7)
        self.assertAlmostEqual(m.annual_rainfall_research(134.043,34.343),1150.1)
        values=[x[3] for x in m.JMA_RAIN_STATIONS]
        for lon,lat in ((130.4,32.9),(135.5,35.5),(140.2,40.5)):
            self.assertGreaterEqual(m.annual_rainfall_research(lon,lat),min(values))
            self.assertLessEqual(m.annual_rainfall_research(lon,lat),max(values))
        with self.assertRaises(ValueError):
            m.annual_rainfall_research(float('nan'),35)
        img=Image.new('RGB',(256,256),(128,0,0))
        img.putpixel((101,100),pixel_height(523.45))
        self.assertEqual(m.nearby_dem_estimate(img,100,100),(523.45,1))
        self.assertIsNone(m.nearby_dem_estimate(img,150,150))

    def test_dem_encoding(self):
        for h in (0,1.23,1633.42,3740.44,-12.34):
            self.assertAlmostEqual(m.decode_height(pixel_height(h)),h,places=2)
        self.assertIsNone(m.decode_height((128,0,0)))

    def test_geolocation_and_band_edges(self):
        self.assertEqual(m.tile_position(135.5,36)[0:2],(224,100))
        for wi,ci,expected in ((85,-10,m.BIOME_WARM),
                               (85,-10.001,m.BIOME_COOL),
                               (84.999,0,m.BIOME_COOL),
                               (45,-30,m.BIOME_COOL),
                               (44.999,0,m.BIOME_SUB),
                               (15,-100,m.BIOME_SUB),
                               (14.999,0,m.BIOME_ALPINE)):
            self.assertEqual(m.band(wi,ci),expected)
        # These exactly match the JMA 1991-2020 station normals.
        self.assertAlmostEqual(m.climate_research(140.737,40.822,0)[1],85.7)
        self.assertAlmostEqual(m.climate_research(141.154,39.703,0)[1],86.0)
        # Northern Honshu's cool-forest winter condition is not captured by
        # warmth index alone.
        _,north_wi,north_ci=m.climate_research(140.737,40.822,0)
        self.assertAlmostEqual(north_ci,-17.1)
        self.assertEqual(m.band(north_wi,north_ci),m.BIOME_COOL)
        annual,wi,ci=m.climate_research(140.872,38.268,0)
        self.assertAlmostEqual(annual,12.825,places=3)
        self.assertAlmostEqual(wi,100.0)
        self.assertAlmostEqual(ci,-6.1)
        annual,wi,ci=m.climate_research(130.558,31.597,0)
        self.assertAlmostEqual(wi,165.4)
        base=m.climate_research(135.5,36,0)
        high=m.climate_research(135.5,36,1000)
        self.assertAlmostEqual(base[0]-high[0],6.25)
        self.assertLess(high[1],base[1])
        self.assertEqual(m.band(*m.climate_research(140.872,38.268,0)[1:]),
                         m.BIOME_WARM)
        with self.assertRaises(ValueError):
            m.climate_research(140.872,38.268,float('nan'))
        with self.assertRaises(ValueError):m.tile_position(float('nan'),35)

    def fixture(self,path):
        with path.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(m.MASK_COLS)
            for i,name in enumerate(NAMES):
                w.writerow((i,'0','0',str(135.48+i*.002),'36','1',name))
            w.writerow((13,'0','0','135','36','0',''))

    def test_fixture_and_cache(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);mask=d/'mask.csv';self.fixture(mask)
            land,s=m.load_land(mask);self.assertEqual(s['land_tiles'],13)
            pos=(land[0][4],land[0][5])
            self.assertEqual({(x[4],x[5]) for x in land},{pos})
            cache=d/'cache';cache.mkdir()
            Image.new('RGB',(256,256),pixel_height(1000)).save(
                cache/f'demgm_png_{m.Z}_{pos[0]}_{pos[1]}.png')
            r=m.build(mask,d/'out.csv',d/'report.json',cache=cache)
            self.assertEqual(r['status'],'COMPLETE_RESEARCH')
            self.assertEqual(r['sampled_elevation_count'],13)
            self.assertEqual(r['invalid_or_no_data_land_tiles'],0)
            self.assertEqual(sum(r['proposed_biome_counts'].values()),13)
            self.assertEqual(r['national_coverage_percent'],100.)
            self.assertEqual(len(r['island_dem_coverage']),13)
            for name in NAMES:
                record=r['island_dem_coverage'][name]
                self.assertEqual(record['land_tiles'],1)
                self.assertEqual(record['sampled_elevation_count'],1)
                self.assertEqual(record['coverage_percent'],100.)
                self.assertEqual(sum(record['proposed_biome_counts'].values()),1)
            with (d/'out.csv').open() as f: rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),13)
            self.assertTrue(all(x['elevation_m']=='1000.00' for x in rows))
            self.assertTrue(all(x['quality']=='RESEARCH_ONLY' for x in rows))
            self.assertTrue(all('annual_rainfall_mm' in x for x in rows))
            self.assertTrue(all(1000 < float(x['annual_rainfall_mm']) < 3000 for x in rows))
            self.assertTrue(all(float(x['warmth_index']) >= 0 for x in rows))
            self.assertTrue(all(float(x['coldness_index']) <= 0 for x in rows))
            self.assertEqual(r['biome_warmth_index_c_month'],[85.,45.,15.])
            self.assertEqual(r['warm_temperate_coldness_index_min_c_month'],-10.0)
            self.assertFalse(r['temperature_monthly_observations_are_per_tile'])
            self.assertFalse(r['rainfall_observations_are_per_tile'])

    def test_missing_data_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);mask=d/'mask.csv';self.fixture(mask)
            r=m.build(mask,d/'out.csv',d/'report.json')
            self.assertEqual(r['status'],'PARTIAL_RESEARCH')
            self.assertEqual(r['invalid_or_no_data_land_tiles'],13)
            self.assertEqual(r['requested_source_tiles'],len({m.tile_position(135.48,36)[:2]} | {m.tile_position(lon,lat)[:2] for _,lon,lat,_ in m.ELEVATION_REFERENCE_POINTS}))
            self.assertEqual(r['national_coverage_percent'],0.)
            self.assertEqual(r['gap_reason_counts']['SOURCE_NOT_IN_CACHE'],13)
            self.assertEqual(r['gaps_resolved_by_interpolation'],0)
            self.assertEqual(r['island_dem_coverage']['Honshu']['missing_elevation_count'],1)
            self.assertEqual(r['island_dem_coverage']['Honshu']['coverage_percent'],0.)
            self.assertEqual(sum(r['proposed_biome_counts'].values()),13)
            self.assertTrue(r['missing_dem_biome_uses_playable_1m_fallback'])
            with (d/'out.csv').open() as f:
                row=next(csv.DictReader(f))
            self.assertEqual(row['elevation_m'],'')
            self.assertEqual(row['quality'],'MISSING_ELEVATION')
            self.assertTrue(row['proposed_biome'])
            self.assertTrue(float(row['warmth_index']) >= 0)

    def test_no_data_and_negative_height_not_fabricated(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);mask=d/'mask.csv';self.fixture(mask)
            x,y,px,py=m.tile_position(135.48,36)
            cache=d/'cache';cache.mkdir()
            img=Image.new('RGB',(256,256),pixel_height(0))
            img.putpixel((px,py),(128,0,0))
            name=cache/f'demgm_png_{m.Z}_{x}_{y}.png'
            img.save(name)
            qa=m.build(mask,d/'out.csv',d/'r.json',cache=cache)
            self.assertEqual(qa['status'],'PARTIAL_RESEARCH')
            self.assertEqual(qa['island_dem_coverage']['Honshu']['missing_elevation_count'],1)
            self.assertEqual(qa['gap_reason_counts']['DEM_PIXEL_NO_DATA'],2)
            img.putpixel((px,py),pixel_height(-12));img.save(name)
            qa=m.build(mask,d/'out.csv',d/'r.json',cache=cache)
            self.assertEqual(qa['status'],'PARTIAL_RESEARCH')
            self.assertEqual(qa['island_dem_coverage']['Honshu']['negative_gsi_land_conflict_count'],1)
            self.assertEqual(qa['gap_reason_counts']['NEGATIVE_GSI_LAND_CONFLICT'],2)

    def test_exact_coordinate_high_resolution_reference_diagnostics(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);mask=d/'mask.csv';self.fixture(mask)
            coords={(m.tile_position(lon,lat)[0:2]) for _,lon,lat,_ in m.ELEVATION_REFERENCE_POINTS}
            coords.add(m.tile_position(135.48,36)[:2])
            cache=d/'cache';cache.mkdir()
            for x,y in coords:
                Image.new('RGB',(256,256),pixel_height(100)).save(
                    cache/f'demgm_png_{m.Z}_{x}_{y}.png')
            r=m.build(mask,d/'out.csv',d/'report.json',cache=cache)
            self.assertEqual(len(r['elevation_resolution_checkpoints']),6)
            self.assertFalse(r['elevation_resolution_checkpoints_acceptance'])
            fuji=r['elevation_resolution_checkpoints']['Fuji']
            self.assertEqual(fuji['status'],'COMPARE_ONLY')
            self.assertEqual(fuji['sample_demgm_z8_m'],100)
            self.assertAlmostEqual(fuji['z8_minus_reference_m'],100-3740.44)
            self.assertEqual(r['sampled_elevation_count'],13)
            self.assertEqual(r['status'],'COMPLETE_RESEARCH')
            self.assertEqual(r['requested_source_tiles'],len(coords))
            r2=m.build(mask,d/'out2.csv',d/'report2.json')
            self.assertEqual(r2['elevation_resolution_checkpoints']['Fuji']['status'],'MISSING_Z8')

    def test_mask_validation_and_tile_limit(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'mask.csv';self.fixture(p)
            p.write_text(p.read_text().replace('1,0,0,','11,0,0,',1))
            with self.assertRaises(ValueError):m.load_land(p)
            with self.assertRaises(ValueError):
                m.tile_images({(i,100) for i in range(121)},None,False,120)

if __name__=='__main__':unittest.main(verbosity=2)
