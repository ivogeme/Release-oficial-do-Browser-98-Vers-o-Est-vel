Browser 98

Navegador retrô experimental para a Small Web, Internet clássica e protocolos alternativos.

"Browser 98" (https://img.shields.io/badge/Browser%2098-v1.2-blue)
"Status" (https://img.shields.io/badge/status-experimental-orange)
"Python" (https://img.shields.io/badge/Python-3.x-yellow)
"License" (https://img.shields.io/badge/license-GPLv3-green)

---

Sobre o projeto

O Browser 98 é um navegador experimental desenvolvido em Python com uma interface inspirada nos navegadores e sistemas operacionais dos anos 1990 e início dos anos 2000.

O projeto tem como foco a Small Web, a preservação de tecnologias antigas da Internet e a experimentação com diferentes protocolos de comunicação.

Em vez de tentar reproduzir um navegador moderno completo, o Browser 98 busca oferecer uma experiência simples, leve e funcional para acessar conteúdos tradicionais e protocolos alternativos.

O navegador atualmente possui suporte a:

- HTTP
- HTTPS
- Gemini
- Gopher

---

Versão 1.2

A versão 1.2 representa uma evolução importante do Browser 98.

Nesta versão foram adicionados vários recursos de navegação que aproximam o projeto de um navegador propriamente dito, incluindo:

- Sistema de abas
- Histórico por aba
- Histórico salvo em arquivo
- Recarregamento ignorando o cache
- Normalização de URLs
- Temas retrô
- Pesquisa dentro da página
- Visualizador de código-fonte
- Melhor suporte a Gopher
- Melhor suporte a HTML
- Melhor sistema de cache
- Interface de navegação renovada
- Novos atalhos de teclado
- Sistema inicial de gerenciamento de abas

---

Principais recursos

Abas

O navegador possui suporte a múltiplas páginas abertas simultaneamente.

É possível:

- Criar novas abas
- Fechar abas
- Alternar entre abas
- Manter histórico independente por aba
- Abrir páginas em novas abas
- Abrir o código-fonte em uma nova aba
- Abrir a página "Sobre" em uma nova aba

Atalhos

"Ctrl + T"

Cria uma nova aba.

"Ctrl + W"

Fecha a aba atual.

---

Navegação

O Browser 98 possui os controles básicos de navegação:

- Voltar
- Avançar
- Início
- Recarregar
- Recarregar ignorando o cache
- Barra de endereço
- Botão Ir
- Barra de status

O navegador também tenta corrigir automaticamente alguns endereços digitados sem protocolo.

Por exemplo:

example.com

pode ser convertido para:

http://example.com/

Protocolos como "gemini://" e "gopher://" também são reconhecidos.

---

Protocolos

HTTP

O Browser 98 possui suporte básico ao protocolo HTTP.

Inclui:

- Requisições HTTP
- User-Agent próprio
- Download de conteúdo
- Cache
- Renderização básica de HTML

User-Agent utilizado pelo navegador:

Browser98/1.2 (Retro Engine)

---

HTTPS

O navegador possui suporte básico a HTTPS utilizando TLS através das bibliotecas de rede do Python.

O suporte ainda é experimental e não possui todos os mecanismos de segurança encontrados em navegadores modernos.

---

Gemini

Gemini é um dos principais protocolos suportados pelo Browser 98.

O navegador consegue acessar endereços:

gemini://

O suporte atual inclui:

- Conexões TLS
- Porta padrão 1965
- Status Gemini 10
- Status Gemini 20
- Redirecionamentos
- Entrada de texto
- Pesquisa
- Gemtext
- Links
- Títulos
- Listas
- Citações
- Blocos pré-formatados
- Cache

O projeto utiliza o Gemini como uma das principais referências para a exploração da Small Web.

---

Gopher

O Browser 98 também possui suporte ao protocolo Gopher.

O navegador reconhece diferentes tipos de itens encontrados em menus Gopher.

Entre eles:

- Texto
- Diretórios
- Pesquisa
- Arquivos binários
- Imagens
- Arquivos

O objetivo é permitir acessar servidores Gopher utilizando a mesma interface de navegação.

---

Renderização HTML

O Browser 98 possui um renderizador HTML próprio baseado no "HTMLParser" da biblioteca padrão do Python.

O objetivo atual é oferecer suporte a páginas simples, páginas antigas e conteúdos que não dependam de JavaScript ou de mecanismos modernos de renderização.

O navegador possui suporte básico a elementos como:

h1 até h6
p
br
b
strong
i
em
u
tt
pre
blockquote
ul
ol
li
table
tr
td
a
img
font
center
hr
marquee

Também existe suporte experimental para algumas propriedades "style principalmente relacionadas a cores.



Imagens

O navegador consegue carregar imagens presentes nas páginas.

O carregamento é realizado separadamente para evitar bloquear completamente a interface.

As imagens são:

- Baixadas em segundo plano
- Processadas pelo Pillow
- Redimensionadas para visualização
- Mantidas em memória para reutilização

---

Cache

O Browser 98 possui um sistema de cache em memória.

O limite atual configurado é:

200 MB

Quando o limite é ultrapassado, entradas antigas do cache podem ser removidas.

O cache é utilizado para diferentes tipos de conteúdo, incluindo:

- HTTP
- HTTPS
- Gemini
- Gopher
- Imagens

O navegador também possui uma função de recarregamento forçado que remove a página atual do cache antes de realizar uma nova requisição.

---

Downloads

O navegador possui um sistema básico de downloads.

Alguns tipos de arquivos são identificados automaticamente quando aparecem como links.

Atualmente incluem:

.zip
.exe
.mp3
.pdf
.tar.gz
.gz
.iso

Os downloads são executados em uma thread separada para reduzir o bloqueio da interface.

---

Favoritos

O Browser 98 possui um sistema simples de favoritos.

Os endereços são armazenados no arquivo:

favoritos.txt

Os favoritos podem ser acessados pelo menu Favoritos.

O sistema ainda será expandido em versões futuras.

---

Histórico

O navegador possui histórico individual para cada aba durante a execução.

Além disso, os endereços visitados são registrados no arquivo:

historico.txt

O sistema de histórico ainda está em desenvolvimento e será aprimorado nas próximas versões.

---

Pesquisa na página

A versão 1.2 possui uma ferramenta para localizar texto dentro da página.

Use:

Ctrl + F

O navegador procura o texto e destaca as ocorrências encontradas.

Ao final da pesquisa, a barra de status informa o número de ocorrências encontradas.

---

Visualizador de código-fonte

O Browser 98 possui um visualizador básico do conteúdo recebido da página.

Use:

Ctrl + U

O código-fonte é aberto em uma nova aba utilizando uma fonte monoespaçada.

Esse recurso pode ser utilizado para:

- Estudar HTML
- Desenvolver páginas
- Investigar problemas
- Estudar páginas antigas
- Experimentar com a Small Web

---

Temas

A versão 1.2 possui três temas.

Clássico

Tema padrão inspirado na interface tradicional do Browser 98.

Verde Fósforo

Inspirado nos antigos monitores CRT de fósforo verde.

Âmbar CRT

Inspirado nos antigos monitores monocromáticos de fósforo âmbar.

Os temas alteram a aparência da área de conteúdo.

---

Interface

A interface foi projetada para lembrar softwares da década de 1990.

Ela possui:

- Barra de menus
- Barra de ferramentas
- Botões de navegação
- Barra de endereço
- Sistema de abas
- Área de conteúdo
- Barra de status

A interface utiliza principalmente:

Tkinter
ttk

---

Atalhos de teclado

Atalho| Função
"Ctrl + T"| Nova aba
"Ctrl + W"| Fechar aba
"Ctrl + F"| Localizar na página
"Ctrl + U"| Código-fonte
"F5"| Recarregar

---

Arquitetura atual

O Browser 98 ainda está concentrado principalmente em um único arquivo Python.

Entre os componentes existentes estão:

- Interface gráfica
- Sistema de abas
- Navegação
- Histórico
- Favoritos
- Cache
- Downloads
- Parser HTML
- Parser Gemtext
- Parser Gopher
- Sistema de temas
- Normalização de URLs
- Visualizador de código-fonte

A modularização do projeto será uma das etapas importantes do desenvolvimento futuro.

---

Segurança

O Browser 98 é um projeto experimental.

Ele não deve ser utilizado como substituto de navegadores modernos para operações sensíveis, como:

- Internet Banking
- Compras
- Serviços que exigem autenticação
- Informações confidenciais

O suporte TLS ainda precisa de melhorias, principalmente em relação à validação de certificados.

O projeto prioriza atualmente compatibilidade experimental e acesso a protocolos alternativos.

---

Limitações

O Browser 98 ainda não é um navegador Web moderno completo.

Atualmente existem limitações importantes:

- JavaScript não é executado
- CSS possui suporte muito limitado
- Não existe uma engine de layout moderna
- Formulários HTML possuem suporte limitado
- Histórico ainda é simples
- Favoritos ainda são armazenados em arquivo de texto
- Cache ainda é principalmente baseado em memória
- Downloads ainda são básicos
- TLS ainda precisa de melhorias
- Não existe sandbox
- Não existe isolamento de processos
- Páginas Web modernas podem não funcionar corretamente

Essas limitações fazem parte do estágio atual do projeto.

---

Objetivos

O Browser 98 possui quatro objetivos principais.

1. Small Web

Facilitar o acesso a protocolos e conteúdos que não dependem da Web moderna.

2. Preservação

Manter acessíveis tecnologias e estilos associados à Internet clássica.

3. Retrocomputação

Criar uma experiência inspirada na computação dos anos 1990.

4. Aprendizado

Utilizar o projeto como laboratório para estudar:

- Redes
- Protocolos
- HTML
- Parsing
- TLS
- Cache
- Interfaces gráficas
- Sistemas de navegação
- Arquitetura de navegadores

---

Próximos passos

O foco das próximas versões será principalmente melhorar a base existente, em vez de simplesmente adicionar dezenas de recursos novos.

Prioridades:

- Melhorar estabilidade
- Corrigir problemas de abas
- Melhorar histórico
- Melhorar favoritos
- Melhorar downloads
- Melhorar cache
- Melhorar tratamento de erros
- Melhorar TLS
- Melhorar renderização HTML
- Melhorar compatibilidade Gemini
- Melhorar compatibilidade Gopher
- Modularizar o código
- Criar testes automatizados
- Melhorar documentação

Depois dessa etapa, novos protocolos e recursos poderão ser adicionados gradualmente.

---

Requisitos

Para executar o Browser 98 atualmente são necessários:

- Python 3.x
- Tkinter
- Pillow
- Sistema operacional compatível com Python
- Conexão com a Internet para acessar conteúdo remoto

Instale o Pillow com:

pip install pillow

---

Executando

Clone o repositório:

git clone https://github.com/ivogeme/Release-oficial-do-Browser-98-Vers-o-Est-vel.git

Entre na pasta:

cd Release-oficial-do-Browser-98-Vers-o-Est-vel

Execute o arquivo principal do projeto:

python browser98.py

«O nome do arquivo principal pode mudar conforme a organização da versão disponível no repositório.»

---

Licença

O Browser 98 é distribuído sob a:

GNU General Public License v3.0 (GPL-3.0)

Consulte o arquivo "LICENSE" para obter os termos completos da licença.

---

Status

Versão atual: 1.2

Estado: Experimental / Em desenvolvimento

O Browser 98 já possui uma base funcional de navegação, múltiplas abas, suporte a HTTP, HTTPS, Gemini e Gopher, cache, histórico, favoritos, downloads, temas e ferramentas de análise de páginas.

Ainda existem diversas limitações, mas a versão 1.2 representa uma etapa importante na evolução do projeto.

---

Histórico do projeto

O Browser 98 começou como um projeto experimental e passou por várias versões, recriações e mudanças de direção durante seu desenvolvimento.

A versão atual representa uma nova fase do projeto, com maior foco em:

- Navegação real
- Protocolos alternativos
- Small Web
- Preservação da Internet
- Interface retrô
- Arquitetura de navegador
- Experimentação técnica

O projeto continuará evoluindo gradualmente.

---

Browser 98

Uma experiência de navegação inspirada no passado, construída com ferramentas do presente.

HTTP • HTTPS • Gemini • Gopher

GPLv3 
mini • Gopher

GPLv3mini • Gopher

GPLv3PLv3Lv3