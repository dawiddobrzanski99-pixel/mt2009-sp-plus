# CUSTOM_HORSE_POLYMORPH_TOOLTIP_V1
LABELS = (
    ('attack', 'Wartosc ataku', False), ('defense', 'Obrona', False),
    ('hp', 'Maksymalne HP', False), ('monster', 'Silny na potwory', True),
    ('boss', 'Silny na bossy', True), ('stone', 'Silny na metiny', True),
    ('move', 'Szybkosc ruchu', False), ('speed', 'Szybkosc ataku', True),
    ('resistMonster', 'Odpornosc na potwory', True), ('resistBoss', 'Odpornosc na bossy', True),
    ('classes', 'Odpornosc na kazda z 4 klas', True), ('human', 'Silny na ludzi', True),
    ('elements', 'Silny na kazdy z 6 zywiolow', True))
def level_of(grade, level):
    if grade >= 3: return 40
    return max(0, int(level) + (19 if grade == 1 else 29 if grade == 2 else 0))
def growth(level, maximum, last):
    return max(0, min(level,last)-10)*maximum//(last-10)
def horse(level):
    return dict(attack=min(max(level,0),10)*2, hp=min(max(level,0),10)*100,
        monster=growth(level,5,30),
        boss=0,
        stone=0, move=growth(level,20,21),
        classes=max(0,min(level,20)-11)*15//9, human=10 if level>=21 else 0,
        elements=5 if level>=23 else 2 if level==22 else 0,
        resistMonster=growth(level,5,30),resistBoss=growth(level,5,30))
def poly(level):
    if level>=40: return dict(attack=150,defense=150,monster=15,resistMonster=15,boss=10,stone=10,speed=15)
    if level<=29: return dict(attack=max(level,0)*50//29,defense=max(level,0)*50//29,speed=5 if level>=20 else 0)
    g=level-29
    return dict(attack=50+g*3,defense=50+g*2,monster=g,resistMonster=g,speed=5+g//2)
def append_rewards(tip, values, color):
    for key, text, percent in LABELS:
        n=values.get(key,0)
        if n: tip.AppendTextLine('%s: +%d%s' % (text,n,'%' if percent else ''),color)
def append_next(tip, current, following, name):
    delta=dict((k, following.get(k,0)-current.get(k,0)) for k, text, pct in LABELS)
    tip.AppendSpace(5)
    tip.AppendTextLine(name,tip.NEGATIVE_COLOR)
    if any(delta.values()): append_rewards(tip,delta,tip.NEGATIVE_COLOR)
    else: tip.AppendTextLine('Bez wzrostu bonusow na tym poziomie',tip.NEGATIVE_COLOR)
def append_horse(tip, grade, rawlevel):
    # SEBAN_HORSE_HOOK_V1
    import sebanhorseclient
    sebanhorseclient.append_horse(tip,grade,rawlevel)

def append_poly(tip, grade, rawlevel):
    level=level_of(grade,rawlevel);now=poly(level)
    tip.AppendSpace(5);tip.AppendTextLine('Dziala tylko podczas przemiany',tip.NORMAL_COLOR)
    append_rewards(tip,now,tip.POSITIVE_COLOR)
    if level>=40: tip.AppendTextLine('Czas przemiany: 60 minut',tip.POSITIVE_COLOR)
    elif level>=30: tip.AppendTextLine('Czas przemiany: 30 minut',tip.POSITIVE_COLOR)
    if level<40: append_next(tip,now,poly(level+1),'Bonus nastepnego poziomu:')
