import csv

rows = []
with open('data/eval/results-20260602-171005.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

cats = {}
for r in rows:
    cat = r['categorie']
    if cat not in cats:
        cats[cat] = {'faith': [], 'corr': [], 'ctx': [], 'n': 0}
    cats[cat]['n'] += 1
    if r['faithfulness']:
        cats[cat]['faith'].append(float(r['faithfulness']))
    if r['answer_correctness']:
        cats[cat]['corr'].append(float(r['answer_correctness']))
    if r['context_relevance']:
        cats[cat]['ctx'].append(float(r['context_relevance']))

print(f'Total questions evaluees: {len(rows)}')
print()
for cat, m in sorted(cats.items()):
    f_avg = sum(m['faith'])/len(m['faith']) if m['faith'] else 0
    c_avg = sum(m['corr'])/len(m['corr']) if m['corr'] else 0
    x_avg = sum(m['ctx'])/len(m['ctx']) if m['ctx'] else 0
    print(f'{cat}: N={m["n"]} | faithfulness={f_avg:.3f} | correctness={c_avg:.3f} | ctx_relevance={x_avg:.3f}')

all_f = [float(r['faithfulness']) for r in rows if r['faithfulness']]
all_c = [float(r['answer_correctness']) for r in rows if r['answer_correctness']]
all_x = [float(r['context_relevance']) for r in rows if r['context_relevance']]
print()
print(f'GLOBAL faithfulness   : {sum(all_f)/len(all_f):.3f}')
print(f'GLOBAL correctness    : {sum(all_c)/len(all_c):.3f}')
print(f'GLOBAL ctx_relevance  : {sum(all_x)/len(all_x):.3f}')

# Distribution des scores de correctness
print()
print('Distribution correctness:')
buckets = {'>= 0.8': 0, '0.5-0.79': 0, '< 0.5': 0}
for v in all_c:
    if v >= 0.8:
        buckets['>= 0.8'] += 1
    elif v >= 0.5:
        buckets['0.5-0.79'] += 1
    else:
        buckets['< 0.5'] += 1
for k, v in buckets.items():
    print(f'  {k}: {v} ({100*v/len(all_c):.0f}%)')
