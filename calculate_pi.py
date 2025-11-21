import random

insideCount=0
totalCount=1000000
for i in range(totalCount):
    x=random.random()*2-1
    y=random.random()*2-1
    if x*x+y*y<1:
        insideCount=insideCount+1

pi=4*insideCount/totalCount

print("pi = %f" %pi)