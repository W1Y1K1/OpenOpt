"""Render an existing RC profile; adapted from OpenYield reduce_rc.py."""

def render(profile,name=None):
    if name is None:
        scope=profile.get('scope',{})
        name=f'CALIBRATED_OPENYIELD_{scope.get("rows",8)}X{scope.get("cols",8)}'
    lines=[f'.subckt {name} '+' '.join(profile['ports'])]
    lines.extend(' '.join(m) for m in profile['mos'])
    lines.extend(f'Rcal_{i} {a} {b} {r:.15g}' for i,(a,b,r) in enumerate(profile['resistors']))
    lines.extend(f'Ccal_{i} {a} {b} {c:.15g}' for i,(a,b,c) in enumerate(profile['capacitors']))
    lines.extend([f'.ends {name}',''])
    return '\n'.join(lines)
