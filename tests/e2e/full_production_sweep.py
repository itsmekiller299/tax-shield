import requests, time, sys
B="http://localhost:8000/api"; F="http://localhost:3000"
P=[]; F_= []
def ck(c,m):
    (P if c else F_).append(m); print(("PASS " if c else "FAIL ")+m)
ts=str(int(time.time())); H={}
# AUTH
r=requests.post(f"{B}/register",json={"email":f"sweep{ts}@t.com","name":"S","password":"Pass1234!","financial_year":"2024-25"})
ck(r.status_code==200,"auth register"); tok=r.json().get("access_token",""); H={"Authorization":f"Bearer {tok}"}
ck(requests.post(f"{B}/register",json={"email":f"sweep{ts}@t.com","name":"S","password":"x"}).status_code==400,"auth duplicate 400")
ck(requests.post(f"{B}/login",json={"email":f"sweep{ts}@t.com","password":"bad"}).status_code==401,"auth invalid 401")
ck(requests.post(f"{B}/login",json={"email":f"sweep{ts}@t.com","password":"Pass1234!"}).status_code==200,"auth login JSON")
ck(requests.get(f"{B}/transactions").status_code==401,"auth unauth 401")
me=requests.get(f"{B}/me",headers=H).json(); ck(me.get("financial_year")=="2024-25","profile FY")
# TRANSACTIONS
t1=requests.post(f"{B}/transactions",json={"date":"2024-06-01","description":"Salary","amount":600000,"transaction_type":"income","category":"salary","source":"Emp"},headers=H)
ck(t1.status_code==200,"tx create")
ck(requests.post(f"{B}/transactions",json={"date":"2024-06-01","description":"Bad","amount":-5,"transaction_type":"income","category":"salary"},headers=H).status_code==422,"tx negative 422")
ck(requests.post(f"{B}/transactions",json={"description":"NoDate","amount":5,"transaction_type":"income","category":"salary"},headers=H).status_code==422,"tx missing-field 422")
b=requests.post(f"{B}/transactions/bulk",json=[{"date":"2024-08-01","description":"Rent","amount":240000,"transaction_type":"income","category":"rental"},{"date":"2024-09-01","description":"Int","amount":30000,"transaction_type":"income","category":"bank_interest"}],headers=H)
ck(b.status_code==200 and b.json()["inserted"]==2,"tx bulk")
txs=requests.get(f"{B}/transactions",headers=H).json(); ck(len(txs)==3,"tx list 3")
divs=[t for t in txs if t.get("description")=="Salary"]
tid=(txs[0].get("_id") or txs[0].get("id"))
ck(requests.delete(f"{B}/transactions/{tid}",headers=H).status_code==200,"tx delete")
ck(len(requests.get(f"{B}/transactions",headers=H).json())==2,"tx delete persisted")
# re-add whatever was deleted to keep downstream totals intact
dt= [t for t in txs if (t.get("_id") or t.get("id"))==tid][0]
requests.post(f"{B}/transactions",json={"date":dt["date"][:10] if isinstance(dt.get("date"),str) else "2024-06-01","description":dt.get("description","Re"),"amount":dt.get("amount",0),"transaction_type":dt.get("transaction_type","income"),"category":dt.get("category","other")},headers=H)
# CSV upload
import io
csvdata="date,description,amount,transaction_type,category,source\n2024-10-01,Div,20000,income,dividends,Eq\n"
ck(requests.post(f"{B}/transactions/upload-csv",files={"file":("t.csv",csvdata)},headers=H).status_code==200,"tx csv upload")
# INVEST/DED
ck(requests.post(f"{B}/investments",json={"name":"MF","investment_type":"mutual_fund","purchase_date":"2022-01-01","purchase_value":200000,"sale_date":"2024-11-01","sale_value":280000,"gain_loss":80000,"amount":200000},headers=H).status_code==200,"inv create")
ck(len(requests.get(f"{B}/investments",headers=H).json())==1,"inv list")
ck(requests.post(f"{B}/deductions",json={"category":"retirement","amount":100000,"verification_status":"complete","financial_year":"2024-25"},headers=H).status_code==200,"ded complete")
ck(requests.post(f"{B}/deductions",json={"category":"insurance","amount":60000,"verification_status":"needs_review","financial_year":"2024-25"},headers=H).status_code==200,"ded review")
# DOCUMENTS
ck(requests.post(f"{B}/documents",files={"file":("a.txt",b"hello")},data={"document_type":"form16","financial_year":"2024-25"},headers=H).status_code==200,"doc upload")
ck(len(requests.get(f"{B}/documents",headers=H).json())==1,"doc list")
# AIS/26AS/RECON
requests.post(f"{B}/ais-records",json={"source":"Emp","income_type":"salary","amount":600000},headers=H)
requests.post(f"{B}/ais-records",json={"source":"Tenant","income_type":"rental","amount":250000},headers=H)
requests.post(f"{B}/form26as-records",json={"source":"Emp","section":"192","amount_paid":600000,"tds":30000},headers=H)
rec=requests.get(f"{B}/reconciliation",headers=H).json()
ck(rec["matched"]==1 and rec["mismatched"]==1,f"recon 1/1 got {rec['matched']}/{rec['mismatched']}")
# TAX detail old+new
d_old=requests.get(f"{B}/tax-detail?regime=old",headers=H).json()
ck(all(k in d_old for k in ("base","rebate","surcharge","cess","total_liability")),"tax-detail components")
ck(d_old["total_liability"]>0,"tax old>0")
d_new=requests.get(f"{B}/tax-detail?regime=new",headers=H).json(); ck(d_new["total_liability"]>=0,"tax new>=0")
# PAYMENTS→dashboard
requests.post(f"{B}/tax-payments",json={"amount":20000,"payment_type":"advance_tax"},headers=H)
ck(requests.post(f"{B}/tax-payments",json={"amount":-5},headers=H).status_code==422,"pay negative 422")
dash=requests.get(f"{B}/dashboard",headers=H).json()
ck(dash["tax_paid"]==20000 and abs(dash["outstanding_tax"]-(dash["estimated_liability"]-20000))<1,"ledger outstanding")
rd0=requests.get(f"{B}/readiness-score",headers=H).json()
ck(dash["readiness_score"]==rd0["score"],"cross-layer readiness")
# OBLIG/DEADLINES/RISKS/ACTIONS/READINESS
ob=requests.get(f"{B}/obligations",headers=H).json(); dl=requests.get(f"{B}/deadlines",headers=H).json()
ck(len(ob)>=3 and len(dl)>=1,f"oblig {len(ob)} deadlines {len(dl)}")
o1={o["title"]:o["_id"] for o in ob}
requests.post(f"{B}/transactions",json={"date":"2024-09-02","description":"X","amount":1000,"transaction_type":"income","category":"dividends"},headers=H)
o2={o["title"]:o["_id"] for o in requests.get(f"{B}/obligations",headers=H).json()}
ck(all(o1[t]==o2[t] for t in o1 if t in o2),"oblig ids stable")
ck(requests.patch(f"{B}/obligations/{o2 and list(o2.values())[0]}",json={"status":"completed"},headers=H).status_code==200,"patch oblig body")
ck(requests.patch(f"{B}/deadlines/{(dl[0].get('_id') or dl[0].get('id'))}",json={"is_completed":True},headers=H).status_code==200,"patch deadline body")
ck(requests.get(f"{B}/risks",headers=H).json()["count"]>=1,"risks")
ck(requests.get(f"{B}/actions",headers=H).json()["count"]>=1,"actions")
rd=requests.get(f"{B}/readiness-score",headers=H).json()
ck(set(("documentation","compliance","reconciliation","tax_accuracy","actionability"))<=set(rd["breakdown"]),"readiness spec keys")
s0=rd["score"]
requests.post(f"{B}/transactions",json={"date":"2024-11-01","description":"FreeNoDoc","amount":90000,"transaction_type":"income","category":"freelance"},headers=H)
ck(requests.get(f"{B}/readiness-score",headers=H).json()["score"]<=s0,"readiness sensitivity")
# SCENARIOS
sA=requests.post(f"{B}/scenarios",json={"name":"Cur","estimated_income":890000,"estimated_deductions":100000,"estimated_liability":50000},headers=H).json()
sB=requests.post(f"{B}/scenarios",json={"name":"Alt","estimated_income":890000,"estimated_deductions":150000,"estimated_liability":40000},headers=H).json()
ids=[sA.get("_id") or sA.get("id"),sB.get("_id") or sB.get("id")]
cmp=requests.post(f"{B}/scenarios/compare",json={"scenario_ids":ids},headers=H)
ck(cmp.status_code==200 and "computed_liability" in cmp.json()["comparison"][0],"scenario compare computed")
# CHAT (12 intents/langs)
chat=[("Why is my readiness score low?","en"),("Enoda score yen low ah irukku?","ta"),("Mera score low kyun hai?","hi"),
 ("Show missing documents","en"),("Enakku enna documents upload pannanum?","ta"),("Show high-risk alerts.","en"),
 ("Show my deadlines.","en"),("Summarize my finances.","en"),("Explain my tax position","en"),("What if I invest 50000?","en"),
 ("Enoda freelance income-ku invoice missing ah irukka?","ta"),("Mera tax readiness score kitna hai?","hi")]
