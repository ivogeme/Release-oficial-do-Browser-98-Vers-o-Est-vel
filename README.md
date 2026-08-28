# Browser 98 (v1.2)
> Um navegador web minimalista, leve e focado na preservação da Small Web, protocolos retrô e arquiteturas clássicas, desenvolvido em Python com Tkinter e Pillow.
> 
## **Visão Geral**
O **Browser 98** foi projetado para resgatar a essência da navegação clássica dos anos 90 e início dos anos 2000. Sem o peso de motores de renderização modernos ou execução de scripts complexos, ele oferece uma experiência veloz, focada em texto, hiperlinks e leitura limpa. Além do suporte a HTTP/HTTPS tradicional, ele traz implementações nativas para protocolos alternativos e descentralizados.
## **Principais Recursos da Versão 1.2**
 * **Suporte Multi-protocolo Coeso:** Navegue por páginas HTTP/HTTPS clássicas, explore o espaço com o protocolo **Gemini** (com tratamento de certificados e status) e acesse diretórios e arquivos via **Gopher**.
 * **Sistema de Cache Inteligente:** Gerenciamento duplo de cache (páginas e imagens) com limites estritos em bytes e limpeza automática (LRU implícito), garantindo economia de memória.
 * **Multiprocessamento e Assincronia:** Carregamento de páginas e mídias executado inteiramente em *background threads*, mantendo a interface gráfica do Tkinter sempre fluida e sem travamentos.
 * **Persistência Simples e Portável:** Histórico de navegação, lista de favoritos e configurações salvos em arquivos de texto plano locais (historico.txt, favoritos.txt, config.ini).
 * **Resiliência de Rede:** Tratamento avançado de exceções que traduz falhas complexas de sockets e SSL em mensagens amigáveis para o usuário.
## **Requisitos de Sistema**
 * **Python:** Versão 3.8 ou superior (recomendado Python 3.10+)
 * **Dependências Externas:** Biblioteca **Pillow** (PIL) para processamento e exibição de imagens.
 * **Hardware:** Extremamente leve; roda em praticamente qualquer processador com 128 MB a 256 MB de RAM livres e menos de 5 MB de espaço em disco.
## **Como Instalar e Executar**
 1. Certifique-se de ter o Python instalado em seu sistema.
 2. Instale a biblioteca de manipulação de imagens Pillow via terminal:
   ```bash
   pip install Pillow
   
   ```
 3. Baixe ou clone o código-fonte do navegador.
 4. Execute o script principal:
   ```bash
   python browser98.py
   
   ```
sico para páginas HTTP.

O navegador consegue:

- Fazer requisições HTTP.
- Baixar páginas.
- Interpretar HTML.
- Exibir links.
- Exibir imagens.
- Trabalhar com cache.
- Navegar entre páginas.

---

HTTPS

O Browser 98 possui suporte básico a HTTPS utilizando as bibliotecas de rede disponíveis no Python.

O objetivo atual é permitir a navegação em sites que ainda disponibilizam conteúdo compatível com o mecanismo simplificado do navegador.

«O Browser 98 ainda não possui um mecanismo completo de navegador moderno. Portanto, páginas que dependem fortemente de JavaScript, CSS moderno ou APIs avançadas podem não funcionar corretamente.»

---

Gemini

O Gemini é um dos principais focos do projeto.

O navegador possui suporte ao protocolo:

gemini://

Recursos implementados:

- Conexão TLS.
- Requisições Gemini.
- Códigos de status.
- Redirecionamentos.
- Entrada de usuário.
- Links Gemini.
- Renderização básica de Gemtext.
- Blocos de código.
- Títulos.
- Listas.
- Citações.
- Cache.
- Navegação por links.

Compatibilidade TLS

O modo atual de conexão Gemini utiliza uma configuração permissiva de TLS para maximizar a compatibilidade com servidores antigos e configurações que podem apresentar problemas de validação.

Isso é uma característica experimental da versão atual e deverá ser aprimorado em versões futuras.

---

Gopher

O Browser 98 também possui suporte ao protocolo:

gopher://

O navegador reconhece diferentes tipos de recursos Gopher, incluindo:

- Texto.
- Diretórios.
- Pesquisas.
- Arquivos binários.
- Imagens.
- Outros recursos transferíveis.

O objetivo é tornar o navegador útil também para exploração e preservação de conteúdo histórico da Internet.

---

🖥️ Renderizador HTML

O Browser 98 possui um renderizador HTML próprio baseado no "HTMLParser" do Python.

O mecanismo atualmente possui suporte básico para:

- Títulos.
- Parágrafos.
- Links.
- Imagens.
- Listas ordenadas.
- Listas não ordenadas.
- Tabelas básicas.
- Texto em negrito.
- Texto em itálico.
- Sublinhado.
- Texto monoespaçado.
- "blockquote".
- "pre".
- "hr".
- "<font>".
- Algumas propriedades "style".
- "<marquee>" em representação simplificada.
- Formatação básica de conteúdo.

