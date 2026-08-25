# -*- coding: utf-8 -*-
"""Applying the lexical judgements to the reading edition.

Each correction is validated against the original record, then applied to the
text of the definitions alone -- never to the headwords. Everything is logged.

Most of the corrections returned are badly reglued HYPHENATIONS:
« re-cevar », « pro-duktita », « kom-batis », « fa-cile ». The automatic
regluing had missed them because its safeguard kept the hyphen when the
left-hand fragment was itself an attested root -- and « re », « pro », « kom »,
« des », « mi » are precisely prefixes. The remedy is therefore laid here:
when the corrected form ends with the form read, we erase the hyphen and
reglue, instead of replacing one word by another.
"""
import json, re, sys, collections
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=_ROOT + "/work"

def run_step(rep=f"{T}/judge/answers/r.txt", fic=f"{T}/judge/records.json"):
    records={x['id']:x for x in json.load(open(fic))}
    corr=[]
    for l in open(rep,encoding='utf-8'):
        i,_,v=l.rstrip("\n").partition("\t")
        if not v.strip() or not i.strip().isdigit(): continue
        x=records.get(int(i))
        if x is None: continue
        corr.append((x['mot'], v.strip()))
    ent=[json.loads(l) for l in open(f"{T}/editions/dicionario.jsonl",encoding='utf-8')]
    log_=[]
    for word, good in corr:
        # hyphenation: « pro-duktita » -> « produktita »
        if good.lower().endswith(word.lower()) and len(good)>len(word):
            head=good[:len(good)-len(word)]
            pattern=re.compile(r'\b'+re.escape(head)+r'[-\s]+'+re.escape(word)+r'\b', re.I)
        else:
            pattern=re.compile(r'\b'+re.escape(word)+r'\b', re.I)
        for e in ent:
            s=e.get('senci') or []
            for k,t in enumerate(s):
                nt,n=pattern.subn(good, t)
                if n: log_.append((e['image'],e['ligno'],word,good)); s[k]=nt
    with open(f"{T}/editions/dicionario.jsonl","w",encoding='utf-8') as f:
        for e in ent: f.write(json.dumps(e,ensure_ascii=False)+"\n")
    with open(f"{T}/judgements.txt","w",encoding='utf-8') as f:
        f.write("# image\tline\tform read\tform kept\n")
        for x in log_: f.write("%s\t%s\t%s\t%s\n"%x)
    print("corrections kept: %d ; occurrences replaced: %d"%(len(corr),len(log_)))
    return log_

if __name__=="__main__": run_step()
