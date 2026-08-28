#!/usr/bin/env python3
import argparse, os, sys, requests
from openpyxl import load_workbook

def args():
    p = argparse.ArgumentParser()
    p.add_argument("--excel", required=True)
    p.add_argument("--sheet", required=True)
    p.add_argument("--group-id", required=True)
    p.add_argument("--server-tag", required=True)
    p.add_argument("--template-tcp-id", required=True)
    p.add_argument("--template-icmp-id", required=True)
    p.add_argument("--port-macro", default="{$DGUARD.PORT}")
    p.add_argument("--host-prefix", default="camera")
    return p.parse_args()

A = args()
URL = os.environ.get("ZABBIX_URL")
TOKEN = os.environ.get("ZABBIX_TOKEN")
if not URL or not TOKEN:
    sys.exit("Defina ZABBIX_URL e ZABBIX_TOKEN.")

def api(method, params):
    r = requests.post(URL, headers={"Content-Type":"application/json-rpc","Authorization":f"Bearer {TOKEN}"},
        json={"jsonrpc":"2.0","method":method,"params":params,"id":1}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]

def main():
    if input("Isso CRIARÁ hosts no Zabbix. Digite IMPORTAR: ") != "IMPORTAR":
        return
    hosts = api("host.get", {"output":["hostid","host","name"],"selectInterfaces":["ip"]})
    nomes, ips = {}, {}
    for h in hosts:
        nomes[h["name"].strip().lower()] = h
        for i in h.get("interfaces", []):
            if i.get("ip"): ips[i["ip"]] = h

    ws = load_workbook(A.excel, data_only=True)[A.sheet]
    criados = ignorados = falhas = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        numero, nome, ip, porta, grupo = row
        if not nome or not ip or not porta: continue
        nome, ip, porta = str(nome).strip(), str(ip).strip(), str(int(porta))

        if nome.lower() in nomes or ip in ips:
            print(f"[IGNORADO] {nome} | {ip}")
            ignorados += 1
            continue

        host_tecnico = f"{A.host_prefix}-{ip.replace('.', '-')}"
        params = {
            "host": host_tecnico,
            "name": nome,
            "groups":[{"groupid":A.group_id}],
            "interfaces":[{"type":1,"main":1,"useip":1,"ip":ip,"dns":"","port":"10050"}],
            "templates":[{"templateid":A.template_tcp_id},{"templateid":A.template_icmp_id}],
            "tags":[
                {"tag":"tipo","value":"camera"},
                {"tag":"sistema","value":"dguard"},
                {"tag":"servidor","value":A.server_tag}
            ],
            "macros":[{"macro":A.port_macro,"value":porta}]
        }
        try:
            result = api("host.create", params)
            hostid = result["hostids"][0]
            print(f"[CRIADO] {nome} | {ip} | hostid={hostid}")
            nomes[nome.lower()] = {"host":host_tecnico,"hostid":hostid}
            ips[ip] = {"host":host_tecnico,"hostid":hostid}
            criados += 1
        except Exception as e:
            print(f"[ERRO] {nome} | {ip} | {e}")
            falhas += 1

    print(f"\nCriados: {criados} | Ignorados: {ignorados} | Falhas: {falhas}")

if __name__ == "__main__":
    main()
