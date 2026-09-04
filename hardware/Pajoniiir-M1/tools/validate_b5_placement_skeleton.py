#!/usr/bin/env python3
from __future__ import annotations
import json, math, sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
B5=BASE/'m1_mech_b5_placement_skeleton.json'
B4=BASE/'m1_mech_b4_panel_windows.json'
GATES=BASE/'mechanical_gates.json'
USB=BASE/'libraries'/'footprints.pretty'/'Amphenol_87520-1010ALF.kicad_mod'
RCA=BASE/'libraries'/'footprints.pretty'/'Kycon_KLPX-0848A-2-x-G.kicad_mod'

def close(a,b,t=1e-6): return isinstance(a,(int,float)) and math.isclose(float(a),b,abs_tol=t)
def main():
    errors=[]
    b5=json.loads(B5.read_text()); b4=json.loads(B4.read_text()); gates=json.loads(GATES.read_text())
    if b5.get('milestone')!='M1-MECH-B5': errors.append('B5 milestone missing')
    core=b5.get('core_board_mm',{})
    if not close(core.get('width'),104) or not close(core.get('height'),62): errors.append('B5 core drift')
    expected={
      'J2':(19.51,3.90,180,(8.21,23.81,-9.65,6.80)),
      'J3':(51.21,3.90,180,(39.91,55.51,-9.65,6.80)),
      'J4':(70.31,1.75,90,(64.71,75.91,-12.35,8.35)),
      'J5':(82.51,1.75,90,(76.91,88.11,-12.35,8.35)),
    }
    byref={p['refdes']:p for p in b5.get('top_wall_candidate_anchors',[])}
    for ref,(x,y,rot,box) in expected.items():
        p=byref.get(ref,{})
        a=p.get('anchor_mm',{}); c=p.get('transformed_courtyard_mm',{})
        obs=(c.get('x_min'),c.get('x_max'),c.get('y_min'),c.get('y_max'))
        if not(close(a.get('x'),x) and close(a.get('y'),y) and p.get('rotation_deg')==rot): errors.append(f'{ref} anchor drift')
        if not all(close(v,e) for v,e in zip(obs,box)): errors.append(f'{ref} courtyard drift {obs}')
    win=b4['primary_long_io_wall']
    uw=win['USB_HOST_PAIR_window_local_x_mm']; rw=win['RCA_MAIN_PAIR_window_local_x_mm']
    for ref in ('J2','J3'):
        c=byref[ref]['transformed_courtyard_mm']
        if c['x_min']<uw['min']-1e-6 or c['x_max']>uw['max']+1e-6: errors.append(f'{ref} outside USB window')
    for ref in ('J4','J5'):
        c=byref[ref]['transformed_courtyard_mm']
        if c['x_min']<rw['min']-1e-6 or c['x_max']>rw['max']+1e-6: errors.append(f'{ref} outside RCA window')
    s=b5['top_wall_screen_results']
    if not close(s.get('J3_to_upper_left_mount_center_x_clearance_mm'),5.301): errors.append('UL screw clearance drift')
    if not close(s.get('J5_to_upper_right_mount_center_x_clearance_mm'),4.499): errors.append('UR screw clearance drift')
    if not close(s.get('maximum_outboard_courtyard_overhang_from_core_top_edge_mm'),12.35): errors.append('top overhang drift')
    if '87520-1010ALF' not in USB.read_text(): errors.append('Amphenol footprint missing')
    if 'KLPX-0848A' not in RCA.read_text(): errors.append('Kycon footprint missing')
    byid={g.get('id'):g for g in gates.get('gates',[])}
    for gid in ('J2_USB0','J3_USB1','J4_RCA_L','J5_RCA_R'):
        if byid.get(gid,{}).get('allow_blank_footprint') is not False: errors.append(f'{gid} still blank-enabled')
    if byid.get('J1_POWER_INPUT',{}).get('allow_blank_footprint') is not True: errors.append('J1 must remain fail-closed blank gate')
    freeze=b5.get('freeze',{})
    if any(freeze.get(k) is not False for k in ('top_wall_component_anchors_are_production_xy','right_wall_absolute_anchors_locked','left_wall_absolute_anchor_locked','final_board_outline_locked','edge_cuts_allowed','layout_freeze_allowed')):
        errors.append('B5 incorrectly promoted to final/freeze')
    print('Pajoniiir-M1 M1-MECH-B5 placement skeleton validation')
    print('  top anchors: J2/J3 USB + J4/J5 RCA')
    print('  blank footprint hard gates expected: J1 + C3 + C8')
    print('  final Edge.Cuts/layout freeze: blocked')
    if errors:
        for e in errors: print('ERROR:',e,file=sys.stderr)
        return 1
    print('PASS: B5 placement skeleton is internally consistent and fail-closed.')
    return 0
if __name__=='__main__': raise SystemExit(main())