for msg,exp in chat:
    o=requests.post(f"{B}/chat/message",json={"message":msg},headers=H).json()
    ck(o.get("language","").startswith(exp) and o.get("response"),f"chat [{exp}] {msg[:35]}")
f1=requests.post(f"{B}/chat/message",json={"message":"Why is my score low?"},headers=H).json()
f2=requests.post(f"{B}/chat/message",json={"message":"What should I fix first?"},headers=H).json()
ck(f2["intent"]=="EXPLAIN_READINESS","chat context followup")
ck(requests.post(f"{B}/chat/message",json={"message":""},headers=H).status_code==422,"chat empty 422")
ck(len(requests.get(f"{B}/chat/history?limit=5",headers=H).json()["messages"])>0,"chat history")
# VOICE
ck(requests.post(f"{B}/chat/voice/transcribe",json={"transcript":"Enoda score enna?"},headers=H).json()["language"].startswith("ta"),"voice transcribe ta")
ck(requests.post(f"{B}/chat/voice/synthesize",json={"text":"Vanakkam"},headers=H).json()["voice"]=="ta-IN","voice synth ta-IN")
ck(requests.post(f"{B}/chat/voice/transcribe",json={},headers=H).status_code==422,"voice empty 422")
# ISOLATION
r2=requests.post(f"{B}/register",json={"email":f"other{ts}@t.com","name":"O","password":"Pass1234!"}).json()
H2={"Authorization":f"Bearer {r2['access_token']}"}
ck(requests.patch(f"{B}/obligations/{list(o2.values())[0]}",json={"status":"completed"},headers=H2).status_code==404,"isolation 404")
ck(all("Salary" not in m["text"] for m in requests.get(f"{B}/chat/history?limit=50",headers=H2).json()["messages"]),"chat isolation")
# UI routes
for p in ["dashboard","assistant","transactions","obligations","deadlines","documents","scenarios","reports","settings","login","register"]:
    ck(requests.get(f"{F}/{p}",timeout=10).status_code==200,f"ui /{p}")
print(f"\nTOTAL: {len(P)} pass, {len(F_)} fail")
for m in F_: print(" FAIL:",m)
sys.exit(1 if F_ else 0)
