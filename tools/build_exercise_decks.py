#!/usr/bin/env python3
"""Build a concise visual slide deck for every exercise (1–8)."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.xmlchemy import OxmlElement

ROOT=Path(__file__).resolve().parents[1]
NAVY='183153'; BLUE='3977B9'; MUTED='66758B'; PAPER='F5F8FC'
EXERCISES={
1:{'folder':'exercise-1-lottery-algorithm-introduction','title':'Lottery Scheduling','fa':'زمان‌بندی قرعه‌کشی','subtitle':'Proportional-share allocation and seeded experiments','fa_sub':'تخصیص سهم‌متناسب، احتمال و آزمایش‌های بازتولیدپذیر','figs':[
('Decision flow','جریان یک تصمیم زمان‌بندی','diagrams/fig_flowchart.png','The draw maps a winning ticket to exactly one eligible process.'),
('Ticket intervals','بازه‌های بلیت','diagrams/fig_ticket_intervals.png','Ticket ranges form a contiguous decision line.'),
('Ticket share error','خطای سهم بلیت','diagrams/chart_share_error.png','Observed shares approach ticket proportions over repeated decisions.'),
('Baseline Gantt','گانت‌چارت زمان‌بندی پایه','diagrams/gantt_baseline.png','Each bar shows which process receives a CPU quantum.') ]},
2:{'folder':'exercise-2-lottery-vs-edf-rm-comparison','title':'Lottery vs. EDF / RM','fa':'قرعه‌کشی در برابر EDF و RM','subtitle':'Same periodic workload, different scheduling objectives','fa_sub':'بار تناوبی یکسان، هدف‌های زمان‌بندی متفاوت','figs':[
('Policy comparison','مقایسه سیاست‌ها','diagrams/chart_policy_comparison.png','Deadline misses and response metrics distinguish proportional fairness from deadline policies.'),
('EDF schedule','گانت‌چارت EDF','diagrams/gantt_set_b_edf.png','EDF selects the ready job with the earliest absolute deadline.'),
('Lottery schedule','گانت‌چارت Lottery','diagrams/gantt_set_b_lottery.png','Lottery grants quanta probabilistically and can miss hard deadlines.'),
('RM schedule','گانت‌چارت RM','diagrams/gantt_set_b_rm.png','RM assigns fixed priorities from task periods.') ]},
3:{'folder':'exercise-3-manual-edf-rm-scheduling','title':'Manual EDF / RM Scheduling','fa':'زمان‌بندی دستی EDF و RM','subtitle':'Worked schedules, utilization bounds, and deadline analysis','fa_sub':'حل گام‌به‌گام، کران بهره‌وری و تحلیل ضرب‌الاجل','figs':[
('Seven-step manual method','روش دستی هفت‌مرحله‌ای','diagrams/fig_manual_method.png','A repeatable pencil-and-paper process for constructing a schedule.'),
('Deadline misses','خطاهای ضرب‌الاجل','diagrams/chart_misses.png','The same task set can be schedulable under one policy and not another.'),
('EDF Gantt','گانت‌چارت EDF','diagrams/gantt_ex3_3_edf_not_rm_edf.png','Tick-by-tick service order for the constrained example.'),
('Utilization bound','کران بهره‌وری','diagrams/chart_utilization_bound.png','Utilization bounds are sufficient tests, not universal exact feasibility checks.') ]},
4:{'folder':'exercise-4-dekker-peterson-semaphores-monitors','title':'Synchronization Primitives','fa':'الگوریتم‌های همگام‌سازی','subtitle':'Dekker, Peterson, semaphores, monitors, and safety','fa_sub':'دکر، پیترسون، سمافور، مانیتور و ایمنی','figs':[
('Monitor design','ساختار مانیتور','diagrams/fig_monitor.png','A monitor combines shared state, a mutex, and condition-variable predicates.'),
('Lost updates','به‌روزرسانی‌های ازدست‌رفته','diagrams/chart_lost_updates.png','An unprotected read-modify-write sequence can lose increments.'),
('Critical-section Gantt','گانت‌چارت بخش بحرانی','visuals/gantt_synchronization_interleaving.png','Safe interleaving serializes protected entries across two threads.'),
('Dekker protocol','پروتکل دکر','diagrams/fig_dekker_protocol.png','The entry protocol expresses intent, checks the other process, and resolves contention.') ]},
5:{'folder':'exercise-5-lottery-scheduling-synchronization-demo','title':'Lottery Lock Synchronization','fa':'همگام‌سازی با قفل قرعه‌کشی','subtitle':'Weighted admission, ownership, and mutual exclusion','fa_sub':'پذیرش وزن‌دار، مالکیت و انحصار متقابل','figs':[
('Lock architecture','معماری قفل','visuals/fig_lock_architecture.png','Requests enter a wait set, one winner is selected, and ownership protects the critical section.'),
('Observed share','سهم مشاهده‌شده','visuals/chart_lock_shares.png','The seeded run compares grant shares with the 5:3:2 ticket target.'),
('Grant Gantt','گانت‌چارت اعطای قفل','visuals/gantt_lock_grants.png','Each block is one lock grant from the recorded experiment trace.'),
('Mutual exclusion evidence','شواهد انحصار متقابل','visuals/chart_mutual_exclusion.png','The measured maximum concurrent critical sections is one, with no recorded error.') ]},
6:{'folder':'exercise-6-research-paper-and-seminar','title':'Lottery Scheduling Research','fa':'پژوهش زمان‌بندی قرعه‌کشی','subtitle':'Lottery vs. stride, reproducible evidence, and research limits','fa_sub':'مقایسه با stride، شواهد بازتولیدپذیر و محدودیت پژوهش','figs':[
('Policy pipeline','جریان مقایسه سیاست‌ها','visuals/fig_lottery_stride_pipeline.png','Both policies receive the same workload before their share errors are reviewed.'),
('Share error','خطای سهم','visuals/chart_lottery_stride_error.png','Mean and worst lottery errors are compared with the deterministic stride result.'),
('Experiment Gantt','گانت‌چارت آزمایش','visuals/gantt_experiment_plan.png','Lottery seeds and the stride baseline run as parallel experimental branches.'),
('Policy sequence','توالی تخصیص سیاست‌ها','visuals/gantt_policy_sequences.png','An illustrative 24-slot trace contrasts random draws with virtual-pass order.') ]},
7:{'folder':'exercise-7-readers-writers-comparison','title':'Readers-Writers Policies','fa':'سیاست‌های خوانندگان و نویسندگان','subtitle':'Reader preference, writer preference, and fair admission','fa_sub':'اولویت خواننده، اولویت نویسنده و پذیرش منصفانه','figs':[
('Admission logic','منطق پذیرش','visuals/fig_readers_writers_admission.png','Readers may overlap, while writers require exclusive access.'),
('Wait-time comparison','مقایسه زمان انتظار','visuals/chart_policy_wait.png','Observed reader and writer wait measurements reveal the policy trade-off.'),
('Policy Gantt','گانت‌چارت سیاست‌ها','visuals/gantt_policy_interleavings.png','Schematic timelines explain reader and writer overtaking behaviour.'),
('Reader concurrency','هم‌زمانی خوانندگان','visuals/chart_reader_concurrency.png','The shared lock permits parallel readers while writers remain exclusive.') ]},
8:{'folder':'exercise-8-dining-philosophers-deadlock-starvation','title':'Dining Philosophers','fa':'مسئله فیلسوفان غذاخور','subtitle':'Circular wait, resource hierarchy, and fair monitor admission','fa_sub':'انتظار دوری، ترتیب منابع و پذیرش منصفانه با مانیتور','figs':[
('Philosopher ring','حلقه فیلسوفان','visuals/fig_philosopher_ring.png','Adjacent philosophers compete for a shared fork.'),
('Circular wait','گراف انتظار دوری','visuals/fig_circular_wait.png','Every philosopher waits for a fork held by the next neighbour.'),
('Safety and concurrency','نمودار ایمنی و هم‌زمانی','visuals/chart_philosopher_safety.png','All meals finish; observed concurrency is reported beside the theoretical ring maximum.'),
('Fair monitor Gantt','گانت‌چارت پذیرش مانیتور','visuals/gantt_monitor_admission.png','Recorded entry order from the fair monitor, expressed as admission slots.') ]}
}

def add_text(slide,text,x,y,w,h,size,color=NAVY,bold=False,align=PP_ALIGN.LEFT):
    sh=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=sh.text_frame; tf.clear(); tf.word_wrap=True; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    p=tf.paragraphs[0]; p.text=text; p.alignment=align; p.font.name='Aptos'; p.font.size=Pt(size); p.font.bold=bold; p.font.color.rgb=RGBColor.from_string(color); return sh

def add_transition(slide):
    tr=OxmlElement('p:transition'); tr.set('spd','fast'); tr.append(OxmlElement('p:fade')); slide._element.insert(1,tr)

def base_slide(prs,title,fa_title,number,total):
    s=prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb=RGBColor.from_string(PAPER)
    bar=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,prs.slide_width,Inches(.1)); bar.fill.solid(); bar.fill.fore_color.rgb=RGBColor.from_string(BLUE); bar.line.fill.background()
    add_text(s,title,.65,.35,11.8,.54,24,NAVY,True); add_text(s,fa_title,.68,.94,11.6,.34,13,BLUE,True)
    add_text(s,f'{number:02d} / {total:02d}',11.78,7.04,.9,.2,8,MUTED,False,PP_ALIGN.RIGHT)
    add_text(s,'OPERATING SYSTEMS  •  EXERCISE VISUAL NOTES',.68,7.04,8,.2,8,MUTED)
    add_transition(s); return s

def main():
    for n,cfg in EXERCISES.items():
        prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
        s=base_slide(prs,f'Exercise {n} — {cfg["title"]}',cfg['fa'],1,len(cfg['figs'])+1)
        add_text(s,cfg['subtitle'],.9,1.85,5.4,.7,20,NAVY,True)
        add_text(s,cfg['fa_sub'],.9,2.65,5.4,.55,15,BLUE,True)
        add_text(s,'A compact visual guide: concept, measured evidence, and a task-specific Gantt timeline.',.92,3.55,5.0,.8,15,MUTED)
        cover_img=ROOT/cfg['folder']/cfg['figs'][0][2]
        if not cover_img.exists(): raise FileNotFoundError(cover_img)
        from PIL import Image
        with Image.open(cover_img) as im: cw,ch=im.size
        cscale=min(5.9/cw,4.75/ch); cwidth,cheight=cw*cscale,ch*cscale
        s.shapes.add_picture(str(cover_img),Inches(6.55+(5.9-cwidth)/2),Inches(1.55+(4.75-cheight)/2),width=Inches(cwidth),height=Inches(cheight))
        for idx,(title,fa_title,path,caption) in enumerate(cfg['figs'],start=2):
            s=base_slide(prs,title,fa_title,idx,len(cfg['figs'])+1)
            add_text(s,caption,.85,1.48,11.6,.62,13,MUTED)
            img=ROOT/cfg['folder']/path
            if not img.exists(): raise FileNotFoundError(img)
            with Image.open(img) as im: iw,ih=im.size
            maxw,maxh=11.7,4.75; scale=min(maxw/iw,maxh/ih)
            w,h=iw*scale,ih*scale
            s.shapes.add_picture(str(img),Inches((13.333-w)/2),Inches(2.15+(4.75-h)/2),width=Inches(w),height=Inches(h))
        out=ROOT/cfg['folder']/'docs'/f'Exercise{n}_Visual_Seminar.pptx'; out.parent.mkdir(parents=True,exist_ok=True); prs.save(out)
        print(f'Wrote {out} ({len(prs.slides)} slides)')
if __name__=='__main__': main()