O objetivo não é reproduzir integralmente os padrões HTML modernos, mas fornecer um mecanismo pequeno e compreensível.

---

🖼️ Imagens

O navegador possui carregamento de imagens utilizando Pillow.

As imagens podem ser:

- Baixadas separadamente.
- Processadas fora da interface principal.
- Redimensionadas para visualização.
- Inseridas diretamente no conteúdo da página.
- Armazenadas em cache durante a execução.

O carregamento assíncrono evita bloquear completamente a interface enquanto uma imagem está sendo baixada.

---

💾 Cache

O Browser 98 possui um sistema básico de cache em memória.

Limite padrão:

200 MB

O sistema tenta remover entradas antigas quando o limite é ultrapassado.

O cache atualmente é utilizado principalmente para:

- Páginas HTTP/HTTPS.
- Conteúdo Gemini.
- Conteúdo Gopher.
- Redução de requisições repetidas.

O sistema de cache continuará sendo aprimorado nas próximas versões.

---

🔖 Favoritos

O navegador possui um sistema simples de favoritos.

Atualmente é possível:

- Adicionar páginas aos favoritos.
- Salvar favoritos em arquivo.
- Carregar favoritos durante a inicialização.
- Abrir favoritos diretamente pelo menu.

Os favoritos são armazenados localmente.

---

📜 Histórico

A versão 1.2 introduziu histórico persistente.

O navegador salva os endereços visitados em:

historico.txt

Cada aba também possui seu próprio histórico de navegação durante a execução.

O sistema ainda será expandido para oferecer gerenciamento completo do histórico.

---

🎨 Temas

O Browser 98 possui três temas experimentais:

Clássico

Interface clara inspirada em navegadores e sistemas operacionais tradicionais.

Verde Fósforo

Inspirado em antigos monitores CRT verdes.

Âmbar CRT

Inspirado em terminais e monitores monocromáticos de fósforo âmbar.

Os temas podem ser alterados pelo menu:

Exibir

---

🔎 Ferramentas

Localizar na página

Atalho:

Ctrl+F

Permite pesquisar palavras dentro da página atualmente aberta.

Os resultados encontrados são destacados visualmente.

---

Visualizar código-fonte

Atalho:

Ctrl+U

Abre uma nova aba contendo o conteúdo bruto recebido da página.

Isso é especialmente útil para:

- Desenvolvimento.
- Estudos de HTML.
- Debugging.
- Preservação de páginas.
- Análise de conteúdo.

---

📥 Downloads

O navegador possui suporte básico para downloads.

Arquivos reconhecidos incluem, entre outros:

- ZIP.
- EXE.
- MP3.
- PDF.
- TAR.GZ.
- GZ.
- ISO.

O arquivo pode ser salvo utilizando o seletor de arquivos do sistema operacional.

O gerenciador de downloads ainda é considerado experimental.

---

🧩 Arquitetura atual

O projeto atualmente é desenvolvido em:

Python 3

Principais bibliotecas utilizadas:

- "tkinter"
- "urllib"
- "html.parser"
- "urllib.parse"
- "socket"
- "ssl"
- "threading"
- "Pillow"

A interface gráfica utiliza Tkinter.

O projeto foi desenvolvido inicialmente como um navegador experimental e ainda está passando por uma evolução arquitetural.

---

📁 Arquivos principais

A estrutura do projeto poderá evoluir ao longo das próximas versões.

Atualmente, os principais componentes incluem:

Browser 98
├── interface gráfica
├── sistema de abas
├── navegação
├── histórico
├── favoritos
├── cache
├── renderizador HTML
├── renderizador Gemini
├── renderizador Gopher
├── downloads
├── carregamento de imagens
└── sistema de temas

---

🖥️ Compatibilidade

O projeto utiliza Python e Tkinter para manter a interface relativamente simples.

Plataformas de interesse:

- Windows.
- Linux.
- macOS.

Também existe interesse em testar o navegador em computadores antigos.

A compatibilidade com versões antigas do Windows é uma das áreas de pesquisa do projeto.

---

⚠️ Limitações atuais

O Browser 98 ainda é um navegador experimental.

Ele não é compatível com toda a Web moderna.

Entre as principais limitações estão:

- JavaScript não é executado.
- CSS moderno possui suporte muito limitado.
- Não existe um motor de layout completo.
- Não existe DOM completo.
- HTML moderno possui suporte parcial.
- Formulários ainda são limitados.
- Downloads ainda são básicos.
- Cache ainda precisa de melhorias.
- Certificados TLS ainda precisam de um sistema completo de validação.
- Histórico ainda precisa de um gerenciador completo.
- Favoritos ainda não possuem pastas.
- Não existe sincronização.
- Não existe suporte completo às APIs modernas da Web.

