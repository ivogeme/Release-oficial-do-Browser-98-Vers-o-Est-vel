import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog
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
page_cache = {}
image_cache = {}
history = []
history_index = -1

MAX_CACHE_SIZE = 200 * 1024 * 1024  # 200 MB
current_cache_size = 0

def update_status(text):
    """Atualiza a mensagem da barra de status no rodapé."""
    status_bar.config(text=text)
    root.update_idletasks()

def manage_cache_size():
    """Garante que o cache não ultrapasse o limite de memória (Garbage Collector FIFO)."""
    global current_cache_size
    while current_cache_size > MAX_CACHE_SIZE and page_cache:
        first_key = next(iter(page_cache))
        removed = page_cache.pop(first_key)
        current_cache_size -= len(str(removed).encode('utf-8'))

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
        self.current_font_color = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in ["script", "style"]:
            self.ignore_content = True
            return

        # Leitura de bgcolor no <body>
        if tag == "body" and "bgcolor" in attrs_dict:
            bg_color = attrs_dict["bgcolor"]
            try:
                self.widget.configure(bg=bg_color)
            except:
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
            # Verificação de Downloads
            if any(href.lower().endswith(ext) for ext in ['.zip', '.exe', '.mp3', '.pdf', '.tar.gz']):
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
        elif tag == "font":
            if self.current_styles and self.current_styles[-1].startswith("font_color_"):
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
                self.widget.tag_bind(self.current_href, "<Button-1>", lambda e, u=self.current_href: self.open_link(u))
            
            self.widget.tag_bind(self.current_href, "<Enter>", lambda e: self.widget.config(cursor="hand2"))
            self.widget.tag_bind(self.current_href, "<Leave>", lambda e: self.widget.config(cursor="xterm"))
        else:
            self.widget.insert(tk.END, data, tags)

        if self.center:
            self.widget.tag_add("center", start, self.widget.index(tk.END))

    def async_load_image(self, src):
        """Carrega imagens em uma thread separada para não travar a UI."""
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
                
                # Inserção na Thread Principal da UI
                root.after(0, lambda: self._insert_image(photo))
                update_status("Concluído")
            except:
                root.after(0, lambda: self.widget.insert(tk.END, "\n[Imagem não carregada]\n"))

        threading.Thread(target=fetch, daemon=True).start()

    def _insert_image(self, photo):
        self.widget.configure(state=tk.NORMAL)
        self.widget.insert(tk.END, "\n")
        self.widget.image_create(tk.END, image=photo)
        self.widget.insert(tk.END, "\n")
        self.widget.configure(state=tk.DISABLED)

    def open_link(self, url):
        address_bar.delete(0, tk.END)
        address_bar.insert(0, url)
        load_page()

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
            messagebox.showinfo("Browser 98", f"Download concluído com sucesso!\nSalvo em: {save_path}")
        except Exception as e:
            update_status("Erro no download.")
            messagebox.showerror("Erro", f"Falha ao baixar arquivo:\n{e}")

    threading.Thread(target=run_download, daemon=True).start()

# --- Renderização Gemini ---
def render_gemini(url):
    viewer.configure(state=tk.NORMAL)
    viewer.delete(1.0, tk.END)
    if url in page_cache:
        parse_gemtext(page_cache[url], url)
        viewer.configure(state=tk.DISABLED)
        update_status("Concluído (Cache)")
        return

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
            
        if "\r\n" in content:
            header_line, body = content.split("\r\n", 1)
            status_code = header_line.split()[0] if header_line.split() else ""
            
            # Status 10: Input/Busca Necessária
            if status_code.startswith("10"):
                prompt = header_line[3:].strip() or "Digite o termo de pesquisa:"
                user_input = simpledialog.askstring("Gemini Busca", prompt)
                if user_input:
                    search_url = f"gemini://{host}{path}?{user_input}"
                    address_bar.delete(0, tk.END)
                    address_bar.insert(0, search_url)
                    render_gemini(search_url)
                return

            # Status 20: Sucesso
            elif status_code.startswith("20"):  
                page_cache[url] = body
                parse_gemtext(body, url)
                update_status("Concluído")

            # Status 30: Redirecionamento
            elif status_code.startswith("3"):  
                redirect_url = header_line.split(maxsplit=1)[1].strip()
                redirect_url = urljoin(url, redirect_url)
                address_bar.delete(0, tk.END)
                address_bar.insert(0, redirect_url)
                render_gemini(redirect_url)
                return
            else:
                viewer.insert(tk.END, f"Aviso Gemini: Resposta do servidor -> {header_line}\n")
        else:
            viewer.insert(tk.END, "Erro: Resposta Gemini malformada.\n")
    except Exception as e:
        viewer.insert(tk.END, f"Erro de Conexão Gemini:\nDetalhes: {e}")
        update_status("Erro de conexão.")
    
    viewer.configure(state=tk.DISABLED)

