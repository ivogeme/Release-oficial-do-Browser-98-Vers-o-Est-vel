import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, filedialog
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from io import BytesIO
from PIL import Image, ImageTk
import html as html_mod
import socket
import ssl
import os
import threading

# --- Configurações Globais e Cache ---
HOMEPAGE = "gemini://geminiprotocol.net/"
FAVORITES_FILE = "favoritos.txt"
HISTORY_FILE = "historico.txt"
page_cache = {}
image_cache = {}

MAX_CACHE_SIZE = 200 * 1024 * 1024  # 200 MB
current_cache_size = 0

# Configurações de Tema
CURRENT_THEME = "Clássico"
THEMES = {
    "Clássico": {"bg": "white", "fg": "black"},
    "Verde Fósforo": {"bg": "#0d1117", "fg": "#00ff66"},
    "Âmbar CRT": {"bg": "#120a00", "fg": "#ffb000"}
}

# --- Tela Inicial Personalizada ---
WELCOME_HTML = """
<h1>Browser 98</h1>
<p>Bem-vindo ao ecossistema da Small Web e Internet Retrô.</p>
<p>Suporta de forma nativa os protocolos: HTTP, HTTPS, Gemini e Gopher.</p>
<p>Digite um endereço acima ou navegue usando os menus superiores.</p>
"""

def update_status(text):
    """Atualiza a mensagem da barra de status no rodapé."""
    try:
        status_bar.config(text=text)
        root.update_idletasks()
    except Exception:
        pass

def manage_cache_size():
    """Garante que o cache não ultrapasse o limite de memória (Garbage Collector FIFO)."""
    global current_cache_size
    while current_cache_size > MAX_CACHE_SIZE and page_cache:
        first_key = next(iter(page_cache))
        removed = page_cache.pop(first_key)
        current_cache_size -= len(str(removed).encode('utf-8'))

# --- Smart URL Parser ---
def normalize_url(raw_url):
    """Trata e normaliza URLs para evitar erros de DNS e formatação."""
    url = raw_url.strip()
    if not url:
        return HOMEPAGE
    
    # Corrige erros comuns de digitação em TLDs
    if url.endswith(".como"):
        url = url[:-1]
    
    if not any(url.startswith(p) for p in ["http://", "https://", "gemini://", "gopher://"]):
        if "gemini" in url:
            url = "gemini://" + url
        elif "gopher" in url:
            url = "gopher://" + url
        else:
            url = "http://" + url

    parsed = urlparse(url)
    if parsed.netloc and not parsed.path:
        url += "/"

    return url

