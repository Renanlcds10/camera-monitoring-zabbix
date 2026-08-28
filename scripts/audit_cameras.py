#!/usr/bin/env python3
import json, os, sys, requests
from collections import defaultdict

URL=os.environ.get("ZABBIX_URL")
TOKEN=os.environ.get("ZABBIX_TOKEN")
GROUPS=json.loads(os.environ.get("CAMERA_GROUPS","{}"))
PORT_MACRO=os.environ.get("CAMERA_PORT_MACRO","{$DGUARD.PORT}")

if not URL or not TOKEN or not GROUPS:
    sys.exit("Defina ZABBIX_URL, ZABBIX_TOKEN e CAMERA_GROUPS.")

def api(method,params):
    r=requests.post(URL,headers={"Content-Type":"application/json-rpc","Authorization":f"Bearer {TOKEN}"},
        json={"jsonrpc":"2.0","method":method,"params":params,"id":1},timeout=30)
    r.raise_for_status()
    d=r.json()
    if "error" in d: raise RuntimeError(d["error"])
    return d["result"]

def porta(macros):
    for m in macros:
        if m.get("macro")==PORT_MACRO:
            return m.get("value","?")
    return "?"

def status(icmp,tcp):
    if icmp=="1" and tcp=="1": return "OK"
    if icmp=="1" and tcp=="0": return "TCP_FALHA"
    if icmp=="0" and tcp=="0": return "OFFLINE"
    if icmp=="0" and tcp=="1": return "ESTRANHO"
    return "SEM_DADOS"

res=[]
resumo=defaultdict(lambda:defaultdict(int))

for group_name,group_id in GROUPS.items():
    hosts=api("host.get",{"groupids":[group_id],"output":["hostid","host","name"],
        "selectInterfaces":["ip"],"selectMacros":["macro","value"]})
    for h in hosts:
        ip=h.get("interfaces",[{}])[0].get("ip","?") if h.get("interfaces") else "?"
        items=api("item.get",{"hostids":[h["hostid"]],"output":["key_","lastvalue"]})
        icmp=tcp=None
        for item in items:
            if item.get("key_")=="icmpping": icmp=item.get("lastvalue")
            elif item.get("key_","").startswith("net.tcp.service"): tcp=item.get("lastvalue")
        st=status(icmp,tcp)
        res.append((group_name,h["name"],ip,porta(h.get("macros",[])),icmp,tcp,st))
        resumo[group_name]["total"]+=1
        resumo[group_name][st]+=1

for g in GROUPS:
    print(f"\n{g}: {dict(resumo[g])}")

print("\nCÂMERAS COM PROBLEMA")
for g,n,ip,p,icmp,tcp,st in res:
    if st!="OK":
        print(f"[{st}] {g} | {n} | {ip}:{p} | ICMP={icmp} | TCP={tcp}")