def parse_gemtext(text, base_url):
    in_pre_mode = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_pre_mode = not in_pre_mode
            continue
            
        if in_pre_mode:
            viewer.insert(tk.END, line + "\n", ["pre", "mono"])
            continue
            
        if line.startswith("=>"):  
            parts = line[2:].strip().split(maxsplit=1)
            if parts:
                link_url = urljoin(base_url, parts[0])
                link_text = parts[1] if len(parts) > 1 else parts[0]
                start = viewer.index(tk.END)
                viewer.insert(tk.END, "\n" + link_text, ["link"])
                end = viewer.index(tk.END)
                viewer.tag_add(link_url, start, end)
                viewer.tag_bind(link_url, "<Button-1>", lambda e, u=link_url: open_alternative_link(u))
                viewer.tag_bind(link_url, "<Enter>", lambda e: viewer.config(cursor="hand2"))
                viewer.tag_bind(link_url, "<Leave>", lambda e: viewer.config(cursor="xterm"))
            continue
        elif line.startswith("###"):
            viewer.insert(tk.END, "\n\n" + line[3:].strip() + "\n", ["h3"])
        elif line.startswith("##"):
            viewer.insert(tk.END, "\n\n" + line[2:].strip() + "\n", ["h2"])
        elif line.startswith("#"):
            viewer.insert(tk.END, "\n\n" + line[1:].strip() + "\n", ["h1"])
        elif line.startswith("* "):
            viewer.insert(tk.END, "\n• " + line[2:].strip(), [])
        elif line.startswith(">"):
            viewer.insert(tk.END, "\n" + line[1:].strip(), ["quote"])
        else:
            viewer.insert(tk.END, "\n" + line, [])

# --- Renderização Gopher ---
def render_gopher(url):
    viewer.configure(state=tk.NORMAL)
    viewer.delete(1.0, tk.END)
    if url in page_cache:
        parse_gopher_menu(page_cache[url], url)
        viewer.configure(state=tk.DISABLED)
        update_status("Concluído (Cache)")
        return

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
        page_cache[url] = content
        parse_gopher_menu(content, url)
        update_status("Concluído")
    except Exception as e:
        viewer.insert(tk.END, f"Erro de Conexão Gopher:\nDetalhes: {e}")
        update_status("Erro ao carregar Gopher.")
        
    viewer.configure(state=tk.DISABLED)

def parse_gopher_menu(text, base_url):
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
            
            # Tipos 0 (Texto), 1 (Diretório) e 7 (Busca/Query)
            if type_char in ["0", "1", "7"]:  
                gopher_url = f"gopher://{host}:{port}/{type_char}{selector}"
                start = viewer.index(tk.END)
                
                prefix = "[TXT] " if type_char == "0" else ("[DIR] " if type_char == "1" else "[BUSCA] ")
                viewer.insert(tk.END, prefix + display_string + "\n", ["link"])
                end = viewer.index(tk.END)
                viewer.tag_add(gopher_url, start, end)
                
                if type_char == "7":
                    viewer.tag_bind(gopher_url, "<Button-1>", lambda e, u=gopher_url: gopher_search_query(u))
                else:
                    viewer.tag_bind(gopher_url, "<Button-1>", lambda e, u=gopher_url: open_alternative_link(u))
                
                viewer.tag_bind(gopher_url, "<Enter>", lambda e: viewer.config(cursor="hand2"))
                viewer.tag_bind(gopher_url, "<Leave>", lambda e: viewer.config(cursor="xterm"))
            else:
                viewer.insert(tk.END, display_string + "\n")
        else:
            viewer.insert(tk.END, line + "\n")