# --- Parser HTML Avançado ---
class SimpleHTMLParser(HTMLParser):
    def __init__(self, widget, base_url):
        super().__init__()
        self.widget = widget
        self.base_url = base_url
        self.images = []
        self.current_styles = []
        self.current_href = None
        self.list_stack = []
        self.ol_counter = 1
        self.in_pre = False
        self.center = False
        self.ignore_content = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in ["script", "style"]:
            self.ignore_content = True
            return

        if tag == "body" and "bgcolor" in attrs_dict and CURRENT_THEME == "Clássico":
            try:
                self.widget.configure(bg=attrs_dict["bgcolor"])
            except Exception:
                pass

        if tag in ["b", "strong"]:
            self.current_styles.append("bold")
        elif tag in ["i", "em"]:
            self.current_styles.append("italic")
        elif tag == "u":
            self.current_styles.append("underline")
        elif tag == "tt":
            self.current_styles.append("mono")
        elif tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            self.current_styles.append(tag)
            self.widget.insert(tk.END, "\n\n")
        elif tag in ["p", "tr"]:
            self.widget.insert(tk.END, "\n\n")
        elif tag == "td":
            self.widget.insert(tk.END, "\t")
        elif tag == "br":
            self.widget.insert(tk.END, "\n")
        elif tag == "pre":
            self.in_pre = True
            self.current_styles.append("pre")
            self.widget.insert(tk.END, "\n")
        elif tag == "center":
            self.center = True
        elif tag == "blockquote":
            self.widget.insert(tk.END, "\n")
            self.current_styles.append("quote")
        elif tag == "hr":
            self.widget.insert(tk.END, "\n" + "-" * 40 + "\n")
        elif tag == "ul":
            self.list_stack.append("ul")
        elif tag == "ol":
            self.list_stack.append("ol")
            self.ol_counter = 1
        elif tag == "li":
            self.widget.insert(tk.END, "\n")
            if self.list_stack and self.list_stack[-1] == "ul":
                self.widget.insert(tk.END, "• ")
            elif self.list_stack and self.list_stack[-1] == "ol":
                self.widget.insert(tk.END, f"{self.ol_counter}. ")
                self.ol_counter += 1
        elif tag == "a" and "href" in attrs_dict:
            href = attrs_dict["href"]
            if any(href.lower().endswith(ext) for ext in ['.zip', '.exe', '.mp3', '.pdf', '.tar.gz', '.gz', '.iso']):
                self.current_href = "download:" + urljoin(self.base_url, href)
            else:
                self.current_href = urljoin(self.base_url, href)
        elif tag == "img" and "src" in attrs_dict:
            self.async_load_image(attrs_dict["src"])
        elif tag == "font":
            if "color" in attrs_dict:
                color = attrs_dict["color"]
                tag_name = f"font_color_{color}"
                self.widget.tag_configure(tag_name, foreground=color)
                self.current_styles.append(tag_name)
        elif tag == "marquee":
            self.widget.insert(tk.END, "\n[Letreiro]: ")

        if "style" in attrs_dict:
            style_str = attrs_dict["style"].lower()
            if "color:" in style_str:
                try:
                    c_val = style_str.split("color:")[1].split(";")[0].strip()
                    tag_name = f"inline_css_{c_val}"
                    self.widget.tag_configure(tag_name, foreground=c_val)
                    self.current_styles.append(tag_name)
                except Exception:
                    pass

    def handle_endtag(self, tag):
        if tag in ["script", "style"]:
            self.ignore_content = False
            return

        if tag in ["b", "strong", "i", "em", "u", "tt", "pre", "blockquote"]:
            if self.current_styles:
                self.current_styles.pop()
        elif tag.startswith("h"):
            self.widget.insert(tk.END, "\n")
            if self.current_styles:
                self.current_styles.pop()
        elif tag in ["ul", "ol"]:
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "a":
            self.current_href = None
        elif tag == "center":
            self.center = False
        elif tag == "pre":
            self.in_pre = False
        elif tag in ["font", "span"]:
            if self.current_styles:
                self.current_styles.pop()

    def handle_data(self, data):
        if self.ignore_content:
            return

        data = html_mod.unescape(data)
        if not self.in_pre:
            data = " ".join(data.split())

        start = self.widget.index(tk.END)
        tags = list(self.current_styles)

        if self.current_href:
            tags.append("link")
            self.widget.insert(tk.END, data, tags)
            end = self.widget.index(tk.END)
            self.widget.tag_add(self.current_href, start, end)
            
            if self.current_href.startswith("download:"):
                target_url = self.current_href.replace("download:", "")
                self.widget.tag_bind(self.current_href, "<Button-1>", lambda e, u=target_url: download_file(u))
            else:
                self.widget.tag_bind(self.current_href, "<Button-1>", lambda e, u=self.current_href: open_link_in_current_tab(u))
            
            self.widget.tag_bind(self.current_href, "<Enter>", lambda e: self.widget.config(cursor="hand2"))
            self.widget.tag_bind(self.current_href, "<Leave>", lambda e: self.widget.config(cursor="xterm"))
        else:
            self.widget.insert(tk.END, data, tags)

        if self.center:
            self.widget.tag_add("center", start, self.widget.index(tk.END))

    def async_load_image(self, src):
        url = urljoin(self.base_url, src)
        if url in image_cache:
            photo = image_cache[url]
            self.widget.insert(tk.END, "\n")
            self.widget.image_create(tk.END, image=photo)
            self.widget.insert(tk.END, "\n")
            return

        def fetch():
            try:
                update_status(f"Baixando imagem: {src}...")
                data = urlopen(url, timeout=5).read()
                img = Image.open(BytesIO(data))
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                image_cache[url] = photo
                root.after(0, lambda: self._insert_image(photo))
                update_status("Concluído")
            except Exception:
                root.after(0, lambda: self.widget.insert(tk.END, "\n[Imagem não carregada]\n"))

        threading.Thread(target=fetch, daemon=True).start()

    def _insert_image(self, photo):
        try:
            self.widget.configure(state=tk.NORMAL)
            self.widget.insert(tk.END, "\n")
            self.widget.image_create(tk.END, image=photo)
            self.widget.insert(tk.END, "\n")
            self.widget.configure(state=tk.DISABLED)
        except Exception:
            pass

