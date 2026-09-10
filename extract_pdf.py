import fitz, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

doc = fitz.open(r'C:\SIH\SIH26104--Presentation-Format.pptx.pdf')
for i, page in enumerate(doc):
    print(f'\n=== PAGE {i+1} ===')
    print(f'Width: {page.rect.width}, Height: {page.rect.height}')
    blocks = page.get_text('dict')['blocks']
    # sort by y position
    items = []
    for b in blocks:
        if b['type'] == 0:
            for line in b['lines']:
                for span in line['spans']:
                    txt = span['text'].strip()
                    if txt:
                        items.append({
                            'x': round(span['bbox'][0], 1),
                            'y': round(span['bbox'][1], 1),
                            'size': round(span['size'], 1),
                            'color': span['color'],
                            'font': span['font'],
                            'text': txt[:80],
                        })
    items.sort(key=lambda z: (z['y'], z['x']))
    for it in items:
        print(f"  [{it['x']:>6.1f},{it['y']:>6.1f}] sz={it['size']:>5.1f} col=#{it['color']:06x} font={it['font']}  \"{it['text']}\"")
doc.close()
print('\nDONE')