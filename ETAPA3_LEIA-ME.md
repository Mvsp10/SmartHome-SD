# Etapa 3: replicas e leitura por maioria

1. Feche as janelas antigas do sensor antes de iniciar, para evitar duplicidade de leituras.
2. Abra a pasta `smarthome-sd` no VS Code.
3. No terminal, execute `python -m pip install -r requirements.txt`.
4. Confirme que o servico Mosquitto esta em execucao.
5. Execute `powershell -ExecutionPolicy Bypass -File .\iniciar_etapa3.ps1`.
6. Aguarde 10 segundos e abra `http://127.0.0.1:8000/estado`.
7. Teste `http://127.0.0.1:8101/leituras/ultima`, portas 8102 e 8103.
8. Feche a janela da replica 1; atualize `/estado`. Com duas replicas concordantes, o middleware continua respondendo.
9. Feche outra replica; `/estado` deve retornar `sem_consenso` (HTTP 503).

Os bancos SQLite ficam em `dados/replica_1.db`, `replica_2.db`, `replica_3.db`.

**Limites:** as replicas recebem as mesmas publicacoes MQTT, mas nao fazem sincronizacao historica entre si. Uma replica desligada perde leituras desse periodo. A votacao compara a ultima leitura exata e pode ficar temporariamente sem consenso. Nao ha autenticacao, prova criptografica, eleicao de lider nem garantia de execucao de comandos nesta etapa. O controlador antigo e o ventilador continuam disponiveis, mas nao fazem parte da votacao. Nao iniciar o controlador antigo junto com futuros controladores de comando sem coordenacao.
