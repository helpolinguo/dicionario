# -*- coding: utf-8 -*-
"""Lexical cleaning of the reading edition — by the book's ROOTS.

The facsimile keeps the least slip: that is its reason for being. The HTML
edition must give the content of the work, not its accidents of typing.

FIRST VERSION, SET ASIDE. It corrected every rare form towards a frequent one
obtained by exchanging two characters the machine confuses. Over 537 forms it
rendered « papuli » (papules, in « erupto di papuli ») as « populi »
(peoples), « por-tar » as « por-par », and replaced the headword « agapo » by
« agato » -- two real words, the one driving out the other. Raw frequency
ignores sense, and above all morphology: in Ido the ending carries the nature
of the word, -o noun, -a adjective, -e adverb, -ar verb. Changing it is never
a typographic correction.

VERSION ADOPTED. Ido is an a posteriori language: its roots are
international, so they RECUR through the book. The dictionary is thus its own
lexicon. We correct a word of a definition only if:

  1. its root exists NOWHERE as a headword of the book -- the word therefore
     makes no sense in Ido;
  2. a single exchange of look-alikes suffices to make it an attested root;
  3. the exchange does not touch the grammatical ending.

The headwords are never touched: a headword is an article, not an occurrence.
The doubt always benefits the original.

VERSION ADOPTED, NOT APPLIED. It fails too, and for a fundamental reason.
Over 116 proposals it renders « falko » as « talko », « anglo » as « unglo »,
« adoptas » as « adaptas », « feko » as « foko »: all perfectly real Ido
words, which simply are not HEADWORDS of this dictionary. A dictionary of
10,000 roots is not the list of every word of the language: its definitions
use derivatives, proper nouns, Latin forms. Its internal lexicon therefore
cannot serve as arbiter.

Conclusion, verified twice by two methods: no automatic pass here
distinguishes a slip from a legitimate word. It needs a genuine Ido lexicon,
or a reading in context. This tool stays in PROPOSAL mode: it gives a list to
be examined, it changes nothing.
"""
import json, re, sys, collections
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from pairs import PAIRS
T=_ROOT + "/work"

LOOKALIKE=collections.defaultdict(set)
for a,b in PAIRS:
    if len(a)==1 and len(b)==1: LOOKALIKE[a].add(b); LOOKALIKE[b].add(a)
WORD=re.compile(r"[A-Za-zÀ-ÿ]{4,}")
ENDINGS=("ar","ir","or","as","is","os","us","o","a","e","i")
# Function words: they have no headword root and must undergo nothing.
GRAM=set("""la le lo li ed od ma nam kad ka ke ke qua quo qui quan quin kande ube
pro por per pri sen sub sur tra trans ye da de di del dil en inter kun dum kontre
ante dop apud avan cirkum til vers nur anke tam tante quale quante on onu ol olu
il ilu el elu lu li ni vi me tu su ta ti ica ita ca co to omna ula nula multa poka
plu min maxim tre ne yes se do lore nun hike ibe kad esas esis esos esez havas
kom kad e a an al ek for pos segun malgre exter extere intre""".split())

def roots(ent):
    r=set()
    for e in ent:
        v=(e.get('vedetto') or "").lower().lstrip("*+-").rstrip("-")
        if not v: continue
        r.add(v)
        for f in ENDINGS:
            if v.endswith(f) and len(v)-len(f)>=2: r.add(v[:-len(f)]); break
    return r

def _root(w):
    for f in ENDINGS:
        if w.endswith(f) and len(w)-len(f)>=2: return w[:-len(f)]
    return w

def known(w, root):
    w=w.lower()
    return w in root or _root(w) in root or w in GRAM

def variants(w):
    """Exchanges of look-alikes, never on the grammatical ending."""
    n=len(w); end_=len(w)-len(_root(w))
    for i,c in enumerate(w):
        if i >= n-max(end_,1): break
        for d in LOOKALIKE.get(c,()):
            yield w[:i]+d+w[i+1:]

def propose(ent):
    root=roots(ent)
    freq=collections.Counter()
    for e in ent:
        for t in (e.get('senci') or []):
            for w in WORD.findall(t): freq[w.lower()]+=1
    prop={}
    for w,n in freq.items():
        if known(w, root): continue
        cands=[v for v in set(variants(w)) if known(v, root) and freq.get(v,0)+1>n]
        if len(cands)==1: prop[w]=cands[0]
    return prop, root

if __name__=="__main__":
    ent=[json.loads(l) for l in open(f"{T}/editions/dicionario.jsonl",encoding='utf-8')]
    prop,root=propose(ent)
    print("roots known: %d ; corrections proposed: %d"%(len(root),len(prop)))
    for w,v in sorted(prop.items())[:40]: print("   %-22s -> %s"%(w,v))
