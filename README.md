# README.md - Browser 98 (v1.2)
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