# --- Gerenciador de Abas e Componente BrowserTab ---
class BrowserTab:
    def __init__(self, notebook):
        self.notebook = notebook
        self.frame = tk.Frame(notebook)
        self.history = []
        self.history_index = -1
        self.raw_content = ""

        self.viewer = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD)
        self.viewer.pack(fill=tk.BOTH, expand=True)

        self.apply_theme()
        notebook.add(self.frame, text="Nova Aba")

    def apply_theme(self):
        theme = THEMES[CURRENT_THEME]
        bg = theme["bg"]
        fg = theme["fg"]
        
        self.viewer.configure(bg=bg, fg=fg, font=("Courier", 10), insertbackground=fg)
        self.viewer.tag_configure("bold", font=("Courier", 10, "bold"), foreground=fg)
        self.viewer.tag_configure("italic", font=("Courier", 10, "italic"), foreground=fg)
        self.viewer.tag_configure("underline", underline=True, foreground=fg)
        self.viewer.tag_configure("mono", font=("Courier", 10), foreground=fg)
        self.viewer.tag_configure("pre", font=("Courier", 10), foreground=fg)
        self.viewer.tag_configure("quote", lmargin1=20, lmargin2=20, foreground="gray")
        self.viewer.tag_configure("center", justify="center")
        
        link_color = "cyan" if CURRENT_THEME != "Clássico" else "blue"
        self.viewer.tag_configure("link", foreground=link_color, underline=True)
        self.viewer.tag_configure("highlight", background="yellow", foreground="black")

        for i in range(1, 7):
            self.viewer.tag_configure(f"h{i}", font=("Courier", 18 - i * 2, "bold"), foreground=fg)

    def render_welcome_screen(self):
        self.viewer.configure(state=tk.NORMAL)
        self.viewer.delete(1.0, tk.END)
        self.raw_content = WELCOME_HTML
        parser = SimpleHTMLParser(self.viewer, "")
        parser.feed(WELCOME_HTML)
        self.viewer.configure(state=tk.DISABLED)
        notebook.tab(self.frame, text="Início")

# --- Ações de Navegação Globais ---
tabs = []

def get_current_tab():
    current_idx = notebook.index(notebook.select())
    return tabs[current_idx]

def create_new_tab(url=None, title=None):
    tab = BrowserTab(notebook)
    tabs.append(tab)
    notebook.select(tab.frame)
    
    if url:
        address_bar.delete(0, tk.END)
        address_bar.insert(0, url)
        load_page()
    elif title:
        notebook.tab(tab.frame, text=title)
        address_bar.delete(0, tk.END)
    else:
        address_bar.delete(0, tk.END)
        tab.render_welcome_screen()
        
    return tab

def close_current_tab():
    if len(tabs) > 1:
        current_idx = notebook.index(notebook.select())
        notebook.forget(current_idx)
        tabs.pop(current_idx)
        update_address_bar_from_tab()

def open_link_in_current_tab(url):
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    load_page()

def update_address_bar_from_tab(event=None):
    try:
        tab = get_current_tab()
        if tab.history and tab.history_index >= 0:
            address_bar.delete(0, tk.END)
            address_bar.insert(0, tab.history[tab.history_index])
    except (IndexError, tk.TclError):
        pass

# --- Gerenciador de Downloads ---
def download_file(url):
    filename = os.path.basename(urlparse(url).path) or "arquivo_download"
    save_path = filedialog.asksaveasfilename(initialfile=filename)
    if not save_path:
        return

    def run_download():
        try:
            update_status(f"Baixando arquivo: {filename}...")
            data = urlopen(url, timeout=15).read()
            with open(save_path, "wb") as f:
                f.write(data)
            update_status(f"Download concluído: {filename}")
            messagebox.showinfo("Browser 98", f"Download concluído!\nSalvo em: {save_path}")
        except Exception as e:
            update_status("Erro no download.")
            messagebox.showerror("Erro", f"Falha ao baixar arquivo:\n{e}")

    threading.Thread(target=run_download, daemon=True).start()

