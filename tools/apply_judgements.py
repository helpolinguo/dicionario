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
T="/root/dicionario/travail"

def run_step(rep=f"{T}/juger/reponses/r.txt", fic=f"{T}/juger/fiches.json"):
    records={x['id']:x for x in json.load(open(fic))}
    corr=[]
    for l in open(rep,encoding='utf-8'):
        i,_,v=l.rstrip("\n").partition("\t")
        if not v.strip() or not i.strip().isdigit(): continue
        x=records.get(int(i))
        if x is None: continue
        corr.append((x['mot'], v.strip()))
    ent=[json.loads(l) for l in open(f"{T}/edicioni/dicionario.jsonl",encoding='utf-8')]
    log_=[]
    for word, good in corr:
        # hyphenation: « pro-duktita » -> « produktita »
        if good.lower().endswith(word.lower()) and len(good)>len(word):
            head=good[:len(good)-len(word)]
            motif=re.compile(r'\b'+re.escape(head)+r'[-\s]+'+re.escape(word)+r'\b', re.I)
        else:
            motif=re.compile(r'\b'+re.escape(word)+r'\b', re.I)
        for e in ent:
            s=e.get('senci') or []
            for k,t in enumerate(s):
                nt,n=motif.subn(good, t)
                if n: log_.append((e['image'],e['ligno'],word,good)); s[k]=nt
    with open(f"{T}/edicioni/dicionario.jsonl","w",encoding='utf-8') as f:
        for e in ent: f.write(json.dumps(e,ensure_ascii=False)+"\n")
    with open(f"{T}/jugements.txt","w",encoding='utf-8') as f:
        f.write("# image\tligne\tforme lue\tforme retenue\n")
        for x in log_: f.write("%s\t%s\t%s\t%s\n"%x)
    print("corrections retenues : %d ; occurrences remplacees : %d"%(len(corr),len(log_)))
    return log_

if __name__=="__main__": run_step()