def gopher_search_query(url):
    query = simpledialog.askstring("Gopher Search", "Digite o termo de pesquisa para o servidor:")
    if query:
        full_query_url = f"{url}\t{query}"
        open_alternative_link(full_query_url)

def open_alternative_link(url):
    viewer.configure(state=tk.NORMAL)
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    load_page()

# --- NAVEGAÇÃO PRINCIPAL ---
def load_page():
    global history, history_index, current_cache_size
    url = address_bar.get().strip()
    
    viewer.configure(state=tk.NORMAL)
    viewer.configure(bg="white", fg="black")  # Reset das cores de fundo padrão
    
    if url.startswith("gemini://") or url.startswith("gopher://"):
        if not history or history[history_index] != url:
            history = history[:history_index + 1]
            history.append(url)
            history_index += 1
        if url.startswith("gemini://"):
            render_gemini(url)
        else:
            render_gopher(url)
        return

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
        address_bar.delete(0, tk.END)
        address_bar.insert(0, url)
        
    if url in page_cache:
        if not history or history[history_index] != url:
            history = history[:history_index + 1]
            history.append(url)
            history_index += 1
        viewer.delete(1.0, tk.END)
        parser = SimpleHTMLParser(viewer, url)
        parser.feed(page_cache[url])
        viewer.configure(state=tk.DISABLED)
        update_status("Concluído (Cache)")
        return

    try:
        update_status(f"Carregando {url}...")
        req = Request(url, headers={'User-Agent': 'Browser98/1.1 (Retro Engine)'})
        raw_data = urlopen(req, timeout=8).read()
        
        current_cache_size += len(raw_data)
        manage_cache_size()
        
        try:
            html = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            html = raw_data.decode("latin-1", errors="replace")
            
        page_cache[url] = html
        
        if not history or history[history_index] != url:
            history = history[:history_index + 1]
            history.append(url)
            history_index += 1

        viewer.delete(1.0, tk.END)
        parser = SimpleHTMLParser(viewer, url)
        parser.feed(html)
        update_status("Concluído")
    except Exception as e:
        viewer.delete(1.0, tk.END)
        viewer.insert(tk.END, f"Erro de Conexão HTTP/HTTPS:\nNão foi possível carregar a página.\nDetalhes: {e}")
        update_status("Erro de conexão.")
        
    viewer.configure(state=tk.DISABLED)

def go_back():
    global history_index
    if history_index > 0:
        history_index -= 1
        address_bar.delete(0, tk.END)
        address_bar.insert(0, history[history_index])
        load_page()

def go_forward():
    global history_index
    if history_index < len(history) - 1:
        history_index += 1
        address_bar.delete(0, tk.END)
        address_bar.insert(0, history[history_index])
        load_page()

def go_home():
    address_bar.delete(0, tk.END)
    address_bar.insert(0, HOMEPAGE)
    load_page()

# --- Gerenciamento de Favoritos ---
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
                    command=lambda u=fav: [address_bar.delete(0, tk.END), address_bar.insert(0, u), load_page()]
                )

