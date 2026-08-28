# Camera Monitoring with Zabbix, Python and Telegram

Projeto de monitoramento de câmeras IP usando **Zabbix**, **Python** e **Telegram Bot API**.

A ideia deste repositório é apresentar a parte de automação do projeto sem expor informações internas da infraestrutura.

## O que foi automatizado

- Monitoramento ICMP e TCP das câmeras
- Alertas de indisponibilidade e recuperação via Telegram
- Importação em massa de hosts no Zabbix via Python
- Leitura de inventário a partir de planilha Excel
- Validação de duplicidade por nome e IP
- Aplicação automática de grupo, templates, tags e macro de porta
- Dry run antes da criação real
- Auditoria do estado das câmeras

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

Os scripts usam variáveis de ambiente para evitar credenciais no código.

```bash
export ZABBIX_URL="https://zabbix.example.com/api_jsonrpc.php"

read -s ZABBIX_TOKEN
export ZABBIX_TOKEN
```

Não publique tokens, senhas, IPs internos reais ou IDs sensíveis.

## Formato da planilha

As linhas devem seguir o formato:

```text
numero | nome | ip | porta | grupo
```

Exemplo:

```text
1 | Camera Entrada Principal | 10.10.20.21 | 37777 | CAM-01
2 | Camera Recepcao | 10.10.20.22 | 80 | CAM-01
```

## Dry run

O dry run consulta o Zabbix, verifica conflitos e mostra quais hosts seriam criados.

```bash
python scripts/dry_run.py \
  --excel cameras.xlsx \
  --sheet CAM-01 \
  --group-name "Cameras/CAM-01"
```

Nenhum host é criado ou alterado.

## Importação real

```bash
python scripts/import_cameras.py \
  --excel cameras.xlsx \
  --sheet CAM-01 \
  --group-id 123 \
  --server-tag CAM-01 \
  --template-tcp-id 456 \
  --template-icmp-id 789
```

Antes de qualquer criação, o script exige a confirmação:

```text
IMPORTAR
```

## Auditoria

Configure os grupos por variável de ambiente:

```bash
export CAMERA_GROUPS='{"CAM-01":"123","CAM-02":"124"}'
```

Depois execute:

```bash
python scripts/audit_cameras.py
```

Os hosts são classificados como:

- `OK`
- `TCP_FALHA`
- `OFFLINE`
- `ESTRANHO`
- `SEM_DADOS`

## Observação

Os scripts públicos foram adaptados a partir dos scripts usados no ambiente real. Endereços, IDs e outros detalhes internos foram substituídos por parâmetros e exemplos genéricos.
