"""Rigid assembly with rounded optical grid. Run with uv; all geometry in mm."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parent
P=200;W=875.8
parts=[]
def rect(w,h,r=0,cx=0,cy=0):
    if not r:return [[cx-w/2,cy-h/2],[cx+w/2,cy-h/2],[cx+w/2,cy+h/2],[cx-w/2,cy+h/2]]
    pts=[]
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for n in range(17):
            a=math.radians(start+n*90/16);pts.append([cx+x+r*math.cos(a),cy+y+r*math.sin(a)])
    return pts

def box(name,center,size,role,module=0,outline=None,holes=None):
    p=dict(name=name,center=center,size=size,role=role,module=module)
    if outline is not None:p.update(outline=outline,holes=holes or [])
    parts.append(p)
def ring(name,x,y,z,outer,inner,depth,role,module):
    t=(outer-inner)/2
    box(name+'_top',[x,y+(outer-t)/2,z],[outer,t,depth],role,module)
    box(name+'_bottom',[x,y-(outer-t)/2,z],[outer,t,depth],role,module)
    box(name+'_left',[x-(outer-t)/2,y,z],[t,inner,depth],role,module)
    box(name+'_right',[x+(outer-t)/2,y,z],[t,inner,depth],role,module)
box('Rigid_backing',[0,0,3],[W,W,6],'backing',0,rect(W,W,45))
box('Rigid_perimeter_frame',[0,0,18],[W,W,24],'structure',0,rect(W,W,45),[rect(W-24,W-24,33)])
for r in range(4):
    for c in range(4):
        i=r*4+c;x=-300+c*P;y=300-r*P
        ring(f'Node_{i+1:02d}_carrier',x,y,43,163.2,151.2,26,'carrier',1)
        box(f'Node_{i+1:02d}_panel',[x,y,69.6],[160,160,6],'panel',1)
        box(f'Node_{i+1:02d}_diffusion_face',[x,y,75.2],[160,160,.4],'pixel_face',1)
        ring(f'Node_{i+1:02d}_trim',x,y,74,162.4,160,3.2,'trim',1)
        box(f'Node_{i+1:02d}_controller_envelope',[x+23,y+5,49],[65,48,16],'controller',1)
        box(f'Node_{i+1:02d}_speaker_envelope',[x-43,y-17,43],[38,38,18],'speaker',1)
# One connected optical design, to be divided into printable tiles at manufacturing design.
# R2 aperture corners keep clearance around the square 160 mm panel and 162.4 mm trim.
outline=rect(835.8,835.8,35.8)
holes=[rect(164.2,164.2,2,-300+c*P,300-r*P) for r in range(4) for c in range(4)]
box('Rounded_channel_network',[0,0,62],[835.8,835.8,22],'channel_body',2,outline,holes)
box('Continuous_honeycomb_skin',[0,0,74.4],[835.8,835.8,2.8],'channel_skin',2,outline,holes)
# The remote is a separate part located beside the display for illustration, not attached.
box('LilyGo_handheld_envelope',[590,-430,120],[150,88,20],'console',3,rect(150,88,10))
box('LilyGo_display_envelope',[590,-430,130.2],[120,66,.5],'console_screen',3)
# Low rear enclosure and two painted timber feet: placement/stability study only.
box('PowerNex_ST303015_envelope',[0,-220,-105],[300,300,150],'power_enclosure',0,rect(300,300,4))
box('Power_enclosure_rear_door',[0,-220,-181],[296,296,2],'power_door',0,rect(296,296,3))
for x in [-280,280]:box('White_timber_foot_'+str(x),[x,-457.9,-70],[55,40,500],'timber_foot',0)
box('Rear_power_connection_envelope',[0,-320,-8],[45,28,16],'connector',0)
config=dict(status='Rigid appearance concept; NOT manufacturing geometry',revision=3,units='mm',pitch_mm=P,panel_mm=160,pixels_per_node=4096,opening_mm=164.2,clearance_mm=2.1,body_mm=[W,W,257.8],support_envelope_mm=[W,W+40,500],power_enclosure_mm=[300,300,150],support_status="Provisional feet and rear enclosure placement; no stability or mains construction validation",assembly='One rigid backing; no transport split',group_names=['Rigid_frame','Independent_nodes','Honeycomb_channels','Handheld_remote'],track_outer_corner_radius_mm=35.8,aperture_corner_radius_mm=2,backing_corner_radius_mm=45,handheld_remote=True,remote_center_mm=[590,-430,120],console_envelope_unverified=True,transport_body_depth_allowance_mm=105,geometry_note='Rounded custom channel envelope; purchased-mesh exact fit and print tile seams unverified. Honeycomb pattern is continuous in assembly coordinates.',parts=parts)
(ROOT/'assembly.json').write_text(json.dumps(config,indent=2))
back_area=(W/1000)**2-(4-math.pi)*(.045)**2
back_mass=back_area*.006*600
mass=dict(status='ILLUSTRATIVE allowances, not measured shipping weight',assumed_plywood_density_kg_m3=600,backing_kg=round(back_mass,3),hardware_per_node_kg=.35,hardware_16_nodes_kg=5.6,printed_parts_allowance_kg=2,frame_fasteners_allowance_kg=1.2,wiring_connectors_allowance_kg=.8,display_before_power_and_feet_example_kg=round(back_mass+9.6,2),timber_feet_allowance_kg=1.32,subtotal_excluding_power_assembly_kg=round(back_mass+10.92,2),separate_handheld_remote_allowance_kg=.3,subtotal_including_remote_excluding_power_assembly_kg=round(back_mass+11.22,2),excluded=['Rear steel enclosure, both supplies, mains components and mounting brackets: mass not yet supplied','Cases and foam','Stand or wall mounting','Tools and spares'],note='All allowances require weighing; battery/enclosure mass is not verified. Rounded backing area uses ideal analytic arcs, CAD samples those arcs.')
(ROOT/'mass-budget.json').write_text(json.dumps(mass,indent=2))
print(json.dumps({'parts':len(parts),'rigid_body_mm':W,'mass_example_kg':mass['subtotal_excluding_power_assembly_kg']}))
