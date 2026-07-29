# Browser 98

O **Browser 98** é um navegador multiprotocolo ultra-leve projetado para rodar em hardware legado (como sistemas rodando Windows 95/98/ME) e fornecer uma experiência de navegação rápida, segura e totalmente livre de scripts invasivos na era moderna.

Desenvolvido inteiramente em ambiente mobile e portado para Python nativo, o projeto nasceu em 2021 ao perceber a morte programada da retrocompatibilidade na Web comercial comandada pelo HTTP moderno e motores pesados de JavaScript.

## 🌟 Funcionalidades
* **Anti-Rastreamento Nativo:** Totalmente imune a scripts e rastreadores comerciais por não carregar motores JavaScript ou CSS complexos.
* **Preservação Histórica:** Suporte completo para HTML Clássico (HTML 1.0, 2.0 e 3.2 com renderização de tags históricas como `<center>` e tabelas básicas).
* **Conectividade Small Web:** Suporte nativo via sockets e TLS aos protocolos independentes **Gemini** (`gemini://`) e **Gopher** (`gopher://`).
* **Soberania e Privacidade:** Sem caixas-pretas ou telemetria. Construído apenas sobre bibliotecas padrão da linguagem Python (`socket`, `ssl`, `tkinter`).

## 🛠️ Como rodar
Certifique-se de possuir o Python 3 e a biblioteca Pillow instalados no seu ambiente:
```bash
pip install Pillow
python browser98.py

Browser 98

Um navegador leve e minimalista voltado para a Small Web, preservação digital, protocolos alternativos e navegação em computadores com recursos limitados.

"Status" (https://img.shields.io/badge/status-beta-yellow)
"Version" (https://img.shields.io/badge/version-1.1-blue)
"License" (https://img.shields.io/badge/license-GPLv3-blue)

🌐 Sobre o projeto

O Browser 98 é um projeto de navegador desenvolvido com o objetivo de oferecer uma experiência de navegação simples, leve e acessível, evitando a complexidade e o peso dos navegadores modernos.

O projeto busca explorar uma abordagem diferente da navegação na Internet, combinando suporte à Web tradicional com protocolos alternativos e descentralizados da chamada Small Web.

Atualmente, o Browser 98 possui suporte nativo aos seguintes protocolos:

- HTTP
- HTTPS
- Gemini
- Gopher

O navegador também possui suporte a recursos básicos de navegação, como histórico, favoritos, cache, downloads e carregamento de imagens.

---

🕰️ História do projeto

O desenvolvimento do Browser 98 começou em 2021.

Desde o início, o projeto passou por diversas versões, recriações, experimentos e mudanças de arquitetura. Algumas versões foram simplificadas ou tiveram recursos removidos durante o processo de desenvolvimento.

Em 2024, uma versão do Browser 98 chegou a ser integrada ao projeto NewXP, um projeto desenvolvido em colaboração com um colega, baseado no Windows XP e com uma interface inspirada no Windows 10.

O projeto NewXP foi posteriormente descontinuado e não está mais disponível para download. Apesar disso, esse período faz parte da história do desenvolvimento do Browser 98.

Após diferentes fases de desenvolvimento e recriação, o Browser 98 voltou a ser desenvolvido como um projeto independente, evoluindo gradualmente até a atual versão 1.1.

A versão atual representa uma nova etapa do projeto, com melhorias na navegação, gerenciamento de cache, carregamento assíncrono de imagens, downloads, favoritos e suporte ampliado aos protocolos Gemini e Gopher.

---

🎯 Filosofia

O Browser 98 parte de uma ideia simples:

«A Internet não precisa ser pesada para ser útil.»

A Web moderna evoluiu rapidamente, mas muitos computadores antigos e sistemas com poucos recursos ficaram para trás.

O projeto busca explorar uma alternativa baseada em:

- simplicidade;
- baixo consumo de recursos;
- protocolos abertos;
- preservação digital;
- compatibilidade com ambientes limitados;
- Small Web;
- independência de grandes motores de renderização.

O objetivo não é competir diretamente com navegadores modernos como Chrome, Firefox ou Edge.

O objetivo é oferecer uma experiência diferente, voltada para navegação simples, conteúdo leve e protocolos alternativos.

---

✨ Recursos atuais

Navegação

- [x] HTTP
- [x] HTTPS
- [x] Gemini
- [x] Gopher
- [x] Histórico de navegação
- [x] Voltar e avançar
- [x] Página inicial
- [x] Atualização de páginas
- [x] Barra de endereço

HTML

O navegador possui um renderizador HTML básico próprio, com suporte a diversos elementos de HTML clássico, incluindo:

- títulos;
- parágrafos;
- links;
- imagens;
- listas;
- texto em negrito;
- itálico;
- sublinhado;
- texto monoespaçado;
- blocos de citação;
- texto pré-formatado;
- tabelas básicas;
- cores de fonte;
- elementos de alinhamento.

O Browser 98 não pretende ser um navegador compatível com toda a Web moderna. Páginas que dependem fortemente de JavaScript, CSS moderno ou frameworks complexos podem não funcionar corretamente.

---

🌌 Gemini

O Browser 98 possui suporte nativo ao protocolo Gemini.

Recursos atualmente implementados incluem:

- conexão TLS;
- páginas Gemini;
- links;
- títulos;
- listas;
- citações;
- texto pré-formatado;
- respostas de entrada do usuário;
- redirecionamentos;
- cache;
- pesquisa em servidores compatíveis.

O modo de conexão TLS utilizado atualmente prioriza a compatibilidade com servidores Gemini que utilizam certificados que não podem ser validados pelo modelo tradicional de autoridades certificadoras.

---

🕳️ Gopher

O navegador também possui suporte ao protocolo Gopher.

Atualmente são reconhecidos:

- arquivos de texto;
- diretórios;
- mecanismos de busca Gopher.

O suporte ao protocolo Gopher continuará sendo expandido em versões futuras.

---

📥 Downloads

O Browser 98 possui um sistema básico de downloads.

Determinados links de arquivos são identificados automaticamente e podem ser salvos no computador por meio de uma janela de seleção de arquivo.

Entre os formatos atualmente identificados estão:

- ZIP
- EXE
- MP3
- PDF
- TAR.GZ

---

💾 Cache

O navegador possui um sistema de cache em memória para páginas acessadas.

O tamanho máximo configurado atualmente é de aproximadamente 200 MB para o cache de páginas.

O sistema possui gerenciamento automático para evitar que o cache ultrapasse o limite configurado.

---

🖼️ Carregamento de imagens

As imagens são carregadas de forma assíncrona, permitindo que a interface continue respondendo enquanto o conteúdo é baixado.

As imagens também possuem um cache próprio para evitar downloads desnecessários durante a sessão.

---

⭐ Favoritos

O Browser 98 possui um sistema simples de favoritos.

Os endereços são armazenados em um arquivo de texto chamado:

"favoritos.txt"

Essa abordagem mantém o sistema simples e leve, sem necessidade de banco de dados.

---

💻 Requisitos

Os requisitos mínimos ainda estão em fase de testes.

Como estimativa inicial, recomenda-se:

- CPU: processador equivalente a Pentium III ou superior;
- RAM: 128 MB como mínimo estimado;
- RAM recomendada: 256 MB ou mais;
- armazenamento: aproximadamente 50 MB livres, além das dependências;
- resolução mínima: 640×480;
- conexão TCP/IP;
- Python compatível com o código;
- Tkinter;
- Pillow.

A compatibilidade específica com sistemas operacionais antigos, incluindo Windows 95, Windows 98 e Windows ME, ainda precisa ser validada oficialmente.

O objetivo futuro do projeto é ampliar a compatibilidade com computadores e sistemas antigos.

---

🚀 Instalação

Clone o repositório:

git clone https://github.com/ivogeme/Release-oficial-do-Browser-98-Vers-o-Est-vel.git

Entre na pasta:

cd Release-oficial-do-Browser-98-Vers-o-Est-vel

Instale as dependências:

pip install -r requirements.txt

Execute o navegador:

python browser98.py

---

🧪 Status atual

Versão atual: 1.1 Beta

O Browser 98 está em desenvolvimento ativo.

A versão atual é funcional, mas ainda pode apresentar limitações e incompatibilidades com determinados sites e servidores.

O projeto está sendo desenvolvido gradualmente e novos recursos, correções e otimizações serão adicionados nas próximas versões.

---

⚠️ Problemas conhecidos

Entre as limitações atuais estão:

- suporte limitado a HTML moderno;
- ausência de JavaScript;
- suporte limitado a CSS;
- compatibilidade limitada com sites modernos;
- validação tradicional de certificados TLS Gemini desativada por motivos de compatibilidade;
- suporte Gopher ainda em expansão;
- cache de imagens separado do limite principal de cache;
- código ainda concentrado em um único arquivo;
- compatibilidade com sistemas muito antigos ainda não validada oficialmente.

Esses pontos fazem parte do roadmap de desenvolvimento e poderão ser aprimorados em versões futuras.

---

🗺️ Roadmap

Próximas versões

- [ ] Melhorar tratamento de erros;
- [ ] Melhorar gerenciamento de downloads;
- [ ] Downloads em blocos para reduzir o consumo de memória;
- [ ] Melhorar gerenciamento do cache;
- [ ] Melhorar histórico de navegação;
- [ ] Melhorar compatibilidade TLS do Gemini;
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

