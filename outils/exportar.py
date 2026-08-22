# -*- coding: utf-8 -*-
"""Exportation de la base lexicale : JSONL, TSV, et edition HTML autonome."""
import json, os, sys, html, collections
T="/root/dicionario/travail"; SORT=f"{T}/edicioni"

def charger():
    return [json.loads(l) for l in open(f"{SORT}/dicionario.jsonl",encoding='utf-8')]

def tsv(ent):
    with open(f"{SORT}/dicionario.tsv","w",encoding='utf-8') as f:
        f.write("vedetto\tfako\tsenci\tnomi_latina\tsimbolo_kemiala\tlingui\tkodo\tpagino\tligno\timago\tdrapeli\n")
        for e in ent:
            f.write("\t".join([
                e['vedetto'], e['fako'] or "",
                " ¶ ".join(e['senci']), "; ".join(e['latina']),
                e.get('simbolo') or "",
                ",".join(e['lingui']), e['kodo'] or "",
                str(e['pagino']), str(e['ligno']), str(e['image']),
                ",".join(e['drapeli'])]).replace("\n"," ")+"\n")

GABARITO = """<!DOCTYPE html><html lang="io"><meta charset="utf-8">
<title>Dicionario de la 10.000 radiki di la linguo universala Ido</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--enk:#1a1a1a;--pap:#fbfaf7;--sub:#6b6560;--acc:#7A3D00;--lin:#e2ddd5;--flag:var(--acc)}
@media(prefers-color-scheme:dark){:root{--enk:#e8e4de;--pap:#16161a;--sub:#9a938c;--acc:#D6A06A;--lin:#2c2c33}}
*{box-sizing:border-box}
body{margin:0;background:var(--pap);color:var(--enk);
 font:16px/1.55 "Iowan Old Style",Palatino,"Palatino Linotype",Georgia,serif}
header{position:sticky;top:0;background:var(--pap);border-bottom:1px solid var(--lin);
 padding:14px 20px 12px;z-index:9}
/* Le bouton de telechargement s'ancre en haut a droite du titre. Sur ecran
   etroit il perd son texte et ne garde que l'icone : la barre de recherche a
   besoin de toute la largeur. */
.tito{display:flex;align-items:flex-start;gap:12px;justify-content:space-between}
.dl{flex:none;display:inline-flex;align-items:center;gap:6px;text-decoration:none;
 border:1px solid var(--lin);border-radius:7px;padding:6px 11px;color:var(--acc);
 background:var(--pap);font-size:13px;font-weight:600;white-space:nowrap;
 transition:background .12s,border-color .12s}
.dl:hover{background:var(--lin);border-color:var(--acc)}
.dl svg{display:block;width:15px;height:15px;stroke:currentColor;fill:none;
 stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
@media (max-width:560px){.dl span{display:none}.dl{padding:7px 9px}}
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
.simb{color:var(--sub)}
.simb i{font-style:italic}
.simb b{font-weight:600;color:var(--enk);font-size:14px}
.subvorto{margin:3px 0 3px 16px;text-indent:-10px;line-height:1.45}
.subvorto>b{color:var(--acc)}
.subvorto .lin{color:var(--sub);font-size:11.5px;margin-left:6px;letter-spacing:.03em}
.subvorto::before{content:"\u25b8";color:var(--acc);margin-right:5px}
.meta{margin-top:5px;font-size:11.5px;color:var(--sub);font-family:system-ui,sans-serif;
 display:flex;gap:9px;flex-wrap:wrap}
.dr{color:var(--flag)}
mark{background:rgba(214,160,106,.34);color:inherit;border-radius:2px}
</style>
<header>
<div class="tito">
<h1>Dicionario de la 10.000 radiki di la linguo universala Ido</h1>
<a class="dl" href="dicionario.pdf" download title="Deskargar la dicionario (PDF)">
<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"/><path d="M7 11l5 5 5-5"/><path d="M4 20h16"/></svg><span>Deskargar</span></a>
</div>
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
// L'edition depose deux bornes invisibles autour de ce que l'auteur avait
// souligne — domaine, mot cite, nom scientifique. On les rend en italique.
// Le surlignage de la recherche s'applique morceau par morceau, sinon il
// couperait une balise en deux.
// Tout le texte d'un article, bornes otees : c'est la-dessus que porte la
// recherche dans les definitions. On le calcule une fois par article.
function texto(e){
 if(e._t===undefined) e._t=(e.b||[]).map(b=>b.t+' '+(b.u||[]).map(
   x=>x.k+' '+x.q+' '+x.t).join(' ')).join(' ').replace(/[\ue000\ue001]/g,'').toLowerCase();
 return e._t;}
function korpo(t,r){
 if(t.indexOf('\ue000')<0){
  // Aucune borne : la parenthese de tete reste un qualificatif a marquer.
  // Une parenthese d'une seule lettre ou d'un seul chiffre est un numero
  // d'enumeration — « (a) », « (1) » —, non un qualificatif.
  const m=t.match(/^((?:\((?![a-zA-Z0-9]\))[^()]{1,120}\)\s*)+)/);
  // Formule chimique : l'italique la couperait de son indice.
  const kem=m&&(/[0-9\u2080-\u2089]/.test(m[1])||/^[\u2080-\u2089]/.test(t.slice(m[0].length)));
  return (m&&!kem)?'<i>'+surl(m[1].trim(),r)+'</i> '+surl(t.slice(m[0].length),r):surl(t,r);}
 let h='',dedans=false;
 t.split(/[\ue000\ue001]/).forEach((p,i)=>{
  if(!p){dedans=!dedans;return;}
  h+=dedans?'<i>'+surl(p,r)+'</i>':surl(p,r); dedans=!dedans;});
 return h;}
function rendi(e,r){
 // Emprunt cite : chevrons a l'affichage seulement. La recherche porte sur
 // le mot nu, sinon « amen » ne se trouverait plus.
 let h='<article><span class="ved">'+(e.c?'\u00ab\u00a0':'')+surl(e.v,r)+(e.c?'\u00a0\u00bb':'')+'</span>';
 if(e.f)h+='<span class="fako">('+esc(e.f)+')</span>';
 // La parenthese de tete d'un sens est un qualificatif, de meme nature que le
 // domaine de l'article : elle prend l'italique comme lui.
 const B=e.b||[];
 B.forEach((b,i)=>{
  // Un sens sans corps propre porte son numero sur sa premiere sous-entree,
  // plutot que seul sur une ligne vide.
  let num=(B.length>1)?(i+1):0;
  if(b.t||!(b.u&&b.u.length)){
   h+='<p class="senco">'+(num?'<b>'+num+'.</b>':'')+korpo(b.t,r)+'</p>'; num=0;}
  (b.u||[]).forEach(x=>{h+='<p class="subvorto">'+(num?'<b>'+num+'.</b> ':'')
   +'<b>'+surl(x.k,r)+'</b>'+(x.q?' <i>('+esc(x.q)+')</i>':'')+' '+korpo(x.t,r)
   +(x.n&&x.n.length?'<span class="lin">'+esc(x.n.join(', '))+'</span>':'')+'</p>';
   num=0;});});
 if(e.l&&e.l.length)h+='<p class="senco lat">L. '+esc(e.l.join('; '))+'</p>';
 // Le symbole chimique : une etiquette, comme le nom latin. Le livre l'ecrivait
 // de dix facons — avec ou sans tiret, « kemiala » ou « kem. », majuscule ou
 // non, parfois en incise ; il ne s'ecrit plus que d'une.
 if(e.y)h+='<p class="senco simb"><i>Simb. kem.</i> <b>'+esc(e.y)+'</b></p>';
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
 // Les locutions sont des mots qu'on cherche, au meme titre que la vedette :
 // « voco aktiva », « protestanto ». Sans cela elles ne se trouvaient qu'au
 // rang des definitions, tout en bas de la liste.
 const fs=formi(e.v).concat((e.b||[]).flatMap(b=>(b.u||[]).map(x=>x.k.toLowerCase())));
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
 if(texto(e).includes(r))return 5;
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
    D=[{"v":e['vedetto'],"f":e['fako'],"l":e['latina'],
        "b":[{"t":b.get('teksto_k') or b.get('teksto') or '',
              "u":[{"q":x.get('fako') or '',"k":x['loko'],
                    "t":x.get('teksto_k') or x.get('teksto') or '',
                    **({"n":x['lingui']} if x.get('lingui') else {})}
                   for x in (b.get('sub') or [])]}
             for b in (e.get('strukt') or [])],
        "n":e['lingui'],"p":e['pagino'],"g":e['ligno'],"d":e['drapeli'],
        **({"y":e['simbolo']} if e.get('simbolo') else {}),
        **({"c":1} if e.get('citita') else {})} for e in ent]
    s=GABARITO.replace("__DATA__", json.dumps(D, ensure_ascii=False, separators=(',',':')))
    s=s.replace("__N__", f"{len(ent)} ")
    # index.html, e ne dicionario.html : la pagino publikigesas tale quale sur
    # GitHub Pages, ube « index.html » esas la nomo qua sequesas automate.
    open(f"{SORT}/index.html","w",encoding='utf-8').write(s)
    return os.path.getsize(f"{SORT}/index.html")

if __name__=="__main__":
    ent=charger(); tsv(ent); n=html_edition(ent)
    print(len(ent),"enregistrements ; HTML", round(n/1e6,2),"Mo")
    print("a verifier :", sum(1 for e in ent if e['drapeli']))
