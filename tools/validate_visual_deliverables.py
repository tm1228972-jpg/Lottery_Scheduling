#!/usr/bin/env python3
"""Fail the build if any report/deck omits embedded visual evidence."""
from pathlib import Path
import re
import zipfile
from pptx import Presentation
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
EXERCISES = [
    'exercise-1-lottery-algorithm-introduction',
    'exercise-2-lottery-vs-edf-rm-comparison',
    'exercise-3-manual-edf-rm-scheduling',
    'exercise-4-dekker-peterson-semaphores-monitors',
    'exercise-5-lottery-scheduling-synchronization-demo',
    'exercise-6-research-paper-and-seminar',
    'exercise-7-readers-writers-comparison',
    'exercise-8-dining-philosophers-deadlock-starvation',
]

def pdf_image_count(path: Path) -> int:
    reader = PdfReader(str(path))
    count = 0
    for page in reader.pages:
        try:
            count += len(page.images)
        except Exception:
            xobj = page.get('/Resources', {}).get('/XObject', {})
            try:
                count += sum(1 for obj in xobj.get_object().values()
                             if obj.get_object().get('/Subtype') == '/Image')
            except Exception:
                pass
    return count


def main():
    problems = []
    for idx, directory in enumerate(EXERCISES, start=1):
        docs = ROOT / directory / 'docs'
        for lang in ('EN', 'FA'):
            sources = list((ROOT / directory).glob(f'REPORT_{lang}.md'))
            if not sources:
                problems.append(f'{directory}: missing REPORT_{lang}.md')
                continue
            source = sources[0].read_text(encoding='utf-8')
            images = re.findall(r'!\[[^\]]*\]\(([^)]+\.png)\)', source)
            gantt = [p for p in images if 'gantt_' in p.lower()]
            if len(images) < 3:
                problems.append(f'{directory} {lang}: only {len(images)} Markdown figure references')
            if not gantt:
                problems.append(f'{directory} {lang}: no Gantt/timeline figure in report source')

            docx_files = list(docs.glob(f'Exercise*_{lang}.docx'))
            pdf_files = list(docs.glob(f'Exercise*_{lang}.pdf'))
            if not docx_files or not pdf_files:
                problems.append(f'{directory} {lang}: missing generated DOCX/PDF')
                continue
            docx = docx_files[0]
            with zipfile.ZipFile(docx) as zf:
                media = [n for n in zf.namelist() if n.startswith('word/media/')]
            if len(media) < 3:
                problems.append(f'{docx}: only {len(media)} embedded Word images')
            pdf = pdf_files[0]
            count = pdf_image_count(pdf)
            if count < 3:
                problems.append(f'{pdf}: only {count} embedded PDF images')
            print(f'Exercise {idx} {lang}: {len(images)} figure refs, {len(media)} DOCX images, {count} PDF images')

        deck = docs / f'Exercise{idx}_Visual_Seminar.pptx'
        deck_pdf = docs / f'Exercise{idx}_Visual_Seminar.pdf'
        if not deck.is_file() or not deck_pdf.is_file():
            problems.append(f'{directory}: missing visual slide deck or PDF export')
            continue
        prs = Presentation(str(deck))
        if len(prs.slides) != 5:
            problems.append(f'{deck}: expected 5 slides, got {len(prs.slides)}')
        for sn, slide in enumerate(prs.slides, start=1):
            pics = [s for s in slide.shapes if s.shape_type == 13]
            if not pics:
                problems.append(f'{deck}: slide {sn} has no embedded visual')
        if len(PdfReader(str(deck_pdf)).pages) != 5:
            problems.append(f'{deck_pdf}: expected 5 PDF pages')
        print(f'Exercise {idx} slides: {len(prs.slides)} slides; every slide contains an image')

    if problems:
        raise SystemExit('\n'.join(problems))
    print('PASS: all 16 Word/PDF reports include diagrams/charts and at least one Gantt/timeline; all 8 visual decks are complete.')

if __name__ == '__main__':
    main()
