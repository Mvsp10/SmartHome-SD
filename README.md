# SmartHome SD — Casa Inteligente Distribuída

Projeto acadêmico de Sistemas Distribuídos: simulação de uma casa inteligente com sensor de temperatura, MQTT, controladores replicados, middleware HTTP e interface web.

## Arquitetura

- **Sensor:** `sensores/temperatura.py` publica temperaturas simuladas a cada 3 segundos no tópico MQTT `casa/sensores/temperatura`.
- **Réplicas:** três processos `controladores/replica.py` (portas 8101, 8102, 8103) recebem as leituras MQTT e as armazenam em bancos SQLite separados.
- **Middleware:** `middleware/api.py` (porta 8000) consulta as réplicas, exige ao menos duas respostas idênticas para apresentar consenso e encaminha comandos ao ventilador.
- **Atuador:** `atuadores/ventilador_confiavel.py` recebe comandos MQTT, registra IDs executados em SQLite para evitar execução duplicada do mesmo ID e publica confirmações.
- **Cliente:** `cliente/index.html` é servido pelo middleware em `http://127.0.0.1:8000/`.

## Requisitos

- Windows com PowerShell; Python 3.12+; Mosquitto executando localmente na porta 1883.
- Bibliotecas Python em `requirements.txt`.

## Instalação

Abra o PowerShell na pasta `smarthome-sd`:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Inicie o broker Mosquitto antes de executar o projeto. Caso o comando `mosquitto` não esteja no PATH, inicie o serviço pelo Windows ou pela instalação local.

## Execução principal (réplicas, middleware, atuador e sensor)

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar_etapa4.ps1
```

O script abre janelas separadas para os componentes. Aguarde alguns segundos e acesse:

- Painel: http://127.0.0.1:8000/
- Documentação da API: http://127.0.0.1:8000/docs
- Estado/consenso: http://127.0.0.1:8000/estado

**Importante:** não execute `iniciar.ps1` ou `iniciar_etapa3.ps1` ao mesmo tempo que `iniciar_etapa4.ps1`. A Etapa 1/2 é uma demonstração separada, com controlador e atuador antigos.

## Rotas principais

| Rota | Método | Função |
| --- | --- | --- |
| `/` | GET | Interface web |
| `/estado` | GET | Leitura por maioria das réplicas |
| `/comandos/ventilador` | POST | Envia comando `ligar`/`desligar` e aguarda confirmação |
| `http://127.0.0.1:8101/saude` | GET | Verifica a réplica 1 (análoga às outras) |
| `http://127.0.0.1:8101/leituras/ultima` | GET | Última leitura da réplica 1 |

Exemplo de corpo JSON para `POST /comandos/ventilador`: `{"acao":"ligar"}`. É possível fornecer `id` para reenvio idempotente da mesma operação.

## Experimentos demonstráveis

1. **Consenso:** com três réplicas ativas, consultar `/estado` e observar `votos: 3` quando as leituras coincidirem.
2. **Queda de réplica:** fechar a réplica 1 e consultar `/estado` com as duas restantes; o comando HTTP também pode usar a réplica 2 como fallback.
3. **Resposta divergente:** reiniciar somente a réplica 3 no PowerShell com `$env:SIMULAR_FALHA='1'; python controladores\replica.py --id 3`. Ela retorna valor falso 99.0 em `/leituras/ultima`, e o middleware pode apontar `replicas_divergentes: [3]` quando as outras duas concordam. Encerrar a réplica e limpar a variável com `Remove-Item Env:SIMULAR_FALHA -ErrorAction SilentlyContinue`.
4. **Comando confirmado:** no painel, ligar/desligar o ventilador e observar confirmação e réplica utilizada.

## Limitações importantes

- Réplicas recebem publicações MQTT independentemente; **não existe sincronização histórica entre bancos**. Uma réplica fora do ar pode perder leituras.
- Consenso é votação simples de leituras idênticas, não consenso distribuído forte. Atrasos MQTT podem causar falta temporária de consenso.
- Preparação de comandos usa a primeira réplica disponível; **não replica a operação em todas as réplicas**.
- Deduplicação no atuador é por ID de comando. O ACK mantido no middleware é em memória e pode se perder ao reiniciar.
- O controle automático de temperatura (`controladores/controlador.py` + `atuadores/ventilador.py`) é uma demonstração anterior **separada** da execução principal com interface. Não há política integrada de conciliação entre comandos manuais e automáticos.
- A interface confirma o processamento do comando, mas não lê continuamente o estado físico do ventilador.
- Uso exclusivamente didático/local, sem autenticação ou TLS. Não controlar dispositivos reais.

## Organização

- `sensores/` — sensor simulado
- `controladores/` — controlador simples e réplicas
- `atuadores/` — atuador simples e confiável
- `middleware/` — API e coordenação
- `cliente/` — interface web
- `iniciar_etapa4.ps1` — inicialização da demonstração principal
- `ETAPA3_LEIA-ME.md`, `ETAPA4_LEIA-ME.md` — instruções de testes anteriores

## Tecnologias

Python, FastAPI, Uvicorn, Paho MQTT, Mosquitto, SQLite, HTML, CSS e JavaScript.