# --- Motores Gemini & Gopher ---
def render_gemini(tab, url):
    tab.viewer.configure(state=tk.NORMAL)
    tab.viewer.delete(1.0, tk.END)

    try:
        update_status(f"Conectando a {url}...")
        clean_url = url.split("://")[1]
        parts = clean_url.split("/", 1)
        host = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        
        with socket.create_connection((host, 1965), timeout=8) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                ssock.sendall(f"gemini://{host}{path}\r\n".encode("utf-8"))
                response = b""
                while True:
                    chunk = ssock.read(1024)
                    if not chunk:
                        break
                    response += chunk
        
        content = response.decode("utf-8", errors="replace")
        tab.raw_content = content
            
        if "\r\n" in content:
            header_line, body = content.split("\r\n", 1)
            status_code = header_line.split()[0] if header_line.split() else ""
            
            if status_code.startswith("10"):
                prompt = header_line[3:].strip() or "Digite o termo de pesquisa:"
                user_input = simpledialog.askstring("Gemini Busca", prompt)
                if user_input:
                    search_url = f"gemini://{host}{path}?{user_input}"
                    address_bar.delete(0, tk.END)
                    address_bar.insert(0, search_url)
                    render_gemini(tab, search_url)
                return
            elif status_code.startswith("20"):  
                page_cache[url] = body
                parse_gemtext(tab, body, url)
                update_status("Concluído")
            elif status_code.startswith("3"):  
                redirect_url = header_line.split(maxsplit=1)[1].strip()
                redirect_url = urljoin(url, redirect_url)
                address_bar.delete(0, tk.END)
                address_bar.insert(0, redirect_url)
                render_gemini(tab, redirect_url)
                return
            else:
                tab.viewer.insert(tk.END, f"Aviso Gemini: Resposta do servidor -> {header_line}\n")
    except Exception as e:
        tab.viewer.insert(tk.END, f"Erro de Conexão Gemini:\nDetalhes: {e}")
        update_status("Erro de conexão.")
    
    tab.viewer.configure(state=tk.DISABLED)

def parse_gemtext(tab, text, base_url):
    in_pre_mode = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_pre_mode = not in_pre_mode
            continue
            
        if in_pre_mode:
            tab.viewer.insert(tk.END, line + "\n", ["pre", "mono"])
            continue
            
        if line.startswith("=>"):  
            parts = line[2:].strip().split(maxsplit=1)
            if parts:
                link_url = urljoin(base_url, parts[0])
                link_text = parts[1] if len(parts) > 1 else parts[0]
                start = tab.viewer.index(tk.END)
                tab.viewer.insert(tk.END, "\n" + link_text, ["link"])
                end = tab.viewer.index(tk.END)
                tab.viewer.tag_add(link_url, start, end)
                tab.viewer.tag_bind(link_url, "<Button-1>", lambda e, u=link_url: open_link_in_current_tab(u))
                tab.viewer.tag_bind(link_url, "<Enter>", lambda e: tab.viewer.config(cursor="hand2"))
                tab.viewer.tag_bind(link_url, "<Leave>", lambda e: tab.viewer.config(cursor="xterm"))
            continue
        elif line.startswith("###"):
            tab.viewer.insert(tk.END, "\n\n" + line[3:].strip() + "\n", ["h3"])
        elif line.startswith("##"):
            tab.viewer.insert(tk.END, "\n\n" + line[2:].strip() + "\n", ["h2"])
        elif line.startswith("#"):
            tab.viewer.insert(tk.END, "\n\n" + line[1:].strip() + "\n", ["h1"])
        elif line.startswith("* "):
            tab.viewer.insert(tk.END, "\n• " + line[2:].strip(), [])
        elif line.startswith(">"):
            tab.viewer.insert(tk.END, "\n" + line[1:].strip(), ["quote"])
        else:
            tab.viewer.insert(tk.END, "\n" + line, [])

