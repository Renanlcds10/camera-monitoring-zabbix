# Monitoramento de Câmeras IP com Zabbix, Python e Telegram

Projeto desenvolvido para centralizar o monitoramento das câmeras IP de uma infraestrutura que possui atualmente **178 câmeras**, distribuídas entre diferentes servidores/grupos.

O objetivo foi facilitar a identificação de câmeras offline ou com problema de comunicação, evitando a necessidade de verificar manualmente cada equipamento no sistema de CFTV.

Para isso utilizei **Zabbix**, automações em **Python** e integração com **Telegram** para envio dos alertas para a equipe técnica.

## O problema

O ambiente possui uma quantidade grande de câmeras IP e verificar manualmente se cada câmera estava funcionando acabava sendo trabalhoso.

Além disso, uma câmera podia responder na rede, mas o serviço utilizado pelo sistema de monitoramento de vídeo não estar disponível.

Por isso decidi monitorar dois pontos diferentes:

- comunicação com o equipamento através de ICMP (ping);
- disponibilidade do serviço através de uma conexão TCP na porta utilizada pela câmera.

Dessa forma consigo diferenciar uma câmera totalmente offline de uma câmera que ainda está na rede, mas está com problema no serviço TCP.

## Como ficou o monitoramento

Atualmente o projeto monitora **178 câmeras IP**, separadas em 5 grupos:

| Grupo | Quantidade |
|------|-----------:|
| CAM-11 | 40 |
| CAM-12 | 47 |
| CAM-13 | 44 |
| CAM-14 | 19 |
| CAM-15 | 28 |
| **Total** | **178** |

Cada câmera possui monitoramento de:

- ICMP;
- porta TCP;
- status ONLINE/OFFLINE;
- grupo/servidor responsável;
- tags para organização dentro do Zabbix.

Algumas câmeras utilizam portas TCP diferentes, então a porta é configurada individualmente através de uma macro no host.

## Arquitetura

O funcionamento ficou basicamente assim:

```text
                  +------------------+
                  |    Câmeras IP    |
                  +--------+---------+
                           |
                      ICMP + TCP
                           |
                           v
                  +------------------+
                  |      Zabbix      |
                  |                  |
                  | Items / Triggers |
                  +----+--------+----+
                       |        ^
             problema  |        | recuperação
                       v        |
                  +------------------+
                  |     Telegram     |
                  +--------+---------+
                           |
                           v
                    Equipe técnica


        +----------------------------+
        |           Python           |
        |                            |
        | Importação em massa        |
        | Dry Run                    |
        | Auditoria                  |
        +-------------+--------------+
                      |
                 Zabbix API
                      |
                      v
                   Zabbix
```

## Automações em Python

Como eram muitas câmeras para cadastrar manualmente, utilizei Python para automatizar parte do processo através da API do Zabbix.

Os scripts deste repositório representam essa parte do projeto.

### `import_cameras.py`

Responsável pela criação dos hosts no Zabbix a partir de uma planilha Excel.

Antes de criar cada host o script verifica se já existe:

- uma câmera com o mesmo nome;
- uma câmera utilizando o mesmo IP.

Na criação são configurados automaticamente:

- grupo;
- templates;
- interface/IP;
- tags;
- macro com a porta TCP.

Antes da importação real o script também exige uma confirmação manual digitando `IMPORTAR`.

### `dry_run.py`

Criei esse script para validar a planilha antes de fazer qualquer alteração no Zabbix.

Ele consulta os hosts existentes e mostra:

- quais câmeras seriam criadas;
- quais já existem;
- possíveis conflitos de IP.

No final apresenta um resumo e **não cria ou altera nenhum host**.

Foi uma forma de conferir os dados antes de executar a importação real.

### `audit_cameras.py`

Depois do cadastro das câmeras, criei também um script para consultar o estado dos equipamentos através da API do Zabbix.

A auditoria verifica o último resultado do ICMP e TCP e classifica cada câmera como:

| Status | Situação |
|--------|----------|
| `OK` | ICMP e TCP funcionando |
| `TCP_FALHA` | responde ping, mas a porta TCP não responde |
| `OFFLINE` | ICMP e TCP indisponíveis |
| `ESTRANHO` | TCP responde mesmo sem resposta ICMP |
| `SEM_DADOS` | ainda não existem dados suficientes |

No final o script apresenta um resumo por grupo, um resumo geral e lista somente as câmeras que precisam de atenção.

## Alertas pelo Telegram

Também configurei o Zabbix para enviar notificações para um grupo no Telegram utilizado pela equipe técnica.

Quando uma câmera fica indisponível, é enviado um alerta contendo informações como:

```text
🚨 CÂMERA OFFLINE

📹 Nome da câmera
🌐 IP: xxx.xxx.xxx.xxx

🔴 Status: OFFLINE
🕐 Detectado: horário
📅 Data: data
```

Quando a comunicação volta, o Zabbix envia outra notificação informando que a câmera está online novamente.

Isso permite que a equipe seja avisada sem precisar ficar acompanhando constantemente a tela do Zabbix.

## Tecnologias utilizadas

- Zabbix
- Python 3
- Zabbix API / JSON-RPC
- Requests
- OpenPyXL
- Telegram Bot API
- ICMP
- TCP/IP
- Excel

## Estrutura do repositório

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

## Executando os scripts

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure o endereço da API:

```bash
export ZABBIX_URL="https://zabbix.example.com/api_jsonrpc.php"
```

O token da API é utilizado através de variável de ambiente e não fica salvo dentro dos scripts:

```bash
read -s ZABBIX_TOKEN
export ZABBIX_TOKEN
```

### Dry Run

Exemplo:

```bash
python scripts/dry_run.py \
  --excel cameras.xlsx \
  --sheet CAM-01 \
  --group-name "Cameras/CAM-01"
```

### Importação

Exemplo:

```bash
python scripts/import_cameras.py \
  --excel cameras.xlsx \
  --sheet CAM-01 \
  --group-id 123 \
  --server-tag CAM-01 \
  --template-tcp-id 456 \
  --template-icmp-id 789
```

### Auditoria

Os grupos podem ser informados através de uma variável de ambiente:

```bash
export CAMERA_GROUPS='{"CAM-01":"123","CAM-02":"124"}'
```

Depois:

```bash
python scripts/audit_cameras.py
```

## Segurança

Como este repositório é público, alguns dados utilizados no ambiente real não estão presentes aqui.

Foram removidos ou substituídos:

- IPs internos;
- token da API;
- IDs reais de grupos e templates;
- caminhos internos do servidor;
- informações específicas da infraestrutura.

Os scripts publicados aqui foram adaptados a partir dos scripts utilizados durante a implantação real.

## Resultado

Com o projeto foi possível centralizar o acompanhamento das **178 câmeras IP** no Zabbix e automatizar boa parte do processo de cadastro e verificação.

Além do monitoramento, os alertas pelo Telegram ajudam a equipe técnica a identificar rapidamente quando uma câmera fica offline e também quando ela volta a funcionar.

O projeto também acabou sendo uma oportunidade de trabalhar na prática com **monitoramento de infraestrutura, redes, Python, APIs e automação**.