Essas limitações são conhecidas e fazem parte do estado atual do projeto.

---

🎯 Objetivos da próxima versão

O foco das próximas versões será principalmente estabilidade, arquitetura e qualidade, em vez de simplesmente adicionar dezenas de novos recursos.

Prioridades:

- Corrigir bugs encontrados na versão 1.2.
- Melhorar o gerenciamento das abas.
- Melhorar o histórico.
- Melhorar os favoritos.
- Melhorar o sistema de cache.
- Melhorar o tratamento de erros.
- Melhorar o gerenciamento de memória.
- Melhorar o suporte HTTP/HTTPS.
- Melhorar a compatibilidade Gemini.
- Melhorar o suporte Gopher.
- Melhorar o renderizador HTML.
- Melhorar o sistema de downloads.
- Melhorar a documentação.
- Criar testes automatizados.
- Organizar o código em módulos.

---

🛠️ Desenvolvimento

O Browser 98 é um projeto experimental e de código aberto.

Contribuições podem ajudar principalmente nas seguintes áreas:

- Desenvolvimento Python.
- Protocolos de Internet.
- HTML.
- Redes.
- Interface gráfica.
- Testes.
- Compatibilidade com sistemas antigos.
- Preservação digital.
- Documentação.

Antes de enviar alterações grandes, recomenda-se verificar o estado atual do projeto e manter as mudanças compatíveis com a proposta de um navegador pequeno e experimental.

---

📜 Licença

Este projeto é distribuído sob a licença:

GNU General Public License v3.0

Consulte o arquivo "LICENSE" para obter o texto completo da licença.

---

🕰️ História do projeto

O Browser 98 começou a ser desenvolvido em 2021.

Durante seu desenvolvimento, o projeto passou por diversas versões, experimentos e recriações.

Em determinado momento, partes do projeto foram utilizadas em outro projeto experimental chamado NewXP, que buscava criar uma experiência semelhante ao Windows XP utilizando uma interface inspirada em versões mais recentes do Windows.

O NewXP posteriormente foi descontinuado.

O Browser 98 continuou seu desenvolvimento de forma independente, chegando à atual arquitetura baseada em Python e Tkinter.

A versão 1.2 representa uma nova etapa do projeto, principalmente pela introdução do sistema de abas, temas, histórico persistente, visualização do código-fonte e ferramentas de pesquisa.

---

🌐 Filosofia do projeto

O Browser 98 não tenta ser o navegador mais poderoso do mundo.

A proposta é outra.

Ele busca demonstrar que ainda é possível criar uma experiência de navegação pequena, compreensível e independente, utilizando tecnologias relativamente simples.

O projeto também serve como experiência de aprendizado sobre:

- Redes.
- Protocolos.
- HTML.
- TLS.
- Interfaces gráficas.
- Sistemas de cache.
- Gerenciamento de arquivos.
- Renderização de conteúdo.
- Arquitetura de navegadores.

A ideia é construir o navegador gradualmente, começando por uma base simples e expandindo suas capacidades sem perder sua identidade.

---

📸 Capturas de tela

As capturas de tela do projeto podem ser encontradas na página do repositório.

Novas capturas serão adicionadas conforme o desenvolvimento avançar.

---

🚧 Status

Browser 98 v1.2

Estado:

Em desenvolvimento ativo.

A versão atual é utilizável como navegador experimental para conteúdos simples, Small Web, Gemini e Gopher, mas ainda não deve ser considerada uma alternativa completa aos navegadores modernos.

---

🔮 Futuro

O desenvolvimento futuro deverá seguir uma evolução gradual:

v1.2
 │
 ├── Estabilidade
 ├── Correção de bugs
 ├── Melhorias de navegação
 └── Melhorias do código
        │
        ▼
Próximas versões
 │
 ├── Renderização HTML aprimorada
 ├── Melhor segurança TLS
 ├── Melhor gerenciamento de downloads
 ├── Cache persistente aprimorado
 ├── Histórico avançado
 ├── Favoritos avançados
 ├── Mais protocolos
 └── Melhor compatibilidade

O objetivo é fazer o Browser 98 crescer sem transformar o projeto em uma cópia dos navegadores modernos.

---

⭐ Se você gostou do projeto

Se o Browser 98 chamou sua atenção, você pode:

- ⭐ Marcar o repositório com uma estrela.
- 🐛 Relatar problemas.
- 💡 Sugerir melhorias.
- 🔧 Contribuir com código.
- 📖 Melhorar a documentação.
- 📸 Enviar capturas de tela.
- 🧪 Testar o navegador em diferentes sistemas.

---

Browser 98
Uma pequena janela para a Internet.