def render_gopher(tab, url):
    tab.viewer.configure(state=tk.NORMAL)
    tab.viewer.delete(1.0, tk.END)

    try:
        update_status(f"Conectando ao servidor Gopher {url}...")
        clean_url = url.split("://")[1]
        parts = clean_url.split("/", 1)
        host_port = parts[0].split(":")
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 70
        selector = "/" + parts[1] if len(parts) > 1 else ""
        
        with socket.create_connection((host, port), timeout=6) as sock:
            sock.sendall(f"{selector}\r\n".encode("utf-8"))
            response = b""
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk
                
        content = response.decode("utf-8", errors="replace")
        tab.raw_content = content
        page_cache[url] = content
        parse_gopher_menu(tab, content, url)
        update_status("Concluído")
    except Exception as e:
        tab.viewer.insert(tk.END, f"Erro de Conexão Gopher:\nDetalhes: {e}")
        update_status("Erro ao carregar Gopher.")
        
    tab.viewer.configure(state=tk.DISABLED)

def parse_gopher_menu(tab, text, base_url):
    for line in text.splitlines():
        if not line or line == ".":
            continue
        type_char = line[0]
        parts = line[1:].split("\t")
        if len(parts) >= 3:
            display_string = parts[0]
            selector = parts[1]
            host = parts[2]
            port = parts[3] if len(parts) > 3 else "70"
            
            if type_char in ["0", "1", "7", "4", "5", "9", "I", "g"]:  
                gopher_url = f"gopher://{host}:{port}/{type_char}{selector}"
                start = tab.viewer.index(tk.END)
                
                prefix_map = {"0": "[TXT] ", "1": "[DIR] ", "7": "[BUSCA] ", "9": "[BIN] ", "I": "[IMG] "}
                prefix = prefix_map.get(type_char, "[ARQ] ")
                
                tab.viewer.insert(tk.END, prefix + display_string + "\n", ["link"])
                end = tab.viewer.index(tk.END)
                tab.viewer.tag_add(gopher_url, start, end)
                
                if type_char == "7":
                    tab.viewer.tag_bind(gopher_url, "<Button-1>", lambda e, u=gopher_url: gopher_search_query(u))
                elif type_char in ["4", "5", "9", "I", "g"]:
                    tab.viewer.tag_bind(gopher_url, "<Button-1>", lambda e, u=gopher_url: download_file(u))
                else:
                    tab.viewer.tag_bind(gopher_url, "<Button-1>", lambda e, u=gopher_url: open_link_in_current_tab(u))
                
                tab.viewer.tag_bind(gopher_url, "<Enter>", lambda e: tab.viewer.config(cursor="hand2"))
                tab.viewer.tag_bind(gopher_url, "<Leave>", lambda e: tab.viewer.config(cursor="xterm"))
            else:
                tab.viewer.insert(tk.END, display_string + "\n")
        else:
            tab.viewer.insert(tk.END, line + "\n")

def gopher_search_query(url):
    query = simpledialog.askstring("Gopher Search", "Digite o termo de pesquisa:")
    if query:
        open_link_in_current_tab(f"{url}\t{query}")

# --- Carregador Principal de Páginas ---
def load_page(force_reload=False):
    global current_cache_size
    tab = get_current_tab()
    raw_url = address_bar.get()
    
    if not raw_url.strip():
        tab.render_welcome_screen()
        return

    url = normalize_url(raw_url)
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)

    tab.apply_theme()
    tab.viewer.configure(state=tk.NORMAL)
    
    domain = urlparse(url).netloc or "Página"
    notebook.tab(tab.frame, text=domain[:15])

    if not tab.history or tab.history[tab.history_index] != url:
        tab.history = tab.history[:tab.history_index + 1]
        tab.history.append(url)
        tab.history_index += 1
        save_history(url)

    if force_reload and url in page_cache:
        del page_cache[url]

    if url.startswith("gemini://"):
        render_gemini(tab, url)
        return
    elif url.startswith("gopher://"):
        render_gopher(tab, url)
        return

    if url in page_cache and not force_reload:
        tab.viewer.delete(1.0, tk.END)
        tab.raw_content = page_cache[url]
        parser = SimpleHTMLParser(tab.viewer, url)
        parser.feed(page_cache[url])
        tab.viewer.configure(state=tk.DISABLED)
        update_status("Concluído (Cache)")
        return

    try:
        update_status(f"Carregando {url}...")
        req = Request(url, headers={'User-Agent': 'Browser98/1.2 (Retro Engine)'})
        raw_data = urlopen(req, timeout=8).read()
        
        current_cache_size += len(raw_data)
        manage_cache_size()
        
        try:
            html = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            html = raw_data.decode("latin-1", errors="replace")
            
        page_cache[url] = html
        tab.raw_content = html

        tab.viewer.delete(1.0, tk.END)
        parser = SimpleHTMLParser(tab.viewer, url)
        parser.feed(html)
        update_status("Concluído")
    except Exception as e:
        tab.viewer.delete(1.0, tk.END)
        tab.viewer.insert(tk.END, f"Erro de Conexão HTTP/HTTPS:\nDetalhes: {e}")
        update_status("Erro de conexão.")
        
    tab.viewer.configure(state=tk.DISABLED)

