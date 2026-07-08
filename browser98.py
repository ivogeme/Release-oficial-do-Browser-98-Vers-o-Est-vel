import tkinter as tk
from tkinter import scrolledtext
from urllib.request import urlopen
from html.parser import HTMLParser
from urllib.parse import urljoin
from io import BytesIO
from PIL import Image, ImageTk
import html as html_mod
import socket
import ssl

page_cache = {}
image_cache = {}
history = []
history_index = -1

MAX_CACHE_SIZE = 200 * 1024 * 1024  # 200 MB
current_cache_size = 0

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
        self.ignore_content = False  # Filtro anti-poluição para script/style

    def handle_starttag(self, tag, attrs):
        if tag in ["script", "style"]:
            self.ignore_content = True
            return
            
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
        elif tag == "a":
            for a in attrs:
                if a[0] == "href":
                    self.current_href = urljoin(self.base_url, a[1])
        elif tag == "img":
            for a in attrs:
                if a[0] == "src":
                    self.load_image(a[1])

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
            self.widget.tag_bind(
                self.current_href,
                "<Button-1>",
                lambda e, url=self.current_href: self.open_link(url)
            )
        else:
            self.widget.insert(tk.END, data, tags)

        if self.center:
            self.widget.tag_add("center", start, self.widget.index(tk.END))

    def load_image(self, src):
        url = urljoin(self.base_url, src)
        if url in image_cache:
            photo = image_cache[url]
            self.images.append(photo)
            self.widget.insert(tk.END, "\n")
            self.widget.image_create(tk.END, image=photo)
            self.widget.insert(tk.END, "\n")
            return

        try:
            data = urlopen(url, timeout=5).read()
            img = Image.open(BytesIO(data))
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)
            
            image_cache[url] = photo 
            self.images.append(photo)
            self.widget.insert(tk.END, "\n")
            self.widget.image_create(tk.END, image=photo)
            self.widget.insert(tk.END, "\n")
        except:
            self.widget.insert(tk.END, "[Imagem não carregada]\n")

    def open_link(self, url):
        address_bar.delete(0, tk.END)
        address_bar.insert(0, url)
        load_page()

# --- Parsers Auxiliares para Protocolos da Small Web ---

def render_gemini(url):
    viewer.delete(1.0, tk.END)
    if url in page_cache:
        parse_gemtext(page_cache[url], url)
        return

    try:
        clean_url = url.split("://")[1]
        parts = clean_url.split("/", 1)
        host = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"
        
        # AJUSTE TLS: Contexto resiliente para certificados autoassinados e TLS moderno/antigo
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        
        with socket.create_connection((host, 1965), timeout=7) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                request = f"gemini://{host}{path}\r\n"
                ssock.sendall(request.encode("utf-8"))
                
                response = b""
                while True:
                    chunk = ssock.read(1024)
                    if not chunk:
                        break
                    response += chunk
        
        try:
            content = response.decode("utf-8")
        except:
            content = response.decode("latin-1", errors="ignore")
            
        if "\r\n" in content:
            header_line, body = content.split("\r\n", 1)
            if header_line.startswith("20"):  
                page_cache[url] = body
                parse_gemtext(body, url)
            else:
                viewer.insert(tk.END, f"Aviso Gemini: Servidor respondeu com status -> {header_line}\n")
        else:
            viewer.insert(tk.END, "Erro: Resposta do servidor Gemini malformada.\n")
    except Exception as e:
        viewer.insert(tk.END, f"Erro de Conexão Gemini:\nNão foi possível estabelecer o handshake TLS seguro.\nDetalhes: {e}")

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
            # CORREÇÃO: Fatiamento corrigido para capturar links corretamente
            parts = line[2:].strip().split(maxsplit=1)
            if parts:
                link_url = urljoin(base_url, parts[0])
                link_text = parts[1] if len(parts) > 1 else parts[0]
                start = viewer.index(tk.END)
                viewer.insert(tk.END, "\n" + link_text, ["link"])
                end = viewer.index(tk.END)
                viewer.tag_add(link_url, start, end)
                viewer.tag_bind(link_url, "<Button-1>", lambda e, u=link_url: open_alternative_link(u))
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

def render_gopher(url):
    viewer.delete(1.0, tk.END)
    if url in page_cache:
        parse_gopher_menu(page_cache[url], url)
        return

    try:
        clean_url = url.split("://")[1]
        parts = clean_url.split("/", 1)
        host = parts[0]
        selector = "/" + parts[1] if len(parts) > 1 else ""
        
        with socket.create_connection((host, 70), timeout=5) as sock:
            sock.sendall(f"{selector}\r\n".encode("utf-8"))
            response = b""
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk
                
        try:
            content = response.decode("utf-8")
        except:
            content = response.decode("latin-1", errors="ignore")
            
        page_cache[url] = content
        parse_gopher_menu(content, url)
    except Exception as e:
        viewer.insert(tk.END, f"Erro de Conexão Gopher:\nServidor inacessível.\nDetalhes: {e}")

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
            
            if type_char in ["0", "1"]:  
                gopher_url = f"gopher://{host}:{port}/{type_char}{selector}"
                start = viewer.index(tk.END)
                prefix = "[TXT] " if type_char == "0" else "[DIR] "
                viewer.insert(tk.END, prefix + display_string + "\n", ["link"])
                end = viewer.index(tk.END)
                viewer.tag_add(gopher_url, start, end)
                viewer.tag_bind(gopher_url, "<Button-1>", lambda e, u=gopher_url: open_alternative_link(u))
            else:
                viewer.insert(tk.END, display_string + "\n")
        else:
            viewer.insert(tk.END, line + "\n")

def open_alternative_link(url):
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    load_page()

# --- Controle Principal de Navegação ---

def load_page():
    global history, history_index
    url = address_bar.get()
    
    # AJUSTE DE HISTÓRICO: URLs salvas de forma limpa apenas após validação do protocolo
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

    if not url.startswith("http"):
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
        return

    try:
        raw_data = urlopen(url, timeout=5).read()
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
    except Exception as e:
        viewer.delete(1.0, tk.END)
        viewer.insert(tk.END, f"Erro de Conexão:\nNão foi possível carregar a página.\nDetalhes: {e}")

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

# --- Interface ---
root = tk.Tk()
root.title("Browser 98") 
root.geometry("640x480")

top = tk.Frame(root)
top.pack(fill=tk.X)

address_bar = tk.Entry(top)
address_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

# MELHORIA: Atalho do Enter mapeado com sucesso para a barra de digitação
address_bar.bind("<Return>", lambda event: load_page())

tk.Button(top, text="Ir", command=load_page).pack(side=tk.RIGHT)
tk.Button(top, text="Atualizar", command=load_page).pack(side=tk.RIGHT)

viewer = scrolledtext.ScrolledText(root, wrap=tk.WORD)
viewer.pack(fill=tk.BOTH, expand=True)

tk.Button(top, text="←", command=go_back).pack(side=tk.LEFT)
tk.Button(top, text="→", command=go_forward).pack(side=tk.LEFT)

# --- Estilos ---
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

# --- Tela de boas-vindas ---
welcome = """
<h1>Browser 98</h1>
<p>Bem-vindo ao ecossistema da Small Web e Internet Retrô.</p>
<p>Suporta de forma nativa: HTTP, HTTPS, Gemini e Gopher.</p>
<p>Digite um endereço acima ou aperte Enter para começar.</p>
"""
parser = SimpleHTMLParser(viewer, "")
parser.feed(welcome)

root.mainloop()
