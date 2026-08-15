# -*- coding: utf-8 -*-
"""Exportation de la base lexicale : JSONL, TSV, et edition HTML autonome."""
import json, os, sys, html, collections
T="/root/dicionario/travail"; SORT=f"{T}/edicioni"

def charger():
    return [json.loads(l) for l in open(f"{SORT}/dicionario.jsonl",encoding='utf-8')]

def tsv(ent):
    with open(f"{SORT}/dicionario.tsv","w",encoding='utf-8') as f:
        f.write("vedetto\tfako\tsenci\tnomi_latina\tlingui\tkodo\tpagino\tligno\timago\tdrapeli\n")
        for e in ent:
            f.write("\t".join([
                e['vedetto'], e['fako'] or "",
                " ¶ ".join(e['senci']), "; ".join(e['latina']),
                ",".join(e['lingui']), e['kodo'] or "",
                str(e['pagino']), str(e['ligno']), str(e['image']),
                ",".join(e['drapeli'])]).replace("\n"," ")+"\n")

GABARITO = """<!DOCTYPE html><html lang="io"><meta charset="utf-8">
<title>Dicionario de la 10.000 radiki di la linguo universala Ido</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--enk:#1a1a1a;--pap:#fbfaf7;--sub:#6b6560;--acc:#7a4b2a;--lin:#e2ddd5;--flag:#b4552d}
@media(prefers-color-scheme:dark){:root{--enk:#e8e4de;--pap:#16161a;--sub:#9a938c;--acc:#d69a6a;--lin:#2c2c33;--flag:#e08a5c}}
*{box-sizing:border-box}
body{margin:0;background:var(--pap);color:var(--enk);
 font:16px/1.55 "Iowan Old Style",Palatino,"Palatino Linotype",Georgia,serif}
header{position:sticky;top:0;background:var(--pap);border-bottom:1px solid var(--lin);
 padding:14px 20px 12px;z-index:9}
h1{margin:0 0 2px;font-size:17px;font-weight:600;letter-spacing:.01em}
.sub{color:var(--sub);font-size:12.5px;margin-bottom:10px}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
input[type=search]{flex:1 1 260px;min-width:200px;padding:8px 11px;border:1px solid var(--lin);
 border-radius:7px;background:var(--pap);color:var(--enk);font:inherit;font-size:16px}
/* 16px exacte, e ne min: Safari sur iPhone zomas automate sur irga kampo di
   qua la litero-grandeso esas sub 16px, kande onu tushas lu. La altra
   solvuro — maximum-scale=1 en la meta viewport — impedus anke la zomo per
   la fingri, do la lekteblesa por qui bezonas lu. */
input[type=search]:focus{outline:2px solid var(--acc);outline-offset:-1px}
label.f{font-size:12.5px;color:var(--sub);display:flex;gap:5px;align-items:center;cursor:pointer;
 font-family:system-ui,sans-serif}
#kont{max-width:820px;margin:0 auto;padding:18px 20px 80px}
#nombro{color:var(--sub);font-size:12.5px;margin:0 0 14px;font-family:system-ui,sans-serif}
article{padding:11px 0;border-bottom:1px solid var(--lin)}
.ved{font-weight:700;font-size:17px}
.fako{color:var(--acc);font-style:italic;font-size:14px;margin-left:6px}
.senco{margin:4px 0 0}
.senco b{color:var(--sub);font-weight:600;font-size:13px;margin-right:4px}
.lat{font-style:italic;color:var(--sub)}
.meta{margin-top:5px;font-size:11.5px;color:var(--sub);font-family:system-ui,sans-serif;
 display:flex;gap:9px;flex-wrap:wrap}
.dr{color:var(--flag)}
mark{background:rgba(214,154,106,.34);color:inherit;border-radius:2px}
</style>
<header>
<h1>Dicionario de la 10.000 radiki di la linguo universala Ido</h1>
<div class="sub">Marcelo Persiko (Marcel Pesch) · editio princeps, 2 di agosto 1964 · __N__ artikli</div>
<div class="bar">
 <input type="search" id="q" placeholder="Serchez radiko o vorto en la defino…" autocomplete="off">
</div>
</header>
<div id="kont"><p id="nombro"></p><div id="lst"></div></div>

<script>
const D=__DATA__;
const lst=document.getElementById('lst'),q=document.getElementById('q'),
      nb=document.getElementById('nombro');
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function surl(t,r){if(!r)return esc(t);return esc(t).replace(new RegExp('('+r.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&')+')','gi'),'<mark>$1</mark>');}
function rendi(e,r){
 // Emprunt cite : chevrons a l'affichage seulement. La recherche porte sur
 // le mot nu, sinon « amen » ne se trouverait plus.
 let h='<article><span class="ved">'+(e.c?'\u00ab\u00a0':'')+surl(e.v,r)+(e.c?'\u00a0\u00bb':'')+'</span>';
 if(e.f)h+='<span class="fako">('+esc(e.f)+')</span>';
 e.s.forEach((s,i)=>{h+='<p class="senco">'+(e.s.length>1?'<b>'+(i+1)+'.</b>':'')+surl(s,r)+'</p>';});
 if(e.l&&e.l.length)h+='<p class="senco lat">L. '+esc(e.l.join('; '))+'</p>';
 h+='<div class="meta"><span>p. '+e.p+', l. '+e.g+'</span>';
 if(e.n&&e.n.length)h+='<span>'+esc(e.n.join(', '))+'</span>';
 if(e.d&&e.d.length)h+='<span class="dr">'+esc(e.d.join(' · '))+'</span>';
 return h+'</div></article>';}
// Distance de Levenshtein, bornee : on abandonne des que toute la ligne
// courante depasse le maximum tolere. Sert a retrouver un mot malgre une
// coquille — celles de l'original comme celles de qui cherche.
function lev(a,b,max){
 if(Math.abs(a.length-b.length)>max)return max+1;
 let prev=[],cur=[];
 for(let j=0;j<=b.length;j++)prev[j]=j;
 for(let i=1;i<=a.length;i++){
  cur[0]=i; let mini=i;
  for(let j=1;j<=b.length;j++){
   const c=(a.charCodeAt(i-1)===b.charCodeAt(j-1))?0:1;
   cur[j]=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+c);
   if(cur[j]<mini)mini=cur[j];}
  if(mini>max)return max+1;
  const t=prev; prev=cur; cur=t;}
 return prev[b.length];}
// Rang d'un article pour une recherche. La vedette passe AVANT la definition :
// chercher un mot qui est aussi cite dans dix definitions doit donner l'article
// de ce mot en tete, non en dixieme position.
//   0 vedette exacte · 1 vedette commencant par · 2 vedette contenant
//   3 vedette a une faute pres · 4 vedette a deux fautes pres · 5 definition
// Formes comparables d'une vedette. Le « * » des mots non officiels n'en fait
// pas partie. Et une elision — « ka(d) », « on(u) » — se cherche des deux
// manieres : la lettre entre parentheses ne s'ajoute que devant une voyelle,
// mais qui tape « kad » ou « onu » doit tomber sur l'article.
function formi(v){
 v=v.toLowerCase().replace(/^[*+]/,'');
 const m=v.match(/^([^()]+)\(([^()]+)\)$/);
 return m ? [m[1], m[1]+m[2]] : [v];
}
function rango(e,r){
 const fs=formi(e.v);
 let best=-1;
 for(const v of fs){const g=rang1(e,v,r); if(g>=0&&(best<0||g<best))best=g;}
 return best;
}
function rang1(e,v,r){
 if(v===r)return 0;
 if(v.startsWith(r))return 1;
 if(v.includes(r))return 2;
 if(r.length>=4){
  const d=lev(v,r,2);
  if(d<=1)return 3;
  if(d<=2)return 4;}
 if(e.s.join(' ').toLowerCase().includes(r))return 5;
 return -1;}
function montri(){
 const r=q.value.trim().toLowerCase();
 let sel=[];
 for(const e of D){
  if(!r){sel.push([0,e]);continue;}
  const g=rango(e,r);
  if(g>=0)sel.push([g,e]);}
 if(r)sel.sort((x,y)=>x[0]-y[0]||x[1].v.localeCompare(y[1].v));
 const n=sel.length;
 nb.textContent=n+' artikl'+(n>1?'i':'o')+(n>400?' — la 400 unesma montresas':'');
 lst.innerHTML=sel.slice(0,400).map(x=>rendi(x[1],r)).join('');}
q.addEventListener('input',montri); montri();
</script></html>"""

def html_edition(ent):
    D=[{"v":e['vedetto'],"f":e['fako'],"s":e['senci'],"l":e['latina'],
        "n":e['lingui'],"p":e['pagino'],"g":e['ligno'],"d":e['drapeli'],
        **({"c":1} if e.get('citita') else {})} for e in ent]
    s=GABARITO.replace("__DATA__", json.dumps(D, ensure_ascii=False, separators=(',',':')))
    s=s.replace("__N__", f"{len(ent)} ")
    open(f"{SORT}/dicionario.html","w",encoding='utf-8').write(s)
    return os.path.getsize(f"{SORT}/dicionario.html")

if __name__=="__main__":
    ent=charger(); tsv(ent); n=html_edition(ent)
    print(len(ent),"enregistrements ; HTML", round(n/1e6,2),"Mo")
    print("a verifier :", sum(1 for e in ent if e['drapeli']))
