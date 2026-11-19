# Etapa 4 — Comandos confirmados e fallback

**Pare as janelas da Etapa 3 antes de iniciar esta etapa.** Não rode o controlador antigo ou o ventilador antigo junto com os novos componentes.

1. Copie os arquivos para a pasta existente, preservando `.venv` e `dados`. Substitua `middleware/api.py` e `controladores/replica.py`.
2. Rode `powershell -ExecutionPolicy Bypass -File .\iniciar_etapa4.ps1`.
3. Acesse `http://127.0.0.1:8000/docs` e execute POST `/comandos/ventilador` com `{"acao":"ligar"}`.
4. Desligue a réplica 1 e repita com `{"acao":"desligar"}`. A resposta deve indicar `controlador_utilizado: 2` (se a réplica 2 estiver ativa).
5. Reenvie o mesmo ID com a mesma ação para testar deduplicação. **Não reutilize o ID com outra ação.**

**Limitações:** há fallback para preparação de comandos e ACK do atuador, mas a operação ainda não é replicada para todas as bases. Se o middleware cair, o ACK em memória se perde; reenvie com o mesmo ID. A simulação não fornece consenso forte nem resistência criptográfica a ataques. Não use para controlar equipamentos reais.
