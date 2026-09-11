import json, sys, os
import requests
BASE="http://localhost:8000/api"
S=json.load(open("/Users/siva/tax shield/tax-shield/tests/taxshield_persona_test_cases.json"))["test_suite"]["test_cases"]
# tax calc mirror of engine
def liability(t):
    if t<=250000: return 0
    if t<=500000: return (t-250000)*0.05
    if t<=750000: return 12500+(t-500000)*0.10
    if t<=1000000: return 37500+(t-750000)*0.15
    if t<=1250000: return 75000+(t-1000000)*0.20
    if t<=1500000: return 125000+(t-1250000)*0.25
    return 187500+(t-1500000)*0.30
fails=[]
def check(cond,msg):
    print(("PASS " if cond else "FAIL ")+msg)
    if not cond: fails.append(msg)
# persona transaction builders (consistent with JSON totals)
import datetime
def tx(date,desc,amt,ttype,cat,src=""):
    return {"date":date,"description":desc,"amount":amt,"transaction_type":ttype,"category":cat,"source":src}
BUILD={
 "PERSONA_001":[tx("2024-06-01","Salary H1",450000,"income","salary","Employer")]+[tx("2024-12-01","Salary H2",450000,"income","salary","Employer")]+[tx("2024-09-01","Bank interest",25000,"income","bank_interest","Bank")],
 "PERSONA_002":[tx("2024-06-01","Salary",600000,"income","salary","Employer"),tx("2024-08-01","Rental",240000,"income","rental","Tenant"),tx("2024-11-10","MF redemption gain",80000,"income","capital_gains","MF"),tx("2024-09-01","Bank interest",30000,"income","bank_interest","Bank"),tx("2024-10-01","Dividends",20000,"income","dividends","Equity")],
 "PERSONA_003":[tx("2024-07-01","Business receipts H1",1400000,"income","business","Business"),tx("2024-12-01","Business receipts H2",1400000,"income","business","Business"),tx("2024-08-01","Rental",600000,"income","rental","Tenant"),tx("2024-12-20","Equity sale gain",350000,"income","capital_gains","Broker"),tx("2024-09-01","Bank interest",75000,"income","interest" if False else "bank_interest","Bank"),tx("2024-10-01","Dividends",50000,"income","dividends","Equity")],
}
INV={
 "PERSONA_001":[{"name":"PPF FY 2024-25","investment_type":"ppf","category":"retirement","purchase_date":"2024-04-15","purchase_value":100000,"amount":100000}],
 "PERSONA_002":[{"name":"SBI Bluechip Fund","investment_type":"mutual_fund","purchase_date":"2022-05-01","purchase_value":200000,"sale_date":"2024-11-10","sale_value":280000,"gain_loss":80000,"amount":200000}],
 "PERSONA_003":[{"name":"Listed Equity Portfolio","investment_type":"stocks","purchase_date":"2021-08-01","purchase_value":500000,"sale_date":"2024-12-20","sale_value":850000,"gain_loss":350000,"amount":500000}],
}
DED={
 "PERSONA_001":[{"category":"retirement","amount":100000,"verification_status":"complete","description":"PPF","financial_year":"2024-25"},{"category":"insurance","amount":50000,"verification_status":"complete","description":"ELSS","financial_year":"2024-25"},{"category":"medical","amount":25000,"verification_status":"complete","description":"Health insurance","financial_year":"2024-25"}],
 "PERSONA_002":[{"category":"insurance","amount":60000,"verification_status":"needs_review","description":"Term+ELSS","financial_year":"2024-25"},{"category":"retirement","amount":40000,"verification_status":"complete","description":"PPF","financial_year":"2024-25"}],
 "PERSONA_003":[{"category":"retirement","amount":150000,"verification_status":"complete","description":"80C","financial_year":"2024-25"},{"category":"loan_interest","amount":100000,"verification_status":"needs_review","description":"Biz loan int","financial_year":"2024-25"}],
}
import time
ts=str(int(time.time()))
for i,c in enumerate(S):
    pid=c["id"]; email=f"{c['profile']['email_prefix']}_{ts}@example.com"
    print(f"\n=== {pid} {c['name']} ({email}) ===")
    r=requests.post(f"{BASE}/register",json={"email":email,"name":c['profile']['name'],"password":"Pass1234!"})
    check(r.status_code==200,f"{pid} register 200 got {r.status_code}")
    tok=r.json().get("access_token","")
    check(bool(tok),f"{pid} token issued")
    H={"Authorization":f"Bearer {tok}"}
    # negative: invalid login
    r2=requests.post(f"{BASE}/login",json={"email":email,"password":"WRONG"})
    check(r2.status_code==401,f"{pid} invalid login 401 got {r2.status_code}")
    # unauth access
    r3=requests.get(f"{BASE}/transactions")
    check(r3.status_code in (401,403),f"{pid} unauth blocked got {r3.status_code}")
    # create transactions
    for t in BUILD[pid]:
        rr=requests.post(f"{BASE}/transactions",json=t,headers=H)
        if rr.status_code!=200: print("  TX ERR",rr.status_code,rr.text[:200]); check(False,f"{pid} tx create")
    check(True,f"{pid} {len(BUILD[pid])} transactions created")
    for inv in INV[pid]:
        rr=requests.post(f"{BASE}/investments",json=inv,headers=H)
        if rr.status_code!=200: print("  INV ERR",rr.status_code,rr.text[:200])
    for d in DED[pid]:
        rr=requests.post(f"{BASE}/deductions",json=d,headers=H)
        if rr.status_code!=200: print("  DED ERR",rr.status_code,rr.text[:300])
    # negative: negative amount? (engine may accept; just record)
    rn=requests.post(f"{BASE}/transactions",json=tx("2024-01-01","Bad",-100,"income","salary"),headers=H)
    print(f"  negative-amount response: {rn.status_code}")
    if rn.status_code==200:
        # cleanup: delete it
        try:
            alltx=requests.get(f"{BASE}/transactions",headers=H).json()
            bad=[t for t in alltx if t.get("description")=="Bad"]
            for b in bad:
                bid=b.get("_id") or b.get("id")
                requests.delete(f"{BASE}/transactions/{bid}",headers=H)
        except Exception as e: print("  cleanup err",e)
    # dashboard
    dash=requests.get(f"{BASE}/dashboard",headers=H).json()
    exp=c["expected_results"]
    print(f"  dashboard: income={dash['total_income']} taxable={dash['taxable_income']} liability={dash['estimated_liability']} score={dash['readiness_score']}")
    check(abs(dash["total_income"]-exp["income_total"])<1,f"{pid} income_total {dash['total_income']}=={exp['income_total']}")
    # taxable uses only COMPLETE deductions
    check(abs(dash["taxable_income"]-exp["taxable_income"])<1,f"{pid} taxable {dash['taxable_income']}=={exp['taxable_income']}")
    check(abs(dash["estimated_liability"]-exp["tax_liability"])<1,f"{pid} liability {dash['estimated_liability']}=={exp['tax_liability']}")
    rd=requests.get(f"{BASE}/readiness-score",headers=H).json()
    print(f"  readiness: {rd['score']} breakdown={rd['breakdown']}")
    check(0<=rd["score"]<=100,f"{pid} readiness in range")
    # cross-layer: dashboard readiness == readiness endpoint
    check(dash["readiness_score"]==rd["score"],f"{pid} cross-layer readiness consistent")
    ob=requests.get(f"{BASE}/obligations",headers=H).json()
    dl=requests.get(f"{BASE}/deadlines",headers=H).json()
    print(f"  obligations={len(ob)} deadlines={len(dl)}")
    check(len(dl)>=1,f"{pid} deadlines generated")
    # readiness sensitivity: add missing-doc high-risk tx -> score should not increase
    s0=rd["score"]
    requests.post(f"{BASE}/transactions",json=tx("2024-11-01","Freelance no-doc",90000,"income","freelance","ClientX"),headers=H)
    rd2=requests.get(f"{BASE}/readiness-score",headers=H).json()
    print(f"  sensitivity: score {s0} -> {rd2['score']} after risky freelance w/o doc")
    check(rd2["score"]<=s0,f"{pid} readiness decreases/stays on new risk")
    # cleanup risky tx
    try:
        alltx=requests.get(f"{BASE}/transactions",headers=H).json()
        for b in [t for t in alltx if t.get("description")=="Freelance no-doc"]:
            bid=b.get("_id") or b.get("id")
            requests.delete(f"{BASE}/transactions/{bid}",headers=H)
    except Exception as e: print("  cleanup2 err",e)
    # scenarios
    sA=requests.post(f"{BASE}/scenarios",json={"name":"Current","estimated_income":exp["income_total"],"estimated_deductions":exp["deductions_verified_total"],"estimated_liability":exp["tax_liability"]},headers=H).json()
    sB=requests.post(f"{BASE}/scenarios",json={"name":"Alt +50k deduct","estimated_income":exp["income_total"],"estimated_deductions":exp["deductions_verified_total"]+50000,"estimated_liability":liability(exp["taxable_income"]-50000)},headers=H).json()
    ids=[sA.get("_id") or sA.get("id"), sB.get("_id") or sB.get("id")]
    cmp=requests.post(f"{BASE}/scenarios/compare",json={"scenario_ids":ids},headers=H)
    check(cmp.status_code==200,f"{pid} scenario compare 200 got {cmp.status_code}")
    # re-fetch (obligation ids regenerate on re-analysis)
    ob=requests.get(f"{BASE}/obligations",headers=H).json()
    dl=requests.get(f"{BASE}/deadlines",headers=H).json()
    # PATCH obligation + deadline via body form (frontend compat)
    if ob:
        oid=ob[0].get("_id") or ob[0].get("id")
        pr=requests.patch(f"{BASE}/obligations/{oid}",json={"status":"completed"},headers=H)
        check(pr.status_code==200,f"{pid} patch obligation body-form 200 got {pr.status_code}")
    if dl:
        did=dl[0].get("_id") or dl[0].get("id")
        pr=requests.patch(f"{BASE}/deadlines/{did}",json={"is_completed":True},headers=H)
        check(pr.status_code==200,f"{pid} patch deadline body-form 200 got {pr.status_code}")
    # store token for isolation test
    c["_tok"]=tok
# isolation: user1 cannot read user2 data via cross token tamper (obligation id from p1 with p2 token)
try:
    print("\n=== isolation ===")
    t1=S[0]["_tok"]; t2=S[1]["_tok"]
    ob1=requests.get(f"{BASE}/obligations",headers={"Authorization":f"Bearer {t1}"}).json()
    if ob1:
        oid=ob1[0].get("_id") or ob1[0].get("id")
        pr=requests.patch(f"{BASE}/obligations/{oid}",json={"status":"completed"},headers={"Authorization":f"Bearer {t2}"})
        check(pr.status_code==404,f"cross-user patch blocked (404) got {pr.status_code}")
    else: print("  no obligations for isolation test (ok if p1 clean)")
except Exception as e: print("isolation err",e); fails.append("isolation err")
print(f"\nTOTAL FAILS: {len(fails)}")
for f in fails: print(" -",f)
sys.exit(1 if fails else 0)
