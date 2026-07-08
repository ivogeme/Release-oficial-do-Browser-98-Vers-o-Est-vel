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

