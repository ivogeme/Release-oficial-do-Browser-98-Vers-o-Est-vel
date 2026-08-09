Browser 98 v1.2 — Especificação de desenvolvimento

Modifique o código atual do Browser 98 mantendo sua arquitetura em Python/Tkinter e preserve os recursos que já funcionam. Não reescreva o projeto inteiro. A versão 1.2 deve ser uma evolução incremental da versão 1.1.

1. Corrigir a arquitetura de cache

Melhore o sistema atual de "page_cache".

- Corrija o cálculo de "current_cache_size".
- Garanta que páginas removidas do cache realmente diminuam o contador.
- Evite que o cache ultrapasse o limite configurado.
- Não deixe imagens e páginas ocuparem o mesmo sistema de cache sem controle.
- Adicione uma função para limpar todo o cache.
- Adicione uma opção para recarregar a página ignorando o cache.
- Mantenha o limite padrão de 200 MB.
- Não implemente ainda cache persistente em disco.

2. Melhorar o histórico

O histórico atual está somente na memória.

Adicionar:

- salvamento do histórico em um arquivo local;
- carregamento do histórico quando o navegador iniciar;
- opção "Limpar histórico";
- evitar registrar repetidamente a mesma URL durante Voltar/Avançar;
- manter o funcionamento atual dos botões Voltar e Avançar.

Use um arquivo simples, como "historico.txt", para manter a solução leve.

3. Melhorar os favoritos

Manter o sistema atual baseado em arquivo, mas adicionar:

- remover favorito;
- editar favorito;
- evitar favoritos duplicados;
- opção para exportar favoritos;
- opção para importar favoritos.

Não implementar ainda pastas complexas de favoritos.

4. Melhorar downloads

Modificar "download_file()" para não carregar o arquivo inteiro na RAM.

Usar leitura em blocos:

- abrir a conexão;
- ler pequenos blocos de dados;
- gravar os blocos diretamente no arquivo;
- mostrar progresso;
- mostrar quantidade baixada;
- mostrar tamanho total quando o servidor fornecer "Content-Length";
- calcular velocidade aproximada;
- permitir cancelar o download.

Não implementar ainda pausa/retomada de downloads.

5. Melhorar o carregamento das páginas

Adicionar controle básico de carregamento:

- botão "Parar";
- indicador de carregamento;
- atualização da barra de status;
- mensagens como:
  - "Conectando...";
  - "Baixando...";
  - "Processando...";
  - "Concluído";
  - "Erro".

Evitar que operações de rede bloqueiem a interface gráfica.

6. Melhorar o parser HTML

Continuar usando "HTMLParser".

Adicionar suporte melhor para:

- "<title>";
- "<base>";
- "<meta charset>";
- "<font size>";
- "<font face>";
- tabelas;
- células de tabela;
- "colspan";
- "rowspan";
- formulários simples.

Implementar inicialmente apenas:

- "<input type="text">";
- "<input type="submit">";
- "<textarea>";
- "<select>";
- "<option>";
- "<button>".

Não tentar implementar JavaScript.

O navegador continuará sendo deliberadamente um navegador HTML leve e retrô.

7. Melhorar imagens

Manter o carregamento assíncrono existente.

Adicionar:

- tratamento correto de erros;
- suporte a mais formatos reconhecidos pelo Pillow;
- opção para salvar imagem;
- opção para abrir a imagem em uma janela separada;
- evitar carregar a mesma imagem várias vezes;
- limitar o tamanho máximo das imagens carregadas.

Corrigir possíveis problemas de referência de "PhotoImage" para impedir que imagens desapareçam.

8. Melhorar Gemini

Manter o suporte atual ao Gemini.

Adicionar:

- melhor interpretação dos códigos de status;
- suporte mais correto a URLs relativas;
- suporte a links Gemini com query;
- tratamento de respostas inválidas;
- limite de redirecionamentos para evitar loops;
- mostrar o status Gemini na barra de status;
- opção de compatibilidade quando o certificado TLS não puder ser validado.

TLS

Não remover a possibilidade de acessar servidores Gemini antigos ou com certificados problemáticos.

Porém:

- manter a verificação TLS como comportamento padrão sempre que possível;
- quando a validação falhar, informar claramente o problema;
- oferecer uma opção de compatibilidade para permitir conexão sem validação;
- deixar explícito na interface quando a conexão estiver usando TLS sem validação.

Não simplesmente desativar a segurança silenciosamente.

9. Melhorar Gopher

Manter o suporte atual e adicionar os tipos básicos que ainda faltam.

Priorizar:

- texto;
- diretórios;
- buscas;
- arquivos;
- imagens;
- tratamento de erros.

Não tentar transformar Gopher em um navegador moderno.

10. Adicionar "file://"

Implementar suporte para abrir arquivos HTML locais.

Exemplos:

"file:///C:/pagina.html"

ou arquivos locais equivalentes no Linux/macOS.

O navegador deve:

- abrir HTML local;
- resolver imagens relativas;
- resolver links relativos;
- impedir acesso acidental a recursos fora do contexto quando isso representar risco.

11. Melhorar a interface

Manter a interface Tkinter atual.

Adicionar:

- botão Parar;
- indicador simples de carregamento;
- menu "Configurações";
- opção de modo escuro;
- controle do tamanho da fonte;
- zoom simples do conteúdo;
- tela cheia com F11.

Não adicionar ainda sistema complexo de temas.

Como primeira versão de temas, disponibilizar apenas:

- Clássico;
- Escuro;
- Windows 98.

12. Atalhos de teclado básicos

Adicionar:

