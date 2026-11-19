# Relatório técnico — SmartHome SD

## 1. Objetivo

Implementar um middleware didático para uma casa inteligente distribuída, utilizando MQTT para comunicação entre sensor, réplicas e atuador, além de API HTTP para acesso pelo cliente.

## 2. Componentes e fluxo

O sensor simula leituras de temperatura e publica mensagens MQTT. Três réplicas recebem essas mensagens e registram os dados em SQLite. O middleware consulta as réplicas em paralelo e aceita a última leitura quando pelo menos duas retornam exatamente os mesmos dados. A interface web acessa o middleware por métodos HTTP. Para comandos manuais, o middleware solicita a preparação em uma réplica disponível, publica a ordem via MQTT e aguarda confirmação do atuador.

## 3. Tolerância a falhas e divergências

O middleware tenta as três réplicas para consultas e exige duas leituras iguais. Se uma réplica parar, as duas restantes podem manter a leitura disponível. Na preparação de comandos, se a primeira réplica não responder, outra é tentada. Uma variável de ambiente permite simular uma réplica que devolve temperatura falsa (99 °C), para demonstrar a identificação de resposta divergente por votação.

## 4. Idempotência de comandos

Cada comando possui um identificador. O atuador registra os IDs executados em SQLite e, ao receber um ID repetido com a mesma ação, não reaplica a mudança, mas confirma o recebimento. Isso permite repetir uma tentativa após timeout, respeitadas as limitações do sistema.

## 5. Experimentos realizados

- Sensor publicando leituras MQTT e réplicas registrando dados.
- Consulta de estado com três réplicas concordantes (3 votos).
- Interrupção da réplica 1, com leitura ainda disponível pelas duas restantes.
- Comando de desligar executado com fallback para a réplica 2 após falha da primeira.
- Réplica 3 simulando temperatura incorreta, com duas respostas corretas e identificação da divergência.
- Interface web exibindo leituras e enviando comandos de ligar/desligar, com confirmação do atuador.

Os experimentos acima foram relatados durante a execução do projeto; os arquivos do ZIP incluem o código e bancos locais, mas não constituem registro formal de logs de cada experimento. Capturas de tela podem ser anexadas à versão entregue.

## 6. Limitações

A replicação de leituras é independente via MQTT, sem recuperação histórica após falha. A votação por maioria não equivale a um protocolo de consenso forte. As operações preparadas não são replicadas entre todas as bases. O controlador automático antigo é uma demonstração separada do fluxo principal com interface e comandos manuais. Não há autenticação, criptografia de transporte nem garantia de execução distribuída exatamente uma vez.

## 7. Conclusão

O protótipo demonstra comunicação publish/subscribe, persistência local, replicação de leituras, votação por maioria, detecção de divergência e fallback de comandos. Os testes mostram tolerância a falhas simples, dentro dos limites descritos, e permitem discutir os desafios de consistência e disponibilidade em sistemas distribuídos.