# --- Janela Sobre / Manifesto ---
def show_about():
    about_win = tk.Toplevel(root)
    about_win.title("Sobre o Browser 98")
    about_win.geometry("380x260")
    about_win.resizable(False, False)
    
    lbl_title = tk.Label(about_win, text="Browser 98", font=("Courier", 16, "bold"))
    lbl_title.pack(pady=10)
    
    msg = (
        "Versão 1.1 (Build 2026)\n"
        "Desenvolvido para a Small Web e Preservação Retrô.\n\n"
        "Suporte nativo aos protocolos:\n"
        "• HTTP / HTTPS\n"
        "• Gemini (gemini://)\n"
        "• Gopher (gopher://)\n\n"
        "Licença: GNU GPL v3\n"
        "Sua privacidade é respeitada por padrão."
    )
    lbl_msg = tk.Label(about_win, text=msg, font=("Courier", 9), justify=tk.CENTER)
    lbl_msg.pack(padx=10, pady=5)
    
    tk.Button(about_win, text="OK", command=about_win.destroy, width=10).pack(pady=10)

# --- Montagem da Interface Gráfica ---
root = tk.Tk()
root.title("Browser 98") 
root.geometry("640x480")

# Menu Superior
menu_bar = tk.Menu(root)

# Menu Arquivo
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Página Inicial", command=go_home)
file_menu.add_separator()
file_menu.add_command(label="Sair", command=root.quit)
menu_bar.add_cascade(label="Arquivo", menu=file_menu)

# Menu Navegação
nav_menu = tk.Menu(menu_bar, tearoff=0)
nav_menu.add_command(label="Voltar (←)", command=go_back)
nav_menu.add_command(label="Avançar (→)", command=go_forward)
nav_menu.add_command(label="Atualizar", command=load_page)
menu_bar.add_cascade(label="Navegação", menu=nav_menu)

# Menu Favoritos
favorites_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Favoritos", menu=favorites_menu)

# Menu Ajuda
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Sobre o Browser 98", command=show_about)
menu_bar.add_cascade(label="Ajuda", menu=help_menu)

root.config(menu=menu_bar)

# Barra de Ferramentas Superior
top = tk.Frame(root)
top.pack(fill=tk.X, padx=2, pady=2)

tk.Button(top, text="←", command=go_back, width=3).pack(side=tk.LEFT)
tk.Button(top, text="→", command=go_forward, width=3).pack(side=tk.LEFT)
tk.Button(top, text="🏠", command=go_home, width=3).pack(side=tk.LEFT)

address_bar = tk.Entry(top)
address_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
address_bar.bind("<Return>", lambda event: load_page())

tk.Button(top, text="Ir", command=load_page).pack(side=tk.RIGHT)
tk.Button(top, text="Atualizar", command=load_page).pack(side=tk.RIGHT)

# Área do Renderizador de Conteúdo
viewer = scrolledtext.ScrolledText(root, wrap=tk.WORD)
viewer.pack(fill=tk.BOTH, expand=True)

# Barra de Status no Rodapé
status_bar = tk.Label(root, text="Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Courier", 9))
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# --- Configuração de Estilos e Tags de Formatação ---
viewer.configure(bg="white", fg="black", font=("Courier", 10))
viewer.tag_configure("bold", font=("Courier", 10, "bold"))
viewer.tag_configure("italic", font=("Courier", 10, "italic"))
viewer.tag_configure("underline", underline=True)
viewer.tag_configure("mono", font=("Courier", 10))
viewer.tag_configure("pre", font=("Courier", 10))
viewer.tag_configure("quote", lmargin1=20, lmargin2=20, foreground="gray")
viewer.tag_configure("center", justify="center")
viewer.tag_configure("link", foreground="blue", underline=True)

for i in range(1, 7):
    viewer.tag_configure(f"h{i}", font=("Courier", 18 - i * 2, "bold"))

# Construção inicial dos Favoritos
build_favorites_menu()

# --- Tela Inicial de Boas-Vindas ---
welcome = """
<h1>Browser 98</h1>
<p>Bem-vindo ao ecossistema da Small Web e Internet Retrô.</p>
<p>Suporta de forma nativa os protocolos: HTTP, HTTPS, Gemini e Gopher.</p>
<p>Digite um endereço acima ou navegue usando os menus superiores.</p>
"""
viewer.configure(state=tk.NORMAL)
parser = SimpleHTMLParser(viewer, "")
parser.feed(welcome)
viewer.configure(state=tk.DISABLED)

root.mainloop()
