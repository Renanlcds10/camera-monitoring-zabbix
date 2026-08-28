#!/usr/bin/env python3

import json
import os
import sys
from collections import defaultdict

import requests


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ZABBIX_URL = os.environ.get("ZABBIX_URL")
TOKEN = os.environ.get("ZABBIX_TOKEN")

GROUPS_JSON = os.environ.get(
    "CAMERA_GROUPS",
    "{}"
)

PORT_MACRO = os.environ.get(
    "CAMERA_PORT_MACRO",
    "{$DGUARD.PORT}"
)

if not ZABBIX_URL:
    print("ERRO: variável ZABBIX_URL não encontrada.")
    sys.exit(1)

if not TOKEN:
    print("ERRO: variável ZABBIX_TOKEN não encontrada.")
    sys.exit(1)

try:
    GRUPOS = json.loads(
        GROUPS_JSON
    )

except json.JSONDecodeError:
    print(
        "ERRO: CAMERA_GROUPS precisa ser um JSON válido."
    )
    sys.exit(1)

if not GRUPOS:
    print("ERRO: variável CAMERA_GROUPS não configurada.")
    print()
    print(
        'Exemplo: export CAMERA_GROUPS='
        '\'{"CAM-01":"123","CAM-02":"124"}\''
    )
    sys.exit(1)


# ============================================================
# API
# ============================================================

def api(method, params):

    response = requests.post(
        ZABBIX_URL,
        headers={
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {TOKEN}",
        },
        json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(
            f"Erro Zabbix API: {data['error']}"
        )

    return data["result"]


# ============================================================
# DESCOBRIR PORTA
# ============================================================

def descobrir_porta(macros):

    for macro in macros:

        if macro.get("macro") == PORT_MACRO:

            return macro.get(
                "value",
                "?"
            )

    return "?"


# ============================================================
# CLASSIFICAR STATUS
# ============================================================

def classificar(icmp, tcp):

    if icmp == "1" and tcp == "1":
        return "OK"

    if icmp == "1" and tcp == "0":
        return "TCP_FALHA"

    if icmp == "0" and tcp == "0":
        return "OFFLINE"

    if icmp == "0" and tcp == "1":
        return "ESTRANHO"

    return "SEM_DADOS"


# ============================================================
# ESTRUTURAS DE RESULTADO
# ============================================================

resultado = []

resumo_cam = defaultdict(
    lambda: {
        "total": 0,
        "ok": 0,
        "tcp": 0,
        "offline": 0,
        "estranho": 0,
        "sem_dados": 0,
    }
)


# ============================================================
# INÍCIO
# ============================================================

print()
print("=" * 70)
print("AUDITORIA DAS CÂMERAS")
print("=" * 70)
print()


# ============================================================
# CONSULTAR GRUPOS
# ============================================================

for cam, groupid in GRUPOS.items():

    print(f"Consultando {cam}...")

    hosts = api(
        "host.get",
        {
            "groupids": [groupid],
            "output": [
                "hostid",
                "host",
                "name"
            ],
            "selectInterfaces": ["ip"],
            "selectMacros": [
                "macro",
                "value"
            ],
        },
    )

    for host in hosts:

        hostid = host["hostid"]
        nome = host["name"]

        interfaces = host.get(
            "interfaces",
            []
        )

        if interfaces:
            ip = interfaces[0].get(
                "ip",
                "?"
            )
        else:
            ip = "?"

        porta = descobrir_porta(
            host.get(
                "macros",
                []
            )
        )

        items = api(
            "item.get",
            {
                "hostids": [hostid],
                "output": [
                    "itemid",
                    "name",
                    "key_",
                    "lastvalue",
                    "lastclock",
                ],
            },
        )

        icmp = None
        tcp = None

        for item in items:

            key = item.get(
                "key_",
                ""
            )

            if key == "icmpping":
                icmp = item.get(
                    "lastvalue"
                )

            if key.startswith(
                "net.tcp.service"
            ):
                tcp = item.get(
                    "lastvalue"
                )

        status = classificar(
            icmp,
            tcp
        )

        resultado.append(
            {
                "cam": cam,
                "nome": nome,
                "ip": ip,
                "porta": porta,
                "icmp": icmp,
                "tcp": tcp,
                "status": status,
            }
        )

        r = resumo_cam[cam]
        r["total"] += 1

        if status == "OK":
            r["ok"] += 1

        elif status == "TCP_FALHA":
            r["tcp"] += 1

        elif status == "OFFLINE":
            r["offline"] += 1

        elif status == "ESTRANHO":
            r["estranho"] += 1

        else:
            r["sem_dados"] += 1


# ============================================================
# RESUMO POR GRUPO
# ============================================================

print()
print("=" * 70)
print("RESUMO POR GRUPO")
print("=" * 70)

for cam in GRUPOS:

    r = resumo_cam[cam]

    print()
    print(cam)
    print("-" * 40)

    print(f"Total:              {r['total']}")
    print(f"OK:                 {r['ok']}")
    print(f"TCP falhando:       {r['tcp']}")
    print(f"Offline:            {r['offline']}")
    print(f"Estranho:           {r['estranho']}")
    print(f"Sem dados:          {r['sem_dados']}")


# ============================================================
# RESUMO GERAL
# ============================================================

total = len(resultado)

ok = sum(
    x["status"] == "OK"
    for x in resultado
)

tcp_falha = sum(
    x["status"] == "TCP_FALHA"
    for x in resultado
)

offline = sum(
    x["status"] == "OFFLINE"
    for x in resultado
)

estranho = sum(
    x["status"] == "ESTRANHO"
    for x in resultado
)

sem_dados = sum(
    x["status"] == "SEM_DADOS"
    for x in resultado
)

print()
print("=" * 70)
print("RESUMO GERAL")
print("=" * 70)

print(f"Total monitorado:   {total}")
print(f"OK:                 {ok}")
print(f"TCP falhando:       {tcp_falha}")
print(f"Offline:            {offline}")
print(f"Estranho:           {estranho}")
print(f"Sem dados:          {sem_dados}")


# ============================================================
# CÂMERAS COM PROBLEMA
# ============================================================

print()
print("=" * 70)
print("CÂMERAS COM PROBLEMA")
print("=" * 70)

problemas = [
    x
    for x in resultado
    if x["status"] != "OK"
]

if not problemas:

    print()
    print("Nenhum problema encontrado!")

else:

    for camera in problemas:

        print()
        print(
            f"[{camera['status']}] "
            f"{camera['cam']} | "
            f"{camera['nome']}"
        )

        print(
            f"    IP: {camera['ip']} | "
            f"Porta: {camera['porta']} | "
            f"ICMP: {camera['icmp']} | "
            f"TCP: {camera['tcp']}"
        )


print()
print("=" * 70)
print("AUDITORIA FINALIZADA")
print("=" * 70)
