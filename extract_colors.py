import fitz, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

doc = fitz.open(r'C:\SIH\SIH26104--Presentation-Format.pptx.pdf')
for i, page in enumerate(doc):
    print(f'\n=== PAGE {i+1} ===')
    # Sample background colors at several points
    pix = page.get_pixmap(dpi=36)  # low res for sampling
    from collections import Counter
    # Sample pixels
    w, h = pix.width, pix.height
    samples = []
    padding = 5
    for x in range(padding, w-padding, max(1, w//20)):
        for y in range(padding, h-padding, max(1, h//20)):
            samples.append(pix.pixel(x, y))
    common = Counter(samples).most_common(8)
    for rgb, cnt in common:
        print(f'  bg RGB({rgb[0]},{rgb[1]},{rgb[2]}) count={cnt}')
    # Extract images on page
    images = page.get_images(full=True)
    print(f'  Images on page: {len(images)}')
    # Get drawings/vector info
    drawings = page.get_drawings()
    print(f'  Vector drawings: {len(drawings)}')
    rects = []
    fills = []
    for d in drawings:
        if d['type'] == 'f':
            r = d['rect']
            rects.append(r)
            if d.get('fill'):
                fills.append(tuple(d['fill']))
    if rects:
        print(f'  Sample rect count: {len(rects)}')
        from collections import Counter
        fc = Counter(fills).most_common(6)
        for f, c in fc:
            print(f'    fill RGB({f[0]*255:.0f},{f[1]*255:.0f},{f[2]*255:.0f}) count={c}')
doc.close()
print('\nDONE')