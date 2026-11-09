import json,re,time,urllib.request,urllib.parse,difflib,sys,os
UA={'User-Agent':'pineau-rl-study/1.0'}
def get(u,t=60): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t).read()
S=json.load(open(sys.argv[1])); out=sys.argv[2]
for r in S:
    f=f"{out}/{r['id']}.pdf"
    if os.path.exists(f) and os.path.getsize(f)>20000: r['pdf']=f; continue
    src=None
    try:
        if r.get('pdf_url') or 'proceedings.iclr.cc' in r['url'] or 'papers.nips.cc' in r['url'] or 'proceedings.mlr.press' in r['url']:
            p=r.get('pdf_url') or r['url'].replace('/hash/','/file/').replace('-Abstract-Conference.html','-Paper-Conference.pdf')
            open(f,'wb').write(get(p)); src=p
        else:
            words=re.sub(r'[^A-Za-z0-9 ]',' ',r['title']).split()
            q='+AND+'.join('ti:'+urllib.parse.quote(w) for w in words if len(w)>3)[:900]
            x=get('http://export.arxiv.org/api/query?search_query='+q+'&max_results=5').decode()
            best=None
            for eid,tt in re.findall(r'<entry>.*?<id>(.*?)</id>.*?<title>(.*?)</title>',x,re.S):
                sc=difflib.SequenceMatcher(None,' '.join(tt.split()).lower(),r['title'].lower()).ratio()
                if sc>0.85 and (not best or sc>best[0]): best=(sc,eid)
            if best:
                p=best[1].replace('/abs/','/pdf/'); open(f,'wb').write(get(p)); src=p
            time.sleep(3)
    except Exception as e: print('ERR',r['id'],e)
    if src: r['pdf']=f; r['pdf_src']=src
    print(r['id'],'OK' if src else 'MISSING',r['title'][:70],flush=True)
json.dump(S,open(sys.argv[1],'w'),indent=1,ensure_ascii=False)