def reload_page():
    load_page(force_reload=True)

# --- Controles de Navegação ---
def go_back():
    tab = get_current_tab()
    if tab.history_index > 0:
        tab.history_index -= 1
        address_bar.delete(0, tk.END)
        address_bar.insert(0, tab.history[tab.history_index])
        load_page()

def go_forward():
    tab = get_current_tab()
    if tab.history_index < len(tab.history) - 1:
        tab.history_index += 1
        address_bar.delete(0, tk.END)
        address_bar.insert(0, tab.history[tab.history_index])
        load_page()

def go_home():
    tab = get_current_tab()
    address_bar.delete(0, tk.END)
    tab.render_welcome_screen()

# --- Recurso: Visualizador de Código Fonte ---
def view_source(event=None):
    current_tab = get_current_tab()
    content = current_tab.raw_content if current_tab.raw_content else "[Sem código fonte disponível]"
    
    new_tab = create_new_tab(title="Código Fonte")
    new_tab.viewer.configure(state=tk.NORMAL)
    new_tab.viewer.delete(1.0, tk.END)
    new_tab.viewer.insert(tk.END, content, ["pre", "mono"])
    new_tab.viewer.configure(state=tk.DISABLED)

# --- Recurso: Localizar na Página ---
def find_in_page(event=None):
    tab = get_current_tab()
    query = simpledialog.askstring("Localizar", "Digite o termo para buscar na página:")
    if not query:
        return

    tab.viewer.tag_remove("highlight", "1.0", tk.END)
    idx = "1.0"
    matches = 0
    while True:
        idx = tab.viewer.search(query, idx, nocase=True, stopindex=tk.END)
        if not idx:
            break
        lastidx = f"{idx}+{len(query)}c"
        tab.viewer.tag_add("highlight", idx, lastidx)
        idx = lastidx
        matches += 1

    update_status(f"Busca por '{query}': {matches} ocorrência(s) encontrada(s).")

# --- Recurso: Troca de Temas ---
def set_theme(theme_name):
    global CURRENT_THEME
    CURRENT_THEME = theme_name
    for tab in tabs:
        tab.apply_theme()
    
    tab = get_current_tab()
    if not address_bar.get().strip():
        tab.render_welcome_screen()
    else:
        load_page()

# --- Favoritos e Histórico ---
def add_favorite():
    url = address_bar.get().strip()
    if not url:
        return
    try:
        with open(FAVORITES_FILE, "a", encoding="utf-8") as f:
            f.write(url + "\n")
        messagebox.showinfo("Favoritos", f"Site adicionado aos favoritos!\n{url}")
        build_favorites_menu()
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar o favorito: {e}")

def build_favorites_menu():
    favorites_menu.delete(0, tk.END)
    favorites_menu.add_command(label="⭐ Adicionar aos Favoritos", command=add_favorite)
    favorites_menu.add_separator()
    
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            favs = [line.strip() for line in f if line.strip()]
            for fav in favs:
                favorites_menu.add_command(
                    label=fav,
                    command=lambda u=fav: open_link_in_current_tab(u)
                )

def save_history(url):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(url + "\n")
    except Exception:
        pass

