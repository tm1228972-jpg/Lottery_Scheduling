#!/usr/bin/env python3
"""Generate exercise-specific diagrams, charts, and Gantt-style timelines."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
COL = {'navy':'#183153','blue':'#3977B9','cyan':'#43A6B6','orange':'#E69A3A','green':'#42966C','red':'#C45D5D','gray':'#65758B','light':'#EAF0F6','pale':'#F7F9FC','white':'#FFFFFF','purple':'#8B75B5'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titleweight':'bold','axes.titlesize':14,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})

def out(ex, name):
    p=ROOT/ex/'visuals'/name
    p.parent.mkdir(parents=True,exist_ok=True)
    return p

def finish(fig, path):
    fig.tight_layout(pad=1.7)
    fig.savefig(path,dpi=170,bbox_inches='tight')
    plt.close(fig)

def box(ax, xy, w, h, title, body, color):
    x,y=xy
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.03,rounding_size=0.08',facecolor=color,edgecolor=COL['navy'],linewidth=1.1)
    ax.add_patch(p)
    ax.text(x+w/2,y+h*.66,title,ha='center',va='center',weight='bold',color=COL['navy'],fontsize=10)
    ax.text(x+w/2,y+h*.31,body,ha='center',va='center',color=COL['gray'],fontsize=8.5,wrap=True)

def arrow(ax,a,b,label=None):
    ar=FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,color=COL['gray'],linewidth=1.4)
    ax.add_patch(ar)
    if label: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.09,label,ha='center',fontsize=8,color=COL['gray'])

def flow_image(ex, name, title, nodes, edges):
    fig,ax=plt.subplots(figsize=(11,4.5)); ax.set_xlim(0,12); ax.set_ylim(0,4.5); ax.axis('off'); ax.set_title(title,pad=16,color=COL['navy'])
    for n in nodes: box(ax,(n[0],n[1]),n[2],n[3],n[4],n[5],n[6])
    for a,b,l in edges: arrow(ax,a,b,l)
    finish(fig,out(ex,name))

def gantt_image(ex,name,title,lanes,subtitle):
    fig,ax=plt.subplots(figsize=(11,4.6))
    palette=[COL['blue'],COL['cyan'],COL['orange'],COL['green'],COL['purple'],COL['red']]
    for yi,(label,segments) in enumerate(lanes):
        ax.broken_barh(segments,(yi-.32,.64),facecolors=[palette[yi%len(palette)]],edgecolors='white',linewidth=1)
    ax.set_yticks(range(len(lanes)),[x[0] for x in lanes]); ax.set_xlabel('Ordered allocation slots / illustrative time units')
    ax.set_title(title,color=COL['navy'],pad=14); ax.grid(axis='x',color='#E5EAF0',linewidth=.8); ax.set_axisbelow(True)
    ax.spines[['top','right','left']].set_visible(False); ax.text(.01,-.22,subtitle,transform=ax.transAxes,fontsize=8,color=COL['gray'])
    finish(fig,out(ex,name))

def metric_chart(ex,name,title,labels,values,colors=None,ylabel=''):
    fig,ax=plt.subplots(figsize=(10.5,4.3)); palette=colors or [COL['blue'],COL['cyan'],COL['orange'],COL['green'],COL['purple']]
    bars=ax.bar(labels,values,color=[palette[i%len(palette)] for i in range(len(values))],width=.62)
    ax.set_title(title,color=COL['navy'],pad=14); ax.set_ylabel(ylabel); ax.grid(axis='y',color='#E5EAF0'); ax.set_axisbelow(True)
    for b,v in zip(bars,values): ax.text(b.get_x()+b.get_width()/2,b.get_height(),f'{v:.3g}',ha='center',va='bottom',fontsize=9,color=COL['navy'])
    ax.spines[['top','right']].set_visible(False); finish(fig,out(ex,name))

def ring_image(ex,name):
    fig,ax=plt.subplots(figsize=(8.2,6.2)); ax.set_aspect('equal'); ax.axis('off'); ax.set_title('Five philosophers and five exclusive forks',color=COL['navy'],pad=12)
    import math
    R=2.15; center=(0,0)
    points=[]
    for i in range(5):
        ang=math.pi/2-2*math.pi*i/5; x,y=R*math.cos(ang),R*math.sin(ang); points.append((x,y))
        ax.add_patch(Circle((x,y),.37,facecolor=COL['light'],edgecolor=COL['blue'],lw=2)); ax.text(x,y,f'P{i}',ha='center',va='center',weight='bold',color=COL['navy'])
    for i in range(5):
        x1,y1=points[i]; x2,y2=points[(i+1)%5]; mx,my=(x1+x2)/2,(y1+y2)/2
        # Fork nodes offset toward the centre so each fork is visibly shared by neighbours.
        mx,my=mx*.72,my*.72
        ax.add_patch(Rectangle((mx-.14,my-.14),.28,.28,facecolor=COL['orange'],edgecolor='#9C6428',lw=1.1)); ax.text(mx,my,f'F{i}',ha='center',va='center',fontsize=8,weight='bold',color='white')
    ax.text(0,0,'2 adjacent\nforks required',ha='center',va='center',fontsize=11,weight='bold',color=COL['gray'])
    ax.set_xlim(-3,3); ax.set_ylim(-2.8,2.8); finish(fig,out(ex,name))

def cycle_image(ex,name):
    fig,ax=plt.subplots(figsize=(8.5,5.8)); ax.set_aspect('equal'); ax.axis('off'); ax.set_title('Circular-wait witness: each philosopher holds one fork',color=COL['navy'],pad=15)
    import math
    pts=[]
    for i in range(5):
        a=math.pi/2-2*math.pi*i/5; x,y=1.8*math.cos(a),1.8*math.sin(a); pts.append((x,y))
        ax.add_patch(Circle((x,y),.34,facecolor=COL['pale'],edgecolor=COL['red'],lw=2)); ax.text(x,y,f'P{i}',ha='center',va='center',weight='bold',color=COL['navy'])
    for i in range(5):
        a,b=pts[i],pts[(i+1)%5]
        ax.add_patch(FancyArrowPatch(a,b,connectionstyle='arc3,rad=-.22',arrowstyle='-|>',mutation_scale=16,color=COL['red'],lw=2,shrinkA=24,shrinkB=24))
    ax.text(0,0,'WAIT-FOR\nCYCLE',ha='center',va='center',fontsize=13,weight='bold',color=COL['red'])
    ax.text(0,-2.35,'Pᵢ waits for the resource held by Pᵢ₊₁ (mod 5)',ha='center',color=COL['gray'],fontsize=9)
    ax.set_xlim(-2.7,2.7); ax.set_ylim(-2.7,2.7); finish(fig,out(ex,name))

def main():
    # Exercise 4: a synchronization interleaving as a Gantt-style protocol timeline.
    ex='exercise-4-dekker-peterson-semaphores-monitors'
    gantt_image(ex,'gantt_synchronization_interleaving.png','Protected counter: serialized critical-section entries',[
        ('Thread A',[(0,1.5),(3,1.5),(6,1.5)]),('Thread B',[(1.5,1.5),(4.5,1.5),(7.5,1.5)])],
        'Schematic safe interleaving: at most one thread occupies the critical section at a time.')

    # Exercise 5: a weighted lottery lock.
    ex='exercise-5-lottery-scheduling-synchronization-demo'
    flow_image(ex,'fig_lock_architecture.png','Weighted lottery lock: request to protected update',[
        (.4,1.8,2.1,1.1,'REQUEST','Thread joins waiter set',COL['light']),
        (3.25,1.8,2.1,1.1,'DRAW','Eligible tickets are sampled', '#E7F4F5'),
        (6.1,1.8,2.1,1.1,'OWNERSHIP','One winner owns the lock', '#FFF1DE'),
        (8.95,1.8,2.1,1.1,'CRITICAL','Update shared counter', '#E8F4EC')],
        [((2.55,2.35),(3.2,2.35),None),((5.4,2.35),(6.05,2.35),None),((8.25,2.35),(8.9,2.35),None)])
    p=ROOT/ex/'output'/'lottery_sync_results.json'; data=json.loads(p.read_text())
    labels=['P1 (5 tickets)','P2 (3 tickets)','P3 (2 tickets)']
    vals=[data['observed_shares'][k]*100 for k in ['P1','P2','P3']]
    targets=[data['expected_shares'][k]*100 for k in ['P1','P2','P3']]
    fig,ax=plt.subplots(figsize=(10.5,4.4)); y=range(3)
    ax.barh([v+.18 for v in y],targets,height=.33,label='Expected',color=COL['light'])
    ax.barh([v-.18 for v in y],vals,height=.33,label='Observed',color=[COL['blue'],COL['cyan'],COL['orange']])
    ax.set_yticks(list(y),labels); ax.set_xlim(0,60); ax.set_xlabel('Share of grants (%)'); ax.set_title('Weighted lock: observed grants versus ticket target',color=COL['navy'],pad=14)
    ax.grid(axis='x',color='#E5EAF0'); ax.legend(frameon=False,ncol=2,loc='lower right'); ax.spines[['top','right','left']].set_visible(False)
    finish(fig,out(ex,'chart_lock_shares.png'))
    trace=json.loads((ROOT/ex/'output'/'lottery_sync_trace.json').read_text())
    seq=[x['process'] for x in trace[:30]]
    lanes=[]
    for proc in ['P1','P2','P3']:
        seg=[(i,1) for i,v in enumerate(seq) if v==proc]
        lanes.append((proc,seg))
    gantt_image(ex,'gantt_lock_grants.png','Observed lock ownership over the first 30 decisions',lanes,
        'Each cell is one granted critical-section entry from the seeded trace; it is not elapsed wall-clock time.')
    metric_chart(ex,'chart_mutual_exclusion.png','Critical-section safety evidence', ['Max concurrent sections','Recorded errors'],[data['max_simultaneous_critical_sections'],len(data['errors'])],[COL['green'],COL['red']], 'Count')

    # Exercise 6: research / lottery against stride.
    ex='exercise-6-research-paper-and-seminar'
    flow_image(ex,'fig_lottery_stride_pipeline.png','Two allocation policies, one controlled workload',[
        (.5,1.9,2.2,1.05,'WORKLOAD','5 : 3 : 2 tickets',COL['light']),
        (3.55,2.8,2.2,1.05,'LOTTERY','Repeated random draws','#E7F4F5'),
        (3.55,.9,2.2,1.05,'STRIDE','Virtual pass minimum','#FFF1DE'),
        (7.0,1.9,2.2,1.05,'METRICS','Share error / variation','#E8F4EC'),
        (10.0,1.9,1.55,1.05,'REVIEW','Scope & limits','#F0ECF8')],
        [((2.75,2.45),(3.5,3.3),None),((2.75,2.4),(3.5,1.45),None),((5.8,3.3),(6.95,2.55),None),((5.8,1.45),(6.95,2.35),None),((9.25,2.45),(9.95,2.45),None)])
    result=json.loads((ROOT/ex/'output'/'scheduler_comparison.json').read_text())
    metric_chart(ex,'chart_lottery_stride_error.png','Maximum absolute share error',
        ['Lottery mean','Lottery worst seed','Stride'],
        [result['lottery']['mean_max_absolute_share_error']*100,result['lottery']['worst_max_absolute_share_error']*100,result['stride']['max_absolute_share_error']*100],
        [COL['blue'],COL['orange'],COL['green']],'Error (percentage points)')
    gantt_image(ex,'gantt_experiment_plan.png','Experiment pipeline and parallel policy runs',[
        ('Configure workload',[(0,1)]),('Lottery seeds',[(1,3)]),('Stride baseline',[(1,3)]),('Aggregate / review',[(4,1)])],
        'Ordered experiment stages; the lottery and stride runs share the same workload definition.')
    # sequence examples from same policy implementations
    def sequences(policy):
        if policy=='lottery':
            import random
            rng=random.Random(7); t=result['workload']['tickets']; names=list(t); total=sum(t.values()); seq=[]
            for _ in range(24):
                d=rng.randint(1,total); s=0
                for n in names:
                    s+=t[n]
                    if d<=s: seq.append(n); break
            return seq
        t=result['workload']['tickets']; stride={k:1_000_000/v for k,v in t.items()}; passes={k:0 for k in t}; seq=[]
        for _ in range(24):
            win=min(t,key=lambda n:(passes[n],list(t).index(n))); seq.append(win); passes[win]+=stride[win]
        return seq
    seq_l,seq_s=sequences('lottery'),sequences('stride')
    lanes=[]
    for proc in ['P1','P2','P3']:
        lanes.append((f'Lottery {proc}',[(i,1) for i,v in enumerate(seq_l) if v==proc]))
    for proc in ['P1','P2','P3']:
        lanes.append((f'Stride {proc}',[(i,1) for i,v in enumerate(seq_s) if v==proc]))
    gantt_image(ex,'gantt_policy_sequences.png','Illustrative first 24 allocation slots: lottery and stride',lanes,
        'Reproducible example using seed 7; stride uses the experiment tie-break. One block = one allocation quantum.')

    # Exercise 7: readers-writers policy trade-offs.
    ex='exercise-7-readers-writers-comparison'
    flow_image(ex,'fig_readers_writers_admission.png','Readers-writers admission and compatibility rules',[
        (.5,1.75,2.4,1.1,'REQUEST','Reader or writer arrives',COL['light']),
        (3.65,1.75,2.4,1.1,'POLICY','Preference / fair queue', '#E7F4F5'),
        (6.8,2.6,2.2,1.0,'READ','Readers may overlap','#E8F4EC'),
        (6.8,.9,2.2,1.0,'WRITE','Writer is exclusive','#FFF1DE'),
        (9.8,1.75,1.7,1.1,'RELEASE','Wake compatible waiters','#F0ECF8')],
        [((2.9,2.3),(3.6,2.3),None),((6.05,2.3),(6.72,3.1),'reader'),((6.05,2.25),(6.72,1.45),'writer'),((9.05,3.1),(9.75,2.55),None),((9.05,1.4),(9.75,2.0),None)])
    rw=json.loads((ROOT/ex/'output'/'readers_writers_results.json').read_text())
    names=['Reader pref.','Writer pref.','Fair queue']
    means_r=[rw['policies'][k]['reader_wait']['mean_ms'] for k in ['reader','writer','fair']]
    means_w=[rw['policies'][k]['writer_wait']['mean_ms'] for k in ['reader','writer','fair']]
    fig,ax=plt.subplots(figsize=(10.5,4.4)); x=range(3)
    ax.bar([i-.18 for i in x],means_r,width=.34,color=COL['cyan'],label='Reader mean wait')
    ax.bar([i+.18 for i in x],means_w,width=.34,color=COL['orange'],label='Writer mean wait')
    ax.set_xticks(list(x),names); ax.set_ylabel('Mean wait (ms)'); ax.set_title('Measured mean wait by admission policy',color=COL['navy'],pad=14)
    ax.grid(axis='y',color='#E5EAF0'); ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False)
    finish(fig,out(ex,'chart_policy_wait.png'))
    gantt_image(ex,'gantt_policy_interleavings.png','Illustrative readers-writers policy timelines',[
        ('Reader preference',[(0,3),(1,3),(3,2)]),('Waiting writer',[(2,3)]),
        ('Writer preference',[(0,3)]),('Priority writer',[(3,2)]),('Held-back reader',[(5,2)]),
        ('Fair queue: readers',[(0,3),(6,2)]),('Fair queue: writer',[(3,3)])],
        'Schematic admission timelines: active reader groups can overlap; writers require an exclusive interval. Not benchmark timestamps.')
    metric_chart(ex,'chart_reader_concurrency.png','Reader concurrency and completed operations',
        ['Peak simultaneous readers','Read entries / 100','Write entries / 100'],
        [rw['policies']['fair']['peak_simultaneous_readers'],rw['policies']['fair']['read_entries']/5,rw['policies']['fair']['write_entries']],
        [COL['cyan'],COL['blue'],COL['orange']],'Count')

    # Exercise 8: dining philosophers.
    ex='exercise-8-dining-philosophers-deadlock-starvation'
    ring_image(ex,'fig_philosopher_ring.png')
    cycle_image(ex,'fig_circular_wait.png')
    flow_image(ex,'fig_resource_hierarchy.png','Global resource hierarchy: acquire forks in increasing rank',[
        (.6,1.8,2.2,1.1,'REQUEST','Need two forks',COL['light']),
        (3.55,1.8,2.2,1.1,'ORDER','Sort by fork id', '#E7F4F5'),
        (6.5,1.8,2.2,1.1,'ACQUIRE','Low id before high id','#FFF1DE'),
        (9.45,1.8,2.0,1.1,'RELEASE','Reverse / scoped release','#E8F4EC')],
        [((2.8,2.35),(3.5,2.35),None),((5.75,2.35),(6.45,2.35),None),((8.7,2.35),(9.4,2.35),None)])
    dining=json.loads((ROOT/ex/'output'/'dining_philosophers_results.json').read_text())
    entry=dining['fair_monitor']['entry_log'][:30]
    lanes=[]
    for pnum in range(5): lanes.append((f'Philosopher {pnum}',[(i,1) for i,v in enumerate(entry) if v==pnum]))
    gantt_image(ex,'gantt_monitor_admission.png','Fair-monitor admission order: first 30 entries',lanes,
        'Each marked slot is one monitor admission from the recorded entry log; this is an order chart, not elapsed meal duration.')
    metric_chart(ex,'chart_philosopher_safety.png','Dining-philosophers completion and concurrency evidence',
        ['Meals completed (total)','Observed simultaneous eaters','Theoretical maximum'],
        [sum(dining['fair_monitor']['completed_meals']),dining['fair_monitor']['max_simultaneous_eaters'],dining['fair_monitor']['theoretical_max_simultaneous_eaters']],
        [COL['green'],COL['blue'],COL['orange']],'Count')

    print('Generated exercise-specific visuals for Exercises 4–8.')

if __name__=='__main__': main()
