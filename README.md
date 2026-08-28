# Camera Monitoring with Zabbix, Python and Telegram

Projeto de monitoramento de câmeras IP usando **Zabbix**, **Python automation** e **Telegram Bot API**.

## Recursos
- Monitoramento ICMP e TCP
- Alertas OFFLINE/ONLINE via Telegram
- Cadastro em massa via Python + Zabbix API
- Importação por Excel
- Prevenção de duplicidade por nome/IP
- Aplicação automática de grupos, templates, tags e macros
- Dry run antes da criação real
- Auditoria de câmeras

## Estrutura
```text
camera-monitoring-zabbix/
├── README.md
├── requirements.txt
├── .gitignore
└── scripts/
    ├── import_cameras.py
    ├── dry_run.py
    └── audit_cameras.py
```

## Segurança
Os scripts usam variáveis de ambiente. Não publique tokens, senhas, IPs internos reais ou IDs sensíveis.

```bash
export ZABBIX_URL="https://zabbix.example.com/api_jsonrpc.php"
read -s ZABBIX_TOKEN
export ZABBIX_TOKEN
```

## Planilha esperada
Colunas:
```text
numero | nome | ip | porta | grupo
```

## Dry run
```bash
python scripts/dry_run.py --excel cameras.xlsx --sheet CAM-01 --group-name "Cameras/CAM-01"
```

## Importação real
```bash
python scripts/import_cameras.py   --excel cameras.xlsx   --sheet CAM-01   --group-id 123   --server-tag CAM-01   --template-tcp-id 456   --template-icmp-id 789
```

## Auditoria
```bash
export CAMERA_GROUPS='{"CAM-01":"123","CAM-02":"124"}'
python scripts/audit_cameras.py
```

Estados possíveis: `OK`, `TCP_FALHA`, `OFFLINE`, `ESTRANHO`, `SEM_DADOS`.

## Objetivo
Apresentar a automação e integração do projeto sem expor informações internas da infraestrutura.
