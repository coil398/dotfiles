"""Independent value-tree oracle. No production imports or parser reuse."""
import random


def cases():
    rng=random.Random(271828)
    leaves=[('name','a'),('name','b'),('name','c'),('lit',False),('lit',7)]
    def grow(depth):
        if not depth: return rng.choice(leaves)
        return (rng.choice(['and','or','==','not']),grow(depth-1),grow(depth-1))
    return [grow(4) for _ in range(64)]


def render(t):
    if t[0]=='name': return t[1]
    if t[0]=='lit': return 'false' if t[1] is False else str(t[1])
    if t[0]=='not': return '(not '+render(t[1])+')'
    return '('+render(t[1])+' '+t[0]+' '+render(t[2])+')'


def run(t,context):
    op=t[0]
    if op=='name': return context[t[1]]
    if op=='lit': return t[1]
    left=run(t[1],context)
    if op=='not': return not left
    if op=='and': return run(t[2],context) if left else left
    if op=='or': return left if left else run(t[2],context)
    return left==run(t[2],context)
