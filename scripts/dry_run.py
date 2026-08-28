#!/usr/bin/env python3
import argparse, os, sys, requests
from openpyxl import load_workbook

p=argparse.ArgumentParser()
p.add_argument("--excel", required=True)
p.add_argument("--sheet", required=True)
p.add_argument("--group-name", required=True)
A=p.parse_args()

URL=os.environ.get("ZABBIX_URL")
TOKEN=os.environ.get("ZABBIX_TOKEN")
if not URL or not TOKEN:
    sys.exit("Defina ZABBIX_URL e ZABBIX_TOKEN.")

def api(method, params):
    r=requests.post(URL, headers={"Content-Type":"application/json-rpc","Authorization":f"Bearer {TOKEN}"},
        json={"jsonrpc":"2.0","method":method,"params":params,"id":1}, timeout=15)
    r.raise_for_status()
    d=r.json()
    if "error" in d: raise RuntimeError(d["error"])
    return d["result"]

hosts=api("host.get",{"output":["hostid","host","name"],"selectInterfaces":["ip"]})
nomes,ips={},{}
for h in hosts:
    nomes[h["name"].strip().lower()]=h
    for i in h.get("interfaces",[]):
        if i.get("ip"): ips[i["ip"]]=h

ws=load_workbook(A.excel,data_only=True)[A.sheet]
criaria=existentes=conflitos=0
for row in ws.iter_rows(min_row=2,values_only=True):
    numero,nome,ip,porta,grupo=row
    if not nome or not ip: continue
    nome,ip=str(nome).strip(),str(ip).strip()
    if nome.lower() in nomes:
        print(f"[JÁ EXISTE] {nome} | {ip}"); existentes+=1; continue
    if ip in ips:
        print(f"[IP EM USO] {nome} | {ip} | {ips[ip]['host']}"); conflitos+=1; continue
    print(f"[CRIARIA] {nome} | {ip}:{int(porta)} | {A.group_name}")
    criaria+=1

print(f"\nSeriam criadas: {criaria} | Já existem: {existentes} | Conflitos: {conflitos}")
print("Nenhum host foi criado ou alterado.")