# --- Janela / Aba Sobre ---
def show_about():
    msg = (
        "<h1>Browser 98</h1>"
        "<p>Versão 1.2 (Build 2026)</p>"
        "<p>Desenvolvido para a Small Web e Preservação Retrô.</p>"
        "<p><b>Novidades da v1.2:</b></p>"
        "<ul>"
        "<li>Sistema de Abas Integrado</li>"
        "<li>Visualizador de Código Fonte (Ctrl+U)</li>"
        "<li>Busca na Página (Ctrl+F)</li>"
        "<li>Temas Retrô (CRT Verde / Âmbar)</li>"
        "</ul>"
        "<p>Licença: GNU GPL v3</p>"
    )
    
    new_tab = create_new_tab(title="Sobre")
    new_tab.viewer.configure(state=tk.NORMAL)
    new_tab.viewer.delete(1.0, tk.END)
    parser = SimpleHTMLParser(new_tab.viewer, "")
    parser.feed(msg)
    new_tab.viewer.configure(state=tk.DISABLED)

# --- Montagem da GUI Principal ---
root = tk.Tk()
root.title("Browser 98 v1.2") 
root.geometry("700x520")

root.bind("<Control-u>", view_source)
root.bind("<Control-f>", find_in_page)
root.bind("<Control-t>", lambda e: create_new_tab())
root.bind("<Control-w>", lambda e: close_current_tab())
root.bind("<F5>", lambda e: reload_page())

# Menu Superior
menu_bar = tk.Menu(root)

# Menu Arquivo
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Nova Aba (Ctrl+T)", command=create_new_tab)
file_menu.add_command(label="Fechar Aba (Ctrl+W)", command=close_current_tab)
file_menu.add_separator()
file_menu.add_command(label="Página Inicial", command=go_home)
file_menu.add_separator()
file_menu.add_command(label="Sair", command=root.quit)
menu_bar.add_cascade(label="Arquivo", menu=file_menu)

# Menu Navegação
nav_menu = tk.Menu(menu_bar, tearoff=0)
nav_menu.add_command(label="Voltar (←)", command=go_back)
nav_menu.add_command(label="Avançar (→)", command=go_forward)
nav_menu.add_command(label="Atualizar (F5)", command=reload_page)
nav_menu.add_separator()
nav_menu.add_command(label="Localizar na Página (Ctrl+F)", command=find_in_page)
nav_menu.add_command(label="Ver Código Fonte (Ctrl+U)", command=view_source)
menu_bar.add_cascade(label="Navegação", menu=nav_menu)

# Menu Exibir / Temas
theme_menu = tk.Menu(menu_bar, tearoff=0)
theme_menu.add_command(label="Clássico (Padrão)", command=lambda: set_theme("Clássico"))
theme_menu.add_command(label="Verde Fósforo", command=lambda: set_theme("Verde Fósforo"))
theme_menu.add_command(label="Âmbar CRT", command=lambda: set_theme("Âmbar CRT"))
menu_bar.add_cascade(label="Exibir", menu=theme_menu)

# Menu Favoritos
favorites_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Favoritos", menu=favorites_menu)

# Menu Ajuda
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Sobre o Browser 98", command=show_about)
menu_bar.add_cascade(label="Ajuda", menu=help_menu)

root.config(menu=menu_bar)

# --- Barra de Ferramentas Estilo Anos 90 ---
btn_kwargs = {
    "bg": "#d4d0c8",
    "activebackground": "#ece9d8",
    "relief": tk.RAISED,
    "bd": 2,
    "font": ("Tahoma", 8, "bold"),
    "padx": 4,
    "pady": 1
}

top = tk.Frame(root, bg="#d4d0c8", bd=1, relief=tk.RAISED)
top.pack(fill=tk.X, padx=0, pady=0)

tk.Button(top, text="Voltar", command=go_back, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(top, text="Avançar", command=go_forward, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(top, text="Recarregar", command=reload_page, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(top, text="Início", command=go_home, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(top, text="+Aba", command=create_new_tab, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)

address_bar = tk.Entry(top, font=("Tahoma", 9), bd=2, relief=tk.SUNKEN)
address_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, pady=2)
address_bar.bind("<Return>", lambda event: load_page())

tk.Button(top, text="Ir", command=load_page, **btn_kwargs).pack(side=tk.RIGHT, padx=1, pady=2)

# Componente de Abas Notebook
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)
notebook.bind("<<NotebookTabChanged>>", update_address_bar_from_tab)

# Barra de Status no Rodapé
status_bar = tk.Label(root, text="Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Courier", 9))
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# Inicialização da Primeira Aba (Com a Tela de Boas-Vindas) e Favoritos
build_favorites_menu()
create_new_tab()

root.mainloop()