- Ctrl+L → selecionar barra de endereço;
- Ctrl+R → recarregar;
- Ctrl+Shift+R → recarregar ignorando cache;
- Alt+Left → voltar;
- Alt+Right → avançar;
- Ctrl+D → adicionar favorito;
- Ctrl+F → pesquisar na página;
- F5 → recarregar;
- F11 → tela cheia;
- Esc → parar carregamento.

13. Pesquisa dentro da página

Adicionar uma pequena ferramenta de pesquisa.

Ela deve:

- procurar texto dentro do "ScrolledText";
- destacar a ocorrência encontrada;
- permitir próxima ocorrência;
- permitir ocorrência anterior;
- fechar a caixa de pesquisa.

Não implementar pesquisa na Internet.

14. Código e organização

Sem reescrever tudo em C ou mudar a linguagem.

Dividir gradualmente o código em módulos:

browser98/
├── main.py
├── ui.py
├── network.py
├── html_parser.py
├── gemini.py
├── gopher.py
├── downloads.py
├── cache.py
├── history.py
├── favorites.py
└── config.py

Manter as funções existentes funcionando durante a migração.

Não criar uma arquitetura excessivamente complexa.

15. Tratamento de erros

Substituir gradualmente os "except:" genéricos por exceções específicas.

Exibir mensagens úteis para:

- erro DNS;
- conexão recusada;
- timeout;
- erro TLS;
- URL inválida;
- arquivo inexistente;
- erro HTTP;
- erro de download;
- erro de imagem.

Nunca deixar uma falha de uma imagem derrubar a página inteira.

16. Logs

Criar um sistema simples de log.

Registrar opcionalmente:

- URL acessada;
- protocolo;
- erros de conexão;
- downloads;
- erros do parser.

O usuário deve poder desativar os logs.

17. Configuração

Criar um arquivo simples de configuração, por exemplo:

"config.ini"

Salvar:

- página inicial;
- tamanho da fonte;
- tema;
- limite do cache;
- pasta de downloads;
- preferência de TLS;
- idioma.

Não utilizar banco de dados.

18. Compatibilidade

Testar prioritariamente:

- Windows 10;
- Windows 7;
- Linux;
- computadores com pouca RAM.

Manter o projeto leve.

Não adicionar dependências pesadas.

19. Segurança básica

Adicionar:

- validação de URLs;
- limite de redirecionamentos;
- limite de tamanho de downloads;
- confirmação antes de abrir determinados arquivos;
- aviso para certificados TLS inválidos;
- tratamento seguro de arquivos locais.

Não implementar JavaScript.

Não implementar execução automática de conteúdo.

20. Melhorias de desempenho

Corrigir principalmente:

- operações de rede bloqueando a interface;
- carregamento de imagens;
- consumo excessivo de memória;
- downloads que carregam arquivos inteiros na RAM;
- crescimento ilimitado de estruturas internas.

Priorizar estabilidade antes de adicionar novos recursos.

21. Documentação da versão 1.2

Atualizar:

- "README.md";
- changelog;
- requisitos;
- instruções de instalação;
- recursos disponíveis;
- limitações conhecidas.

Adicionar uma seção:

"O que há de novo no Browser 98 v1.2"

Listando apenas funcionalidades realmente implementadas.

Regra principal

Não transformar a versão 1.2 em uma reescrita completa.

A prioridade deve ser:

1. corrigir problemas existentes;
2. melhorar estabilidade;
3. melhorar downloads;
4. melhorar cache e histórico;
5. melhorar HTML;
6. melhorar Gemini/Gopher;
7. melhorar interface;
8. organizar o código.

Não implementar ainda:

- abas;
- JavaScript;
- CSS completo;
- engine moderna de navegador;
- WebAssembly;
- HTTP/3;
- sistema complexo de extensões;
- sincronização em nuvem;
- dezenas de novos protocolos.

A versão 1.2 deve continuar sendo reconhecivelmente o mesmo Browser 98, apenas mais estável, utilizável e organizado.horar compatibilidade TLS do Gemini;
- [ ] Expandir suporte ao Gopher;
- [ ] Melhorar suporte a HTML clássico;
- [ ] Adicionar configurações do navegador;
- [ ] Testar em hardware antigo.

Futuro

- [ ] Modularização do código;
- [ ] Cache persistente;
- [ ] Histórico persistente;
- [ ] Melhor suporte a formulários;
- [ ] Suporte ampliado a tipos MIME;
- [ ] Melhor suporte a conteúdo offline;
- [ ] Otimizações para computadores antigos;
- [ ] Possível implementação de uma engine de baixo nível;
- [ ] Possível futura versão em C.

---

📜 Licença

O Browser 98 é distribuído sob os termos da:

GNU General Public License v3.0 (GPLv3)

Consulte o arquivo "LICENSE" para obter o texto completo da licença.

---

👤 Desenvolvimento

O Browser 98 é um projeto independente desenvolvido por Ivo Luiz Miranda dos Santos.

O projeto começou em 2021 e continua em desenvolvimento.

Contribuições, testes, sugestões e relatos de problemas são bem-vindos.

---

🌐 Projeto

Repositório oficial:

https://github.com/ivogeme/Release-oficial-do-Browser-98-Vers-o-Est-vel

​"Nota: Para rodar no Windows 98 nativo, é necessário utilizar uma camada de compatibilidade como o KernelEx para suporte ao Python 3, ou portar as chamadas de biblioteca para o Python 2.7.


🛠️ Como rodar
Certifique-se de possuir o Python 3 e a biblioteca Pillow instalados no seu ambiente:
```bash
pip install Pillow
python browser98.py

