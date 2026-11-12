import kb, rules, cpm
from cpm import Activity
print(len(kb.KB), "proyectos")
for p in kb.KB:
    acts = [Activity(i, n, list(pr), a, m, b, pe, ph) for i, n, ph, pr, a, m, b, pe in p["acts"]]
    r = cpm.compute(acts)
    pr = rules.check(acts, p["team"], p["complexity"])
    print(p["id"], p["complexity"], len(acts), round(r.duration, 1), "OK" if not pr else pr)
