# python sample.py <id> [windows=14] [chars=520] -> evenly spaced excerpts of a transcript
import sys,re
vid=sys.argv[1]; w=int(sys.argv[2]) if len(sys.argv)>2 else 14; c=int(sys.argv[3]) if len(sys.argv)>3 else 520
L=open(f"out/{vid}.txt",encoding="utf-8").read().splitlines()
print(L[0][:140]); T=[re.sub(r"^\[([0-9:]+)\] ",r"\1 ",l) for l in L[1:]]
step=max(1,len(T)//w)
for i in range(0,len(T),step):
    print("-", " ".join(T[i:i+8])[:c])
