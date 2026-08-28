
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, filedialog
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, unquote, quote
from io import BytesIO
from PIL import Image, ImageTk
import html as html_mod
import socket
import ssl
import os
import sys
import threading
import time
import configparser
import logging
import re
import mimetypes


# ============================================================
# Browser 98 v1.2
# Incremental evolution of the original Python/Tkinter engine.
# No JavaScript, no database, no persistent page cache.
# ============================================================

APP_VERSION = "1.2"
APP_BUILD = "2026"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")
FAVORITES_FILE = os.path.join(BASE_DIR, "favoritos.txt")
HISTORY_FILE = os.path.join(BASE_DIR, "historico.txt")
LOG_FILE = os.path.join(BASE_DIR, "browser98.log")

DEFAULT_HOMEPAGE = "gemini://geminiprotocol.net/"
MAX_CACHE_SIZE = 200 * 1024 * 1024
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_DOWNLOAD_SIZE = 512 * 1024 * 1024
MAX_REDIRECTS = 5
DOWNLOAD_BLOCK_SIZE = 64 * 1024
IMAGE_BLOCK_SIZE = 64 * 1024


# ============================================================
# Configuration
# ============================================================

config = configparser.ConfigParser()
config["browser"] = {
    "homepage": DEFAULT_HOMEPAGE,
    "font_size": "10",
    "theme": "Clássico",
    "cache_limit_mb": "200",
    "download_folder": os.path.join(os.path.expanduser("~"), "Downloads"),
    "tls_verify": "yes",
    "language": "pt-BR",
    "logging": "yes",
}

if os.path.exists(CONFIG_FILE):
    try:
        config.read(CONFIG_FILE, encoding="utf-8")
    except (configparser.Error, OSError):
        pass

homepage = config.get("browser", "homepage", fallback=DEFAULT_HOMEPAGE)
try:
    FONT_SIZE = max(7, min(32, config.getint("browser", "font_size", fallback=10)))
except ValueError:
    FONT_SIZE = 10

CURRENT_THEME = config.get("browser", "theme", fallback="Clássico")
try:
    cache_limit_mb = max(1, config.getint("browser", "cache_limit_mb", fallback=200))
except ValueError:
    cache_limit_mb = 200
MAX_CACHE_SIZE = cache_limit_mb * 1024 * 1024

DOWNLOAD_FOLDER = os.path.expanduser(
    config.get(
        "browser",
        "download_folder",
        fallback=os.path.join(os.path.expanduser("~"), "Downloads"),
    )
)
TLS_VERIFY = config.getboolean("browser", "tls_verify", fallback=True)
LOG_ENABLED = config.getboolean("browser", "logging", fallback=True)

THEMES = {
    "Clássico": {"bg": "white", "fg": "black", "link": "blue", "button": "#d4d0c8"},
    "Escuro": {"bg": "#202124", "fg": "#eeeeee", "link": "#6db3ff", "button": "#303134"},
    "Windows 98": {"bg": "#c0c0c0", "fg": "black", "link": "#0000aa", "button": "#d4d0c8"},
    # Preserved from the previous version:
    "Verde Fósforo": {"bg": "#0d1117", "fg": "#00ff66", "link": "#00ffff", "button": "#0d1117"},
    "Âmbar CRT": {"bg": "#120a00", "fg": "#ffb000", "link": "#ffe08a", "button": "#120a00"},
}

if CURRENT_THEME not in THEMES:
    CURRENT_THEME = "Clássico"


def save_config():
    config["browser"]["homepage"] = homepage
    config["browser"]["font_size"] = str(FONT_SIZE)
    config["browser"]["theme"] = CURRENT_THEME
    config["browser"]["cache_limit_mb"] = str(MAX_CACHE_SIZE // (1024 * 1024))
    config["browser"]["download_folder"] = DOWNLOAD_FOLDER
    config["browser"]["tls_verify"] = "yes" if TLS_VERIFY else "no"
    config["browser"]["logging"] = "yes" if LOG_ENABLED else "no"
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)
    except OSError:
        pass


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger("browser98")
logger.setLevel(logging.INFO)
_log_handler = None


def configure_logging():
    global _log_handler
    logger.handlers.clear()
    if not LOG_ENABLED:
        _log_handler = None
        return
    try:
        _log_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        _log_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(_log_handler)
    except OSError:
        _log_handler = None


configure_logging()


def log_info(message):
    try:
        logger.info(message)
    except Exception:
        pass


def log_error(message):
    try:
        logger.error(message)
    except Exception:
        pass


# ============================================================
# Cache
# Separate page and image caches. Both are bounded.
# ============================================================

page_cache = {}       # URL -> text
page_cache_sizes = {} # URL -> bytes
image_cache = {}      # URL -> ImageTk.PhotoImage
image_cache_sizes = {}  # URL -> approximate bytes
image_cache_refs = {}   # URL -> PIL image reference, prevents PhotoImage loss

current_cache_size = 0
current_image_cache_size = 0
cache_lock = threading.RLock()


def _text_size(value):
    if isinstance(value, bytes):
        return len(value)
    return len(str(value).encode("utf-8", errors="replace"))


def _remove_page_cache(url):
    global current_cache_size
    with cache_lock:
        page_cache.pop(url, None)
        size = page_cache_sizes.pop(url, 0)
        current_cache_size = max(0, current_cache_size - size)


def _remove_image_cache(url):
    global current_image_cache_size
    with cache_lock:
        image_cache.pop(url, None)
        image_cache_refs.pop(url, None)
        size = image_cache_sizes.pop(url, 0)
        current_image_cache_size = max(0, current_image_cache_size - size)


def put_page_cache(url, content):
    global current_cache_size
    size = _text_size(content)
    if size > MAX_CACHE_SIZE:
        return
    with cache_lock:
        if url in page_cache:
            current_cache_size = max(0, current_cache_size - page_cache_sizes.get(url, 0))
        page_cache[url] = content
        page_cache_sizes[url] = size
        current_cache_size += size
        while current_cache_size > MAX_CACHE_SIZE and page_cache:
            oldest = next(iter(page_cache))
            if oldest == url and len(page_cache) == 1:
                _remove_page_cache(oldest)
                break
            _remove_page_cache(oldest)


def put_image_cache(url, photo, pil_image, size):
    global current_image_cache_size
    if size > MAX_IMAGE_SIZE:
        return
    with cache_lock:
        if url in image_cache:
            current_image_cache_size = max(
                0, current_image_cache_size - image_cache_sizes.get(url, 0)
            )
        image_cache[url] = photo
        image_cache_refs[url] = pil_image
        image_cache_sizes[url] = size
        current_image_cache_size += size
        while current_image_cache_size > MAX_IMAGE_SIZE * 8:
            if not image_cache:
                break
            oldest = next(iter(image_cache))
            _remove_image_cache(oldest)


def clear_cache():
    global current_cache_size, current_image_cache_size
    with cache_lock:
        page_cache.clear()
        page_cache_sizes.clear()
        image_cache.clear()
        image_cache_sizes.clear()
        image_cache_refs.clear()
        current_cache_size = 0
        current_image_cache_size = 0
    update_status("Cache limpo.")
    log_info("Cache limpo pelo usuário.")


def cache_info_text():
    with cache_lock:
        return (
            f"Páginas: {len(page_cache)} | "
            f"{current_cache_size / 1024 / 1024:.1f} MB / "
            f"{MAX_CACHE_SIZE / 1024 / 1024:.0f} MB | "
            f"Imagens: {len(image_cache)} | "
            f"{current_image_cache_size / 1024 / 1024:.1f} MB"
        )


# ============================================================
# Runtime state
# ============================================================

tabs = []
history_store = []
active_downloads = {}
network_jobs = set()
network_lock = threading.Lock()

WELCOME_HTML = """
<h1>Browser 98</h1>
<p>Bem-vindo ao ecossistema da Small Web e Internet Retrô.</p>
<p>Suporta de forma nativa os protocolos: HTTP, HTTPS, Gemini e Gopher.</p>
<p>Também suporta páginas HTML locais com file://.</p>
<p>Digite um endereço acima ou navegue usando os menus superiores.</p>
"""


def update_status(text):
    try:
        root.after(0, lambda: status_bar.config(text=text))
    except (NameError, RuntimeError, tk.TclError):
        pass


def update_progress(value, show=True):
    def _update():
        try:
            if show:
                progress_bar.pack(fill=tk.X, padx=2, pady=1)
                progress_bar.start(10)
            else:
                progress_bar.stop()
                progress_bar.pack_forget()
        except tk.TclError:
            pass

    try:
        root.after(0, _update)
    except (NameError, RuntimeError):
        pass


def set_busy(busy):
    def _set():
        try:
            if busy:
                progress_bar.pack(fill=tk.X, padx=2, pady=1)
                progress_bar.start(10)
            else:
                progress_bar.stop()
                progress_bar.pack_forget()
        except tk.TclError:
            pass
    try:
        root.after(0, _set)
    except (NameError, RuntimeError):
        pass


# ============================================================
# URL handling
# ============================================================

ALLOWED_SCHEMES = {"http", "https", "gemini", "gopher", "file"}


def normalize_url(raw_url):
    url = raw_url.strip()
    if not url:
        return homepage

    if url in {"browser98://favorites", "browser98://history"}:
        return url

    if url.startswith("file://"):
        return url

    if not any(url.lower().startswith(p + "://") for p in ALLOWED_SCHEMES):
        if "gemini" in url.lower():
            url = "gemini://" + url
        elif "gopher" in url.lower():
            url = "gopher://" + url
        else:
            url = "http://" + url

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES and not url.startswith("browser98://"):
        raise ValueError(f"Protocolo não suportado: {parsed.scheme or '(vazio)'}")

    if parsed.scheme != "file" and parsed.netloc and not parsed.path:
        url += "/"

    return url


def safe_urljoin(base, target):
    try:
        result = urljoin(base, target)
        parsed = urlparse(result)
        if parsed.scheme not in ALLOWED_SCHEMES:
            raise ValueError("Destino bloqueado: protocolo não permitido.")
        return result
    except ValueError:
        raise


# ============================================================
# History
# ============================================================

def load_history():
    global history_store
    history_store = []
    if not os.path.exists(HISTORY_FILE):
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if url and (not history_store or history_store[-1] != url):
                    history_store.append(url)
        history_store = history_store[-5000:]
    except OSError as exc:
        log_error(f"Erro ao carregar histórico: {exc}")


def save_history(url):
    global history_store
    if not url:
        return
    if history_store and history_store[-1] == url:
        return
    history_store.append(url)
    history_store = history_store[-5000:]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(history_store) + ("\n" if history_store else ""))
    except OSError as exc:
        log_error(f"Erro ao salvar histórico: {exc}")


def clear_history():
    global history_store
    history_store = []
    for tab in tabs:
        tab.history = []
        tab.history_index = -1
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("")
    except OSError as exc:
        log_error(f"Erro ao limpar histórico: {exc}")
    update_status("Histórico limpo.")


# ============================================================
# Favorites
# ============================================================

def read_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            result = []
            seen = set()
            for line in f:
                url = line.strip()
                if url and url not in seen:
                    seen.add(url)
                    result.append(url)
            return result
    except OSError as exc:
        log_error(f"Erro lendo favoritos: {exc}")
        return []


def write_favorites(favs):
    unique = []
    seen = set()
    for url in favs:
        url = url.strip()
        if url and url not in seen:
            seen.add(url)
            unique.append(url)
    try:
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            for url in unique:
                f.write(url + "\n")
        return True
    except OSError as exc:
        log_error(f"Erro salvando favoritos: {exc}")
        return False


def add_favorite():
    url = address_bar.get().strip()
    if not url:
        return
    try:
        url = normalize_url(url)
    except ValueError:
        messagebox.showerror("Favoritos", "URL inválida.")
        return
    favs = read_favorites()
    if url in favs:
        messagebox.showinfo("Favoritos", "Esse endereço já está nos favoritos.")
        return
    favs.append(url)
    if write_favorites(favs):
        build_favorites_menu()
        messagebox.showinfo("Favoritos", f"Site adicionado aos favoritos!\n{url}")


def remove_favorite():
    favs = read_favorites()
    if not favs:
        messagebox.showinfo("Favoritos", "Nenhum favorito salvo.")
        return
    choice = simpledialog.askstring(
        "Remover favorito",
        "Digite exatamente a URL do favorito a remover:\n\n" + "\n".join(favs),
    )
    if choice is None:
        return
    if choice in favs:
        favs.remove(choice)
        write_favorites(favs)
        build_favorites_menu()
        render_internal_favorites(get_current_tab())
    else:
        messagebox.showwarning("Favoritos", "Favorito não encontrado.")


def edit_favorite():
    favs = read_favorites()
    if not favs:
        messagebox.showinfo("Favoritos", "Nenhum favorito salvo.")
        return
    old = simpledialog.askstring(
        "Editar favorito",
        "URL atual:\n\n" + "\n".join(favs),
    )
    if old is None:
        return
    if old not in favs:
        messagebox.showwarning("Favoritos", "Favorito não encontrado.")
        return
    new = simpledialog.askstring("Editar favorito", "Nova URL:", initialvalue=old)
    if new is None:
        return
    try:
        new = normalize_url(new)
    except ValueError:
        messagebox.showerror("Favoritos", "Nova URL inválida.")
        return
    favs[favs.index(old)] = new
    write_favorites(favs)
    build_favorites_menu()
    render_internal_favorites(get_current_tab())


def export_bookmarks():
    save_path = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("HTML Files", "*.html"), ("Todos os arquivos", "*.*")],
        initialfile="browser98-bookmarks.html",
    )
    if not save_path:
        return
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(
                '<!DOCTYPE NETSCAPE-Bookmark-file-1>\n'
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
                "<TITLE>Browser 98 Bookmarks</TITLE>\n"
                "<H1>Browser 98 Bookmarks</H1>\n<DL><p>\n"
            )
            for fav in read_favorites():
                safe = html_mod.escape(fav, quote=True)
                f.write(f'    <DT><A HREF="{safe}">{safe}</A>\n')
            f.write("</DL><p>\n")
        messagebox.showinfo("Favoritos", "Favoritos exportados com sucesso.")
    except OSError as exc:
        messagebox.showerror("Erro", f"Falha ao exportar favoritos:\n{exc}")


def import_bookmarks():
    file_path = filedialog.askopenfilename(
        filetypes=[("HTML Files", "*.html;*.htm"), ("Todos os arquivos", "*.*")]
    )
    if not file_path:
        return
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        links = re.findall(r'HREF\s*=\s*["\']([^"\']+)["\']', content, re.I)
        valid = []
        for url in links:
            if urlparse(url).scheme in ALLOWED_SCHEMES:
                valid.append(url)
        favs = read_favorites()
        before = len(favs)
        for url in valid:
            if url not in favs:
                favs.append(url)
        write_favorites(favs)
        build_favorites_menu()
        messagebox.showinfo(
            "Favoritos",
            f"{len(favs) - before} favorito(s) novo(s) importado(s).",
        )
    except OSError as exc:
        messagebox.showerror("Erro", f"Falha ao importar favoritos:\n{exc}")


# ============================================================
# Forms
# ============================================================

class SimpleForm:
    def __init__(self, parser, action, method="get"):
        self.parser = parser
        self.action = action
        self.method = method.lower()
        self.controls = []

    def add_control(self, name, kind, widget, value=""):
        self.controls.append((name, kind, widget, value))

    def submit(self):
        values = []
        for name, kind, widget, default in self.controls:
            if not name:
                continue
            try:
                if kind == "select":
                    value = widget.get()
                elif kind == "textarea":
                    value = widget.get("1.0", tk.END).rstrip("\n")
                elif kind == "submit":
                    value = widget.cget("text")
                else:
                    value = widget.get()
            except tk.TclError:
                value = default
            values.append((name, value))

        if self.method == "post":
            messagebox.showinfo(
                "Browser 98",
                "Formulários POST são reconhecidos, mas o envio POST ainda é limitado nesta versão.",
            )
            return

        query = "&".join(
            f"{quote(str(k))}={quote(str(v))}" for k, v in values
        )
        target = self.action
        if query:
            separator = "&" if "?" in target else "?"
            target += separator + query
        open_link_in_current_tab(target)


# ============================================================
# HTML parser
# ============================================================

class SimpleHTMLParser(HTMLParser):
    def __init__(self, widget, base_url):
        super().__init__(convert_charrefs=True)
        self.widget = widget
        self.base_url = base_url
        self.current_styles = []
        self.current_href = None
        self.list_stack = []
        self.ol_counter = 1
        self.in_pre = False
        self.center = False
        self.ignore_content = False
        self.page_title = ""
        self.document_base = base_url
        self.current_form = None
        self.select_widget = None
        self.select_name = ""
        self.option_values = []
        self.textarea_widget = None
        self.table_rows = []
        self.current_row = None
        self.current_cell = None
        self.cell_colspan = 1
        self.cell_rowspan = 1

    def _insert(self, text, tags=None):
        self.widget.insert(tk.END, text, tags or [])

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = {k.lower(): v for k, v in attrs if k}

        if tag in ("script", "style"):
            self.ignore_content = True
            return
        if tag == "title":
            self._in_title = True
            return
        if tag == "base":
            href = attrs_dict.get("href")
            if href:
                try:
                    self.document_base = safe_urljoin(self.base_url, href)
                except ValueError:
                    pass
            return
        if tag == "meta":
            return

        if tag == "body" and "bgcolor" in attrs_dict and CURRENT_THEME == "Clássico":
            try:
                self.widget.configure(bg=attrs_dict["bgcolor"])
            except tk.TclError:
                pass

        if tag in ("b", "strong"):
            self.current_styles.append("bold")
        elif tag in ("i", "em"):
            self.current_styles.append("italic")
        elif tag == "u":
            self.current_styles.append("underline")
        elif tag == "tt":
            self.current_styles.append("mono")
        elif tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            self.current_styles.append(tag)
            self._insert("\n\n")
        elif tag in ("p", "div", "section", "article"):
            self._insert("\n\n")
        elif tag == "br":
            self._insert("\n")
        elif tag == "pre":
            self.in_pre = True
            self.current_styles.append("pre")
            self._insert("\n")
        elif tag == "center":
            self.center = True
        elif tag == "blockquote":
            self._insert("\n")
            self.current_styles.append("quote")
        elif tag == "hr":
            self._insert("\n" + "-" * 40 + "\n")
        elif tag == "ul":
            self.list_stack.append("ul")
        elif tag == "ol":
            self.list_stack.append("ol")
            self.ol_counter = 1
        elif tag == "li":
            self._insert("\n")
            if self.list_stack and self.list_stack[-1] == "ul":
                self._insert("• ")
            elif self.list_stack and self.list_stack[-1] == "ol":
                self._insert(f"{self.ol_counter}. ")
                self.ol_counter += 1
        elif tag == "a" and attrs_dict.get("href") is not None:
            href = attrs_dict["href"]
            try:
                full = safe_urljoin(self.document_base, href)
                if any(
                    href.lower().split("?")[0].endswith(ext)
                    for ext in (".zip", ".exe", ".mp3", ".pdf", ".tar.gz", ".gz", ".iso")
                ):
                    self.current_href = "download:" + full
                else:
                    self.current_href = full
            except ValueError:
                self.current_href = None
        elif tag == "img" and attrs_dict.get("src"):
            self.async_load_image(attrs_dict["src"])
        elif tag == "font":
            if attrs_dict.get("color"):
                color = attrs_dict["color"]
                tag_name = f"font_color_{color}"
                try:
                    self.widget.tag_configure(tag_name, foreground=color)
                    self.current_styles.append(tag_name)
                except tk.TclError:
                    pass
            if attrs_dict.get("size"):
                self.current_styles.append(f"font_size_{attrs_dict['size']}")
            if attrs_dict.get("face"):
                self.current_styles.append(f"font_face_{attrs_dict['face']}")
        elif tag == "marquee":
            self._insert("\n[Letreiro]: ")
        elif tag == "table":
            self.table_rows = []
        elif tag == "tr":
            self.current_row = []
        elif tag in ("td", "th"):
            self.current_cell = ""
            try:
                self.cell_colspan = max(1, int(attrs_dict.get("colspan", "1")))
            except ValueError:
                self.cell_colspan = 1
            try:
                self.cell_rowspan = max(1, int(attrs_dict.get("rowspan", "1")))
            except ValueError:
                self.cell_rowspan = 1
        elif tag == "form":
            action = attrs_dict.get("action", self.document_base)
            try:
                action = safe_urljoin(self.document_base, action)
            except ValueError:
                action = self.document_base
            self.current_form = SimpleForm(
                self, action, attrs_dict.get("method", "get")
            )
        elif tag == "input" and self.current_form is not None:
            typ = attrs_dict.get("type", "text").lower()
            name = attrs_dict.get("name", "")
            value = attrs_dict.get("value", "")
            if typ in ("text", "search"):
                self._insert("\n")
                self._insert(f"{name}: " if name else "")
                entry = tk.Entry(self.widget)
                self.widget.window_create(tk.END, window=entry)
                self.current_form.add_control(name, typ, entry, value)
                self._insert("\n")
                entry.insert(0, value)
            elif typ == "submit":
                self._insert("\n")
                button = tk.Button(
                    self.widget,
                    text=value or "Enviar",
                    command=self.current_form.submit,
                )
                self.widget.window_create(tk.END, window=button)
                self._insert("\n")
                self.current_form.add_control(name, "submit", button, value)
        elif tag == "textarea" and self.current_form is not None:
            name = attrs_dict.get("name", "")
            self._insert("\n")
            text = tk.Text(self.widget, width=40, height=4)
            self.widget.window_create(tk.END, window=text)
            self.textarea_widget = text
            self.current_form.add_control(name, "textarea", text, "")
            self._insert("\n")
        elif tag == "select" and self.current_form is not None:
            self.select_name = attrs_dict.get("name", "")
            self.select_widget = ttk.Combobox(self.widget, state="readonly", width=25)
            self.widget.window_create(tk.END, window=self.select_widget)
            self.option_values = []
        elif tag == "option" and self.select_widget is not None:
            self._in_option = True
            self._option_value = attrs_dict.get("value", "")
            self._option_text = ""
        elif tag == "button":
            self._insert("\n")
            button = tk.Button(self.widget, text=attrs_dict.get("value", "Botão"))
            self.widget.window_create(tk.END, window=button)
            self._insert("\n")

        style = attrs_dict.get("style", "")
        if style:
            match = re.search(r"color\s*:\s*([^;]+)", style, re.I)
            if match:
                color = match.group(1).strip()
                tag_name = f"inline_css_{color}"
                try:
                    self.widget.tag_configure(tag_name, foreground=color)
                    self.current_styles.append(tag_name)
                except tk.TclError:
                    pass

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style"):
            self.ignore_content = False
            return
        if tag == "title":
            self._in_title = False
            return
        if tag in ("td", "th"):
            if self.current_row is not None:
                cell = self.current_cell.strip() if self.current_cell else ""
                self.current_row.append(
                    (cell, self.cell_colspan, self.cell_rowspan)
                )
            self.current_cell = None
        elif tag == "tr":
            if self.current_row:
                self.table_rows.append(self.current_row)
            self.current_row = None
        elif tag == "table":
            self.render_table()
        elif tag in ("b", "strong", "i", "em", "u", "tt", "pre", "blockquote"):
            if self.current_styles:
                self.current_styles.pop()
            if tag == "pre":
                self.in_pre = False
        elif tag.startswith("h"):
            self._insert("\n")
            if self.current_styles:
                self.current_styles.pop()
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "a":
            self.current_href = None
        elif tag == "center":
            self.center = False
        elif tag == "font":
            while self.current_styles and (
                self.current_styles[-1].startswith("font_")
                or self.current_styles[-1].startswith("font_size_")
                or self.current_styles[-1].startswith("font_face_")
            ):
                self.current_styles.pop()
        elif tag == "form":
            self.current_form = None
        elif tag == "select":
            if self.select_widget is not None:
                self.select_widget["values"] = [
                    x[1] for x in self.option_values
                ]
                if self.option_values:
                    self.select_widget.current(0)
                if self.current_form is not None:
                    self.current_form.add_control(
                        self.select_name,
                        "select",
                        self.select_widget,
                        "",
                    )
            self.select_widget = None
            self.option_values = []
            self.select_name = ""
        elif tag == "option":
            if self.select_widget is not None:
                self.option_values.append(
                    (self._option_value, self._option_text.strip())
                )
            self._in_option = False

    def handle_data(self, data):
        if getattr(self, "_in_title", False):
            self.page_title += data.strip()
            return
        if getattr(self, "_in_option", False):
            self._option_text = getattr(self, "_option_text", "") + data
            return
        if self.ignore_content:
            return

        data = html_mod.unescape(data)
        if self.current_cell is not None:
            self.current_cell += " " + data
            return

        if not self.in_pre:
            data = " ".join(data.split())

        if not data:
            return

        start = self.widget.index(tk.END)
        tags = list(self.current_styles)

        if self.current_href:
            tags.append("link")
            self.widget.insert(tk.END, data, tags)
            end = self.widget.index(tk.END)
            tag_name = self.current_href
            self.widget.tag_add(tag_name, start, end)
            if tag_name.startswith("download:"):
                target = tag_name[len("download:"):]
                self.widget.tag_bind(
                    tag_name, "<Button-1>",
                    lambda e, u=target: download_file(u)
                )
            else:
                self.widget.tag_bind(
                    tag_name, "<Button-1>",
                    lambda e, u=tag_name: open_link_in_current_tab(u)
                )
            self.widget.tag_bind(
                tag_name, "<Enter>",
                lambda e: self.widget.config(cursor="hand2")
            )
            self.widget.tag_bind(
                tag_name, "<Leave>",
                lambda e: self.widget.config(cursor="xterm")
            )
        else:
            self.widget.insert(tk.END, data, tags)

        if self.center:
            self.widget.tag_add("center", start, self.widget.index(tk.END))

    def handle_comment(self, data):
        return

    def render_table(self):
        if not self.table_rows:
            return
        self._insert("\n")
        normalized = []
        widths = {}
        for row in self.table_rows:
            out = []
            col = 0
            for text, colspan, rowspan in row:
                for offset in range(colspan):
                    value = text if offset == 0 else ""
                    out.append(value)
                    widths[col + offset] = max(
                        widths.get(col + offset, 0), len(value)
                    )
                col += colspan
            normalized.append(out)

        if not normalized:
            return
        max_col = max(widths) if widths else 0
        divider = "+" + "+".join(
            "-" * (widths.get(i, 0) + 2) for i in range(max_col + 1)
        ) + "+\n"
        self._insert(divider, ["mono"])
        for row in normalized:
            row = row + [""] * (max_col + 1 - len(row))
            line = "|"
            for i, cell in enumerate(row):
                line += " " + cell.ljust(widths.get(i, 0)) + " |"
            self._insert(line + "\n", ["mono"])
        self._insert(divider + "\n", ["mono"])

    def async_load_image(self, src):
        try:
            url = safe_urljoin(self.document_base, src)
        except ValueError:
            return

        with cache_lock:
            photo = image_cache.get(url)
        if photo is not None:
            self._insert_image(photo)
            return

        def fetch():
            try:
                request = Request(url, headers={"User-Agent": "Browser98/1.2"})
                img_mark = None
                with urlopen(request, timeout=8) as response:
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > MAX_IMAGE_SIZE:
                        raise ValueError("Imagem excede o limite de tamanho.")
                    data = bytearray()
                    while True:
                        chunk = response.read(IMAGE_BLOCK_SIZE)
                        if not chunk:
                            break
                        data.extend(chunk)
                        if len(data) > MAX_IMAGE_SIZE:
                            raise ValueError("Imagem excede o limite de tamanho.")
                        
                        try:
                            img = Image.open(BytesIO(bytes(data)))
                            img.load()
                            img.thumbnail((600, 600))
                            photo_chunk = ImageTk.PhotoImage(img)
                            
                            def _update_netscape_style(p=photo_chunk, mark=img_mark):
                                nonlocal img_mark
                                try:
                                    self.widget.configure(state=tk.NORMAL)
                                    if mark is None:
                                        self.widget.insert(tk.END, "\n")
                                        img_mark = self.widget.index(tk.END + "-1c")
                                        self.widget.image_create(img_mark, image=p)
                                        self.widget.insert(tk.END, "\n")
                                    else:
                                        self.widget.image_configure(mark, image=p)
                                    self.widget.configure(state=tk.DISABLED)
                                except tk.TclError:
                                    pass

                            root.after(0, _update_netscape_style)
                        except Exception:
                            pass

                img = Image.open(BytesIO(bytes(data)))
                img.load()
                img.thumbnail((600, 600))
                photo = ImageTk.PhotoImage(img)
                put_image_cache(url, photo, img, len(data))
                root.after(0, lambda p=photo: self._insert_image(p))
            except (URLError, OSError, ValueError, Exception) as exc:
                log_error(f"Erro de imagem {url}: {exc}")
                root.after(
                    0,
                    lambda: self._insert_text_safe("\n[Imagem não carregada]\n"),
                )

        threading.Thread(target=fetch, daemon=True).start()

    def _insert_text_safe(self, text):
        try:
            self.widget.configure(state=tk.NORMAL)
            self.widget.insert(tk.END, text)
            self.widget.configure(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _insert_image(self, photo):
        try:
            self.widget.configure(state=tk.NORMAL)
            self.widget.insert(tk.END, "\n")
            self.widget.image_create(tk.END, image=photo)
            self.widget.insert(tk.END, "\n")
            self.widget.configure(state=tk.DISABLED)
        except tk.TclError:
            pass


# ============================================================
# Browser tab
# ============================================================

class BrowserTab:
    def __init__(self, notebook):
        self.notebook = notebook
        self.frame = tk.Frame(notebook)
        self.history = []
        self.history_index = -1
        self.raw_content = ""
        self.current_url = ""
        self.loading = False
        self.stop_event = threading.Event()
        self.zoom = 1.0

        self.viewer = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            undo=False,
            padx=5,
            pady=5,
        )
        self.viewer.pack(fill=tk.BOTH, expand=True)
        self.apply_theme()
        notebook.add(self.frame, text="Nova Aba")

    def apply_theme(self):
        theme = THEMES[CURRENT_THEME]
        bg, fg = theme["bg"], theme["fg"]
        size = max(7, min(32, int(FONT_SIZE * self.zoom)))
        self.viewer.configure(
            bg=bg, fg=fg,
            font=("Courier", size),
            insertbackground=fg,
        )
        self.viewer.tag_configure("bold", font=("Courier", size, "bold"), foreground=fg)
        self.viewer.tag_configure("italic", font=("Courier", size, "italic"), foreground=fg)
        self.viewer.tag_configure("underline", underline=True, foreground=fg)
        self.viewer.tag_configure("mono", font=("Courier", size), foreground=fg)
        self.viewer.tag_configure("pre", font=("Courier", size), foreground=fg)
        self.viewer.tag_configure("quote", lmargin1=20, lmargin2=20, foreground="gray")
        self.viewer.tag_configure("center", justify="center")
        self.viewer.tag_configure(
            "link", foreground=theme["link"], underline=True
        )
        self.viewer.tag_configure(
            "highlight", background="yellow", foreground="black"
        )
        for i in range(1, 7):
            hsize = max(9, int((18 - i * 2) * self.zoom))
            self.viewer.tag_configure(
                f"h{i}",
                font=("Courier", hsize, "bold"),
                foreground=fg,
            )

    def render_welcome_screen(self):
        self.viewer.configure(state=tk.NORMAL)
        self.viewer.delete("1.0", tk.END)
        self.raw_content = WELCOME_HTML
        parser = SimpleHTMLParser(self.viewer, "")
        parser.feed(WELCOME_HTML)
        self.viewer.configure(state=tk.DISABLED)
        notebook.tab(self.frame, text="Início")
        self.current_url = ""

    def zoom_in(self):
        self.zoom = min(2.0, self.zoom + 0.1)
        self.apply_theme()

    def zoom_out(self):
        self.zoom = max(0.6, self.zoom - 0.1)
        self.apply_theme()

    def zoom_reset(self):
        self.zoom = 1.0
        self.apply_theme()


# ============================================================
# Navigation
# ============================================================

def get_current_tab():
    try:
        idx = notebook.index(notebook.select())
        return tabs[idx]
    except (tk.TclError, IndexError):
        return tabs[0] if tabs else None


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
    if len(tabs) <= 1:
        return
    try:
        idx = notebook.index(notebook.select())
        tabs[idx].stop_event.set()
        notebook.forget(idx)
        tabs.pop(idx)
        update_address_bar_from_tab()
    except (tk.TclError, IndexError):
        pass


def update_address_bar_from_tab(event=None):
    tab = get_current_tab()
    if not tab:
        return
    if tab.current_url:
        address_bar.delete(0, tk.END)
        address_bar.insert(0, tab.current_url)


def open_link_in_current_tab(url):
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    load_page()


def go_back(event=None):
    tab = get_current_tab()
    if not tab or tab.history_index <= 0:
        return
    tab.stop_event.set()
    tab.history_index -= 1
    url = tab.history[tab.history_index]
    tab.current_url = url
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    load_page(record_history=False)


def go_forward(event=None):
    tab = get_current_tab()
    if not tab or tab.history_index >= len(tab.history) - 1:
        return
    tab.stop_event.set()
    tab.history_index += 1
    url = tab.history[tab.history_index]
    tab.current_url = url
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    load_page(record_history=False)


def go_home():
    tab = get_current_tab()
    if not tab:
        return
    tab.stop_event.set()
    address_bar.delete(0, tk.END)
    tab.render_welcome_screen()
    update_status("Página inicial.")


def stop_loading(event=None):
    tab = get_current_tab()
    if tab:
        tab.stop_event.set()
        tab.loading = False
    update_status("Carregamento interrompido.")
    update_progress(0, show=False)
    set_busy(False)


def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))


# ============================================================
# HTTP / file loading helpers
# ============================================================

def display_error(tab, title, detail):
    def _show():
        try:
            tab.viewer.configure(state=tk.NORMAL)
            tab.viewer.delete("1.0", tk.END)
            tab.viewer.insert(tk.END, f"{title}\n\n{detail}")
            tab.viewer.configure(state=tk.DISABLED)
        except tk.TclError:
            pass
    try:
        root.after(0, _show)
    except (RuntimeError, tk.TclError):
        pass


def classify_network_error(exc):
    if isinstance(exc, HTTPError):
        return f"Erro HTTP {exc.code}: {exc.reason}"
    if isinstance(exc, socket.gaierror):
        return "Erro DNS: o servidor não pôde ser encontrado."
    if isinstance(exc, ConnectionRefusedError):
        return "Conexão recusada pelo servidor."
    if isinstance(exc, TimeoutError) or isinstance(exc, socket.timeout):
        return "Tempo limite de conexão excedido."
    if isinstance(exc, ssl.SSLError):
        return f"Erro TLS: {exc}"
    if isinstance(exc, URLError):
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, socket.gaierror):
            return "Erro DNS: o servidor não pôde ser encontrado."
        return f"Erro de rede: {reason}"
    if isinstance(exc, ValueError):
        return f"URL inválida: {exc}"
    return f"Erro: {exc}"


def load_file_url(tab, url):
    try:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        if sys.platform.startswith("win") and re.match(r"^/[A-Za-z]:", path):
            path = path[1:]
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        ext = os.path.splitext(path)[1].lower()
        if ext not in (".html", ".htm", ".xhtml", ".txt", ".gmi"):
            if not messagebox.askyesno(
                "Arquivo local",
                "Este arquivo não é HTML/texto.\nDeseja tentar abri-lo como texto?",
            ):
                return

        # file:// is intentionally restricted to regular local files.
        with open(path, "rb") as f:
            raw = f.read(MAX_DOWNLOAD_SIZE + 1)
        if len(raw) > MAX_DOWNLOAD_SIZE:
            raise ValueError("Arquivo local excede o limite permitido.")

        text = raw.decode("utf-8", errors="replace")
        tab.raw_content = text
        tab.viewer.configure(state=tk.NORMAL)
        tab.viewer.delete("1.0", tk.END)
        parser = SimpleHTMLParser(tab.viewer, url)
        parser.feed(text)
        tab.viewer.configure(state=tk.DISABLED)
        update_status("Concluído")
        log_info(f"Arquivo local acessado: {path}")
    except FileNotFoundError:
        display_error(tab, "Arquivo inexistente", url)
        update_status("Erro: arquivo inexistente.")
    except (OSError, ValueError) as exc:
        display_error(tab, "Erro ao abrir arquivo local", str(exc))
        update_status("Erro ao abrir arquivo local.")


def _fetch_http_thread(tab, url, job_event, force_reload):
    try:
        update_status("Conectando...")
        update_progress(10)
        req = Request(
            url,
            headers={"User-Agent": "Browser98/1.2 (Retro Engine)"},
        )
        with urlopen(req, timeout=10) as response:
            total_header = response.headers.get("Content-Length")
            total = None
            if total_header:
                try:
                    total = int(total_header)
                except ValueError:
                    total = None
            if total is not None and total > MAX_DOWNLOAD_SIZE:
                raise ValueError("Página excede o limite de tamanho.")

            data = bytearray()
            downloaded = 0
            while not job_event.is_set():
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                data.extend(chunk)
                downloaded += len(chunk)
                if downloaded > MAX_DOWNLOAD_SIZE:
                    raise ValueError("Página excede o limite de tamanho.")
                if total:
                    update_progress(10 + (downloaded / total) * 70)
                else:
                    update_progress(40, show=True)
                update_status(f"Baixando... {downloaded / 1024:.1f} KB")

        if job_event.is_set():
            return

        update_status("Processando...")
        try:
            text = bytes(data).decode("utf-8")
        except UnicodeDecodeError:
            text = bytes(data).decode("latin-1", errors="replace")

        put_page_cache(url, text)
        log_info(f"URL acessada: HTTP(S) {url}")
        root.after(0, lambda: _render_http_result(tab, url, text))
    except Exception as exc:
        if job_event.is_set():
            return
        log_error(f"HTTP {url}: {exc}")
        root.after(0, lambda e=exc: _render_http_error(tab, e))


def _render_http_result(tab, url, text):
    try:
        tab.viewer.configure(state=tk.NORMAL)
        tab.viewer.delete("1.0", tk.END)
        parser = SimpleHTMLParser(tab.viewer, url)
        parser.feed(text)
        tab.viewer.configure(state=tk.DISABLED)
        if parser.page_title.strip():
            notebook.tab(tab.frame, text=parser.page_title.strip()[:15])
        update_status("Concluído")
        update_progress(100)
        root.after(250, lambda: update_progress(0, show=False))
    except tk.TclError as exc:
        log_error(f"Erro do parser: {exc}")
        display_error(tab, "Erro do parser HTML", str(exc))


def _render_http_error(tab, exc):
    detail = classify_network_error(exc)
    display_error(tab, "Erro de Conexão HTTP/HTTPS", detail)
    update_status("Erro")
    update_progress(0, show=False)


# ============================================================
# Gemini
# ============================================================

def gemini_context():
    if TLS_VERIFY:
        return ssl.create_default_context()
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.set_ciphers("DEFAULT@SECLEVEL=1")
    return context


def render_gemini(tab, url, redirects=0):
    if redirects > MAX_REDIRECTS:
        display_error(tab, "Gemini", "Limite de redirecionamentos excedido.")
        update_status("Erro: muitos redirecionamentos.")
        return

    tab.viewer.configure(state=tk.NORMAL)
    tab.viewer.delete("1.0", tk.END)
    tab.loading = True
    tab.stop_event.clear()
    job_event = tab.stop_event

    def worker():
        try:
            parsed = urlparse(url)
            host = parsed.hostname
            if not host:
                raise ValueError("Servidor Gemini inválido.")
            port = parsed.port or 1965
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query

            update_status("Conectando...")
            update_progress(20)

            context = gemini_context()
            try:
                raw = socket.create_connection((host, port), timeout=10)
                ssock = context.wrap_socket(raw, server_hostname=host)
                tls_unverified = not TLS_VERIFY
            except ssl.SSLCertVerificationError as exc:
                # Never open Tk dialogs from the network worker.
                decision = {"value": None}
                done = threading.Event()

                def ask_tls_compat():
                    decision["value"] = messagebox.askyesno(
                        "Certificado TLS inválido",
                        "A validação TLS falhou.\n\n"
                        f"{exc}\n\n"
                        "Deseja usar o modo de compatibilidade sem validação?",
                    )
                    done.set()

                root.after(0, ask_tls_compat)
                done.wait()

                if not decision["value"]:
                    raise

                compat = ssl.create_default_context()
                compat.check_hostname = False
                compat.verify_mode = ssl.CERT_NONE
                compat.set_ciphers("DEFAULT@SECLEVEL=1")
                raw = socket.create_connection((host, port), timeout=10)
                ssock = compat.wrap_socket(raw, server_hostname=host)
                tls_unverified = True

            with ssock:
                ssock.settimeout(10)
                ssock.sendall(f"gemini://{host}{path}\r\n".encode("utf-8"))
                response = bytearray()
                while not job_event.is_set():
                    chunk = ssock.recv(4096)
                    if not chunk:
                        break
                    response.extend(chunk)
                    if len(response) > MAX_DOWNLOAD_SIZE:
                        raise ValueError("Resposta Gemini excede o limite.")

            if job_event.is_set():
                return

            text = bytes(response).decode("utf-8", errors="replace")
            if "\r\n" not in text:
                raise ValueError("Resposta Gemini inválida: cabeçalho ausente.")

            header, body = text.split("\r\n", 1)
            match = re.match(r"^(\d\d)\s?(.*)$", header)
            if not match:
                raise ValueError("Código de status Gemini inválido.")

            status = match.group(1)
            meta = match.group(2).strip()
            log_info(f"Gemini {url} -> {status}")

            if tls_unverified:
                status_message = f"Gemini {status} | TLS SEM VALIDAÇÃO"
            else:
                status_message = f"Gemini {status} | TLS validado"
            update_status(status_message)

            if status.startswith("1"):
                prompt = meta or "Digite o termo de pesquisa:"
                root.after(0, lambda: _gemini_input(tab, host, path, prompt))
                return
            if status.startswith("2"):
                put_page_cache(url, body)
                root.after(
                    0,
                    lambda: _render_gemini_body(tab, url, body, status_message),
                )
                return
            if status.startswith("3"):
                if redirects >= MAX_REDIRECTS:
                    raise ValueError("Limite de redirecionamentos excedido.")
                target = safe_urljoin(url, meta)
                root.after(
                    0,
                    lambda: _gemini_redirect(tab, target, redirects + 1),
                )
                return
            if status.startswith("4"):
                raise ValueError(f"Temporário: {status} {meta}")
            if status.startswith("5"):
                raise ValueError(f"Servidor Gemini recusou: {status} {meta}")
            if status.startswith("6"):
                raise ValueError(f"Erro de certificado: {status} {meta}")
            raise ValueError(f"Status Gemini desconhecido: {status} {meta}")
        except Exception as exc:
            if job_event.is_set():
                return
            log_error(f"Gemini {url}: {exc}")
            root.after(0, lambda e=exc: _render_gemini_error(tab, e))
        finally:
            tab.loading = False
            update_progress(0, show=False)

    threading.Thread(target=worker, daemon=True).start()


def _gemini_input(tab, host, path, prompt):
    value = simpledialog.askstring("Gemini Busca", prompt)
    if value:
        query = quote(value, safe="")
        target = f"gemini://{host}{path}"
        target += ("&" if "?" in target else "?") + query
        address_bar.delete(0, tk.END)
        address_bar.insert(0, target)
        load_page()


def _gemini_redirect(tab, target, redirects):
    address_bar.delete(0, tk.END)
    address_bar.insert(0, target)
    load_page(record_history=False, redirect_count=redirects)


def _render_gemini_body(tab, url, body, status_message):
    tab.raw_content = body
    tab.viewer.configure(state=tk.NORMAL)
    tab.viewer.delete("1.0", tk.END)
    parse_gemtext(tab, body, url)
    tab.viewer.configure(state=tk.DISABLED)
    update_status(f"Concluído | {status_message}")


def _render_gemini_error(tab, exc):
    display_error(tab, "Erro de Conexão Gemini", classify_network_error(exc))
    update_status("Erro")


def parse_gemtext(tab, text, base_url):
    in_pre = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_pre = not in_pre
            continue
        if in_pre:
            tab.viewer.insert(tk.END, line + "\n", ["pre", "mono"])
            continue
        if line.startswith("=>"):
            parts = line[2:].strip().split(None, 1)
            if parts:
                try:
                    link_url = safe_urljoin(base_url, parts[0])
                except ValueError:
                    continue
                label = parts[1] if len(parts) > 1 else parts[0]
                start = tab.viewer.index(tk.END)
                tab.viewer.insert(tk.END, "\n" + label, ["link"])
                end = tab.viewer.index(tk.END)
                tag = f"gemini_link_{start}"
                tab.viewer.tag_add(tag, start, end)
                tab.viewer.tag_bind(
                    tag, "<Button-1>",
                    lambda e, u=link_url: open_link_in_current_tab(u)
                )
                tab.viewer.tag_bind(
                    tag, "<Enter>",
                    lambda e: tab.viewer.config(cursor="hand2")
                )
                tab.viewer.tag_bind(
                    tag, "<Leave>",
                    lambda e: tab.viewer.config(cursor="xterm")
                )
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


# ============================================================
# Gopher
# ============================================================

def render_gopher(tab, url):
    tab.viewer.configure(state=tk.NORMAL)
    tab.viewer.delete("1.0", tk.END)
    tab.loading = True
    tab.stop_event.clear()
    event = tab.stop_event

    def worker():
        try:
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 70
            selector = parsed.path or ""
            if parsed.query:
                selector += "\t" + parsed.query

            update_status("Conectando...")
            update_progress(20)

            with socket.create_connection((host, port), timeout=8) as sock:
                sock.settimeout(8)
                sock.sendall((selector + "\r\n").encode("utf-8"))
                response = bytearray()
                while not event.is_set():
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response.extend(chunk)
                    if len(response) > MAX_DOWNLOAD_SIZE:
                        raise ValueError("Resposta Gopher excede o limite.")

            if event.is_set():
                return

            content = bytes(response).decode("utf-8", errors="replace")
            put_page_cache(url, content)
            log_info(f"Gopher {url}")
            root.after(0, lambda: _render_gopher_result(tab, url, content))
        except Exception as exc:
            if event.is_set():
                return
            log_error(f"Gopher {url}: {exc}")
            display_error(tab, "Erro de Conexão Gopher", classify_network_error(exc))
            update_status("Erro")
        finally:
            tab.loading = False
            update_progress(0, show=False)

    threading.Thread(target=worker, daemon=True).start()


def _render_gopher_result(tab, url, content):
    tab.raw_content = content
    parse_gopher_menu(tab, content, url)
    tab.viewer.configure(state=tk.DISABLED)
    update_status("Concluído")


def parse_gopher_menu(tab, text, base_url):
    for line in text.splitlines():
        if not line or line == ".":
            continue
        type_char = line[0]
        parts = line[1:].split("\t")
        if len(parts) < 3:
            tab.viewer.insert(tk.END, line + "\n")
            continue

        display_string = parts[0]
        selector = parts[1]
        host = parts[2]
        port = parts[3] if len(parts) > 3 and parts[3].isdigit() else "70"

        gopher_url = (
            f"gopher://{host}:{port}/{type_char}{selector}"
        )

        prefix_map = {
            "0": "[TXT] ",
            "1": "[DIR] ",
            "7": "[BUSCA] ",
            "4": "[MACRO] ",
            "5": "[DOS] ",
            "9": "[BIN] ",
            "I": "[IMG] ",
            "g": "[GIF] ",
            "h": "[URL] ",
        }
        prefix = prefix_map.get(type_char, "[ITEM] ")

        start = tab.viewer.index(tk.END)
        tab.viewer.insert(tk.END, prefix + display_string + "\n", ["link"])
        end = tab.viewer.index(tk.END)
        tag = f"gopher_{start}"
        tab.viewer.tag_add(tag, start, end)

        if type_char == "7":
            tab.viewer.tag_bind(
                tag, "<Button-1>",
                lambda e, u=gopher_url: gopher_search_query(u)
            )
        elif type_char == "h":
            try:
                target = urljoin(base_url, selector)
                tab.viewer.tag_bind(
                    tag, "<Button-1>",
                    lambda e, u=target: open_link_in_current_tab(u)
                )
            except Exception:
                pass
        elif type_char in ("4", "5", "9", "I", "g"):
            tab.viewer.tag_bind(
                tag, "<Button-1>",
                lambda e, u=gopher_url: download_file(u)
            )
        else:
            tab.viewer.tag_bind(
                tag, "<Button-1>",
                lambda e, u=gopher_url: open_link_in_current_tab(u)
            )

        tab.viewer.tag_bind(
            tag, "<Enter>", lambda e: tab.viewer.config(cursor="hand2")
        )
        tab.viewer.tag_bind(
            tag, "<Leave>", lambda e: tab.viewer.config(cursor="xterm")
        )


def gopher_search_query(url):
    query = simpledialog.askstring("Gopher Search", "Digite o termo de pesquisa:")
    if query:
        parsed = urlparse(url)
        target = url.split("?", 1)[0]
        target += ("?" if "?" not in target else "&") + quote(query)
        open_link_in_current_tab(target)


# ============================================================
# Downloads
# ============================================================

def download_gopher_file(url):
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 70
    selector = parsed.path or ""
    filename = os.path.basename(unquote(selector)) or "gopher_download"

    save_path = filedialog.asksaveasfilename(
        initialdir=DOWNLOAD_FOLDER,
        initialfile=filename,
    )
    if not save_path:
        return

    cancel_event = threading.Event()

    def worker():
        downloaded = 0
        try:
            update_status("Baixando Gopher...")
            with socket.create_connection((host, port), timeout=10) as sock:
                sock.settimeout(10)
                sock.sendall((selector + "\r\n").encode("utf-8"))

                with open(save_path, "wb") as out:
                    while not cancel_event.is_set():
                        chunk = sock.recv(DOWNLOAD_BLOCK_SIZE)
                        if not chunk:
                            break
                        out.write(chunk)
                        downloaded += len(chunk)
                        update_status(
                            f"Baixando Gopher... "
                            f"{downloaded / 1024 / 1024:.2f} MB"
                        )

            if cancel_event.is_set():
                try:
                    os.remove(save_path)
                except OSError:
                    pass
                update_status("Download Gopher cancelado.")
                return

            log_info(f"Download Gopher concluído: {url} | {downloaded} bytes")
            root.after(
                0,
                lambda: messagebox.showinfo(
                    "Browser 98",
                    f"Download Gopher concluído.\\n\\n{save_path}"
                ),
            )
            update_status("Download Gopher concluído.")
        except Exception as exc:
            log_error(f"Download Gopher {url}: {exc}")
            root.after(
                0,
                lambda e=exc: messagebox.showerror(
                    "Erro de download Gopher",
                    classify_network_error(e)
                ),
            )

    threading.Thread(target=worker, daemon=True).start()


def cancel_download(download_id):
    job = active_downloads.get(download_id)
    if job:
        job["event"].set()
        update_status("Cancelando download...")


def download_file(url):
    scheme = urlparse(url).scheme.lower()
    if scheme == "gopher":
        download_gopher_file(url)
        return
    if scheme not in ("http", "https", "file"):
        messagebox.showerror(
            "Download",
            "Este protocolo não possui um método de download implementado."
        )
        return

    filename = os.path.basename(unquote(urlparse(url).path)) or "arquivo_download"
    if not os.path.splitext(filename)[1]:
        filename += ".download"

    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    save_path = filedialog.asksaveasfilename(
        initialdir=DOWNLOAD_FOLDER,
        initialfile=filename,
    )
    if not save_path:
        return

    download_id = str(time.time_ns())
    event = threading.Event()
    active_downloads[download_id] = {"event": event, "filename": filename}

    def run_download():
        start = time.monotonic()
        downloaded = 0
        try:
            update_status(f"Conectando... {filename}")
            req = Request(url, headers={"User-Agent": "Browser98/1.2"})
            with urlopen(req, timeout=15) as response:
                total_header = response.headers.get("Content-Length")
                total = None
                if total_header:
                    try:
                        total = int(total_header)
                    except ValueError:
                        total = None
                if total is not None and total > MAX_DOWNLOAD_SIZE:
                    raise ValueError("Download excede o limite permitido.")

                with open(save_path, "wb") as out:
                    while not event.is_set():
                        chunk = response.read(DOWNLOAD_BLOCK_SIZE)
                        if not chunk:
                            break
                        out.write(chunk)
                        downloaded += len(chunk)
                        if downloaded > MAX_DOWNLOAD_SIZE:
                            raise ValueError("Download excede o limite permitido.")

                        elapsed = max(0.001, time.monotonic() - start)
                        speed = downloaded / elapsed
                        speed_kb = speed / 1024

                        if total:
                            pct = downloaded / total * 100
                            update_progress(pct)
                            update_status(
                                f"Baixando... {downloaded / 1024 / 1024:.2f} MB / "
                                f"{total / 1024 / 1024:.2f} MB | "
                                f"{speed_kb:.1f} KB/s"
                            )
                        else:
                            update_progress(50)
                            update_status(
                                f"Baixando... {downloaded / 1024 / 1024:.2f} MB | "
                                f"{speed_kb:.1f} KB/s"
                            )

            if event.is_set():
                try:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                except OSError:
                    pass
                update_status("Download cancelado.")
                return

            elapsed = max(0.001, time.monotonic() - start)
            log_info(
                f"Download concluído: {url} | "
                f"{downloaded} bytes | {downloaded / elapsed:.0f} B/s"
            )
            update_status(f"Download concluído: {filename}")
            root.after(
                0,
                lambda: messagebox.showinfo(
                    "Browser 98",
                    f"Download concluído!\n\n{save_path}\n"
                    f"{downloaded / 1024 / 1024:.2f} MB",
                ),
            )
        except Exception as exc:
            if event.is_set():
                update_status("Download cancelado.")
            else:
                log_error(f"Download {url}: {exc}")
                update_status("Erro no download.")
                root.after(
                    0,
                    lambda e=exc: messagebox.showerror(
                        "Erro de download", classify_network_error(e)
                    ),
                )
        finally:
            active_downloads.pop(download_id, None)
            update_progress(0, show=False)

    cancel_window = tk.Toplevel(root)
    cancel_window.title("Download")
    cancel_window.resizable(False, False)
    ttk.Label(
        cancel_window,
        text=f"Baixando:\n{filename}",
        padding=10,
    ).pack()
    ttk.Button(
        cancel_window,
        text="Cancelar",
        command=lambda: cancel_download(download_id),
    ).pack(pady=(0, 10))

    def monitor():
        if download_id in active_downloads and cancel_window.winfo_exists():
            cancel_window.after(300, monitor)
        elif cancel_window.winfo_exists():
            cancel_window.destroy()

    cancel_window.after(300, monitor)
    threading.Thread(target=run_download, daemon=True).start()


# ============================================================
# Internal pages
# ============================================================

def render_internal_favorites(tab):
    tab.viewer.configure(state=tk.NORMAL)
    tab.viewer.delete("1.0", tk.END)
    tab.viewer.insert(tk.END, "⭐ Meus Favoritos\n", ["h1"])
    tab.viewer.insert(tk.END, "=" * 50 + "\n\n")
    favs = read_favorites()
    if not favs:
        tab.viewer.insert(tk.END, "Nenhum favorito encontrado.\n")
    for fav in favs:
        start = tab.viewer.index(tk.END)
        tab.viewer.insert(tk.END, f"• {fav}\n", ["link"])
        end = tab.viewer.index(tk.END)
        tag = f"fav_{start}"
        tab.viewer.tag_add(tag, start, end)
        tab.viewer.tag_bind(
            tag, "<Button-1>",
            lambda e, u=fav: open_link_in_current_tab(u)
        )
    tab.viewer.configure(state=tk.DISABLED)
    notebook.tab(tab.frame, text="Favoritos")


def render_internal_history(tab):
    tab.viewer.configure(state=tk.NORMAL)
    tab.viewer.delete("1.0", tk.END)
    tab.viewer.insert(tk.END, "📜 Histórico de Navegação\n", ["h1"])
    tab.viewer.insert(tk.END, "=" * 50 + "\n\n")
    if not history_store:
        tab.viewer.insert(tk.END, "Nenhum histórico salvo.\n")
    for entry in reversed(history_store[-200:]):
        start = tab.viewer.index(tk.END)
        tab.viewer.insert(tk.END, f"• {entry}\n", ["link"])
        end = tab.viewer.index(tk.END)
        tag = f"hist_{start}"
        tab.viewer.tag_add(tag, start, end)
        tab.viewer.tag_bind(
            tag, "<Button-1>",
            lambda e, u=entry: open_link_in_current_tab(u)
        )
    tab.viewer.configure(state=tk.DISABLED)
    notebook.tab(tab.frame, text="Histórico")


# ============================================================
# Find in page
# ============================================================

find_state = {"query": "", "last": "1.0"}


def find_in_page(event=None):
    tab = get_current_tab()
    if not tab:
        return

    query = simpledialog.askstring(
        "Localizar",
        "Digite o termo para buscar na página:",
        initialvalue=find_state["query"],
    )
    if not query:
        return

    find_state["query"] = query
    find_state["last"] = "1.0"
    find_next()


def find_next():
    tab = get_current_tab()
    query = find_state["query"]
    if not tab or not query:
        return
    tab.viewer.tag_remove("highlight", "1.0", tk.END)
    idx = tab.viewer.search(
        query,
        find_state["last"],
        nocase=True,
        stopindex=tk.END,
    )
    if not idx:
        idx = tab.viewer.search(
            query, "1.0", nocase=True, stopindex=tk.END
        )
    if idx:
        end = f"{idx}+{len(query)}c"
        tab.viewer.tag_add("highlight", idx, end)
        tab.viewer.see(idx)
        find_state["last"] = end
        update_status(f"Encontrado: {query}")
    else:
        update_status(f"Não encontrado: {query}")


def find_previous():
    tab = get_current_tab()
    query = find_state["query"]
    if not tab or not query:
        return
    tab.viewer.tag_remove("highlight", "1.0", tk.END)
    idx = tab.viewer.search(
        query,
        find_state["last"],
        backwards=True,
        nocase=True,
        stopindex="1.0",
    )
    if idx:
        end = f"{idx}+{len(query)}c"
        tab.viewer.tag_add("highlight", idx, end)
        tab.viewer.see(idx)
        find_state["last"] = idx
        update_status(f"Encontrado: {query}")
    else:
        update_status(f"Não encontrado: {query}")


# ============================================================
# Source / themes / settings
# ============================================================

def view_source(event=None):
    tab = get_current_tab()
    if not tab:
        return
    content = tab.raw_content or "[Sem código fonte disponível]"
    new_tab = create_new_tab(title="Código Fonte")
    new_tab.viewer.configure(state=tk.NORMAL)
    new_tab.viewer.delete("1.0", tk.END)
    new_tab.viewer.insert(tk.END, content, ["pre", "mono"])
    new_tab.viewer.configure(state=tk.DISABLED)


def set_theme(theme_name):
    global CURRENT_THEME
    if theme_name not in THEMES:
        return
    CURRENT_THEME = theme_name
    for tab in tabs:
        tab.apply_theme()
    save_config()
    update_status(f"Tema: {theme_name}")


def change_font_size():
    global FONT_SIZE
    value = simpledialog.askinteger(
        "Tamanho da fonte",
        "Escolha o tamanho da fonte (7 a 32):",
        initialvalue=FONT_SIZE,
        minvalue=7,
        maxvalue=32,
    )
    if value:
        FONT_SIZE = value
        for tab in tabs:
            tab.apply_theme()
        save_config()


def change_cache_limit():
    global MAX_CACHE_SIZE
    value = simpledialog.askinteger(
        "Limite do cache",
        "Limite em MB (1 a 2048):",
        initialvalue=MAX_CACHE_SIZE // (1024 * 1024),
        minvalue=1,
        maxvalue=2048,
    )
    if value:
        MAX_CACHE_SIZE = value * 1024 * 1024
        while current_cache_size > MAX_CACHE_SIZE and page_cache:
            _remove_page_cache(next(iter(page_cache)))
        save_config()
        update_status(f"Limite do cache: {value} MB")


def choose_download_folder():
    global DOWNLOAD_FOLDER
    path = filedialog.askdirectory(initialdir=DOWNLOAD_FOLDER)
    if path:
        DOWNLOAD_FOLDER = path
        save_config()


def toggle_logging():
    global LOG_ENABLED
    LOG_ENABLED = not LOG_ENABLED
    configure_logging()
    save_config()
    update_status("Logs " + ("ativados." if LOG_ENABLED else "desativados."))


def toggle_tls():
    global TLS_VERIFY
    TLS_VERIFY = not TLS_VERIFY
    save_config()
    update_status(
        "TLS padrão: " + ("verificação ativada." if TLS_VERIFY else "modo compatibilidade.")
    )


def settings_dialog():
    new_tab = create_new_tab(title="Configurações")
    
    frame = ttk.Frame(new_tab.frame, padding=12)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Página inicial:").pack(anchor="w")
    home_entry = ttk.Entry(frame)
    home_entry.pack(fill=tk.X, pady=(0, 8))
    home_entry.insert(0, homepage)

    ttk.Label(frame, text="Tema:").pack(anchor="w")
    theme_var = tk.StringVar(value=CURRENT_THEME)
    ttk.Combobox(
        frame,
        textvariable=theme_var,
        values=list(THEMES.keys()),
        state="readonly",
    ).pack(fill=tk.X, pady=(0, 8))

    ttk.Label(frame, text="Tamanho da fonte:").pack(anchor="w")
    font_var = tk.IntVar(value=FONT_SIZE)
    ttk.Spinbox(
        frame, from_=7, to=32, textvariable=font_var
    ).pack(fill=tk.X, pady=(0, 8))

    ttk.Label(frame, text="Limite do cache (MB):").pack(anchor="w")
    cache_var = tk.IntVar(value=MAX_CACHE_SIZE // (1024 * 1024))
    ttk.Spinbox(
        frame, from_=1, to=2048, textvariable=cache_var
    ).pack(fill=tk.X, pady=(0, 8))

    def apply():
        global homepage, FONT_SIZE, CURRENT_THEME, MAX_CACHE_SIZE
        homepage = home_entry.get().strip() or DEFAULT_HOMEPAGE
        try:
            FONT_SIZE = max(7, min(32, int(font_var.get())))
            limit = max(1, min(2048, int(cache_var.get())))
        except (ValueError, tk.TclError):
            messagebox.showerror("Configurações", "Valores inválidos.")
            return
        CURRENT_THEME = theme_var.get()
        MAX_CACHE_SIZE = limit * 1024 * 1024
        while current_cache_size > MAX_CACHE_SIZE and page_cache:
            _remove_page_cache(next(iter(page_cache)))
        for tab in tabs:
            tab.apply_theme()
        save_config()
        close_current_tab()
        update_status("Configurações salvas.")

    ttk.Button(frame, text="Salvar", command=apply).pack(pady=8)
    ttk.Button(frame, text="Cancelar", command=close_current_tab).pack()


# ============================================================
# Page loading coordinator
# ============================================================

def load_page(force_reload=False, record_history=True, redirect_count=0):
    tab = get_current_tab()
    if not tab:
        return

    raw_url = address_bar.get().strip()
    if not raw_url:
        tab.render_welcome_screen()
        return

    try:
        url = normalize_url(raw_url)
    except ValueError as exc:
        display_error(tab, "URL inválida", str(exc))
        update_status("Erro")
        return

    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    tab.current_url = url
    tab.apply_theme()
    tab.stop_event.set()
    tab.stop_event = threading.Event()

    if record_history:
        if not tab.history or tab.history[tab.history_index] != url:
            tab.history = tab.history[: tab.history_index + 1]
            tab.history.append(url)
            tab.history_index += 1
            save_history(url)

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path or "Página"
    notebook.tab(tab.frame, text=domain[:15])

    if url == "browser98://favorites":
        render_internal_favorites(tab)
        return
    if url == "browser98://history":
        render_internal_history(tab)
        return

    if force_reload:
        _remove_page_cache(url)

    if url.startswith("file://"):
        load_file_url(tab, url)
        return

    if url.startswith("gemini://"):
        render_gemini(tab, url, redirect_count)
        return

    if url.startswith("gopher://"):
        render_gopher(tab, url)
        return

    if url in page_cache and not force_reload:
        text = page_cache[url]
        tab.raw_content = text
        tab.viewer.configure(state=tk.NORMAL)
        tab.viewer.delete("1.0", tk.END)
        parser = SimpleHTMLParser(tab.viewer, url)
        parser.feed(text)
        tab.viewer.configure(state=tk.DISABLED)
        update_status("Concluído (Cache)")
        return

    tab.loading = True
    update_status("Conectando...")
    set_busy(True)
    threading.Thread(
        target=_fetch_http_thread,
        args=(tab, url, tab.stop_event, force_reload),
        daemon=True,
    ).start()


def reload_page(event=None):
    load_page(force_reload=False)


def reload_ignore_cache(event=None):
    load_page(force_reload=True)


# ============================================================
# About
# ============================================================

def show_about():
    msg = (
        "<h1>Browser 98</h1>"
        "<p>Versão 1.2 (Build 2026)</p>"
        "<p>Python + Tkinter, com foco em Small Web e Internet Retrô.</p>"
        "<p><b>Novidades:</b></p>"
        "<ul>"
        "<li>Cache de páginas separado do cache de imagens</li>"
        "<li>Histórico persistente em historico.txt</li>"
        "<li>Favoritos sem duplicação, edição, remoção e importação/exportação</li>"
        "<li>Downloads em blocos com progresso, velocidade e cancelamento</li>"
        "<li>Carregamento de rede em segundo plano</li>"
        "<li>HTMLParser com tabelas e formulários simples</li>"
        "<li>Imagens assíncronas com limite e referências seguras</li>"
        "<li>Gemini com status, redirecionamentos e TLS configurável</li>"
        "<li>Gopher com texto, diretórios, buscas e arquivos</li>"
        "<li>Suporte a file://</li>"
        "<li>Configurações, temas, zoom, F11 e atalhos</li>"
        "<li>Logs opcionais e tratamento de erros mais específico</li>"
        "</ul>"
        "<p>JavaScript: não implementado por decisão de projeto.</p>"
        "<p>Licença: GNU GPL v3</p>"
    )
    new_tab = create_new_tab(title="Sobre")
    new_tab.viewer.configure(state=tk.NORMAL)
    new_tab.viewer.delete("1.0", tk.END)
    parser = SimpleHTMLParser(new_tab.viewer, "")
    parser.feed(msg)
    new_tab.viewer.configure(state=tk.DISABLED)


# ============================================================
# GUI
# ============================================================

root = tk.Tk()
root.title(f"Browser 98 v{APP_VERSION}")
root.geometry("760x570")
root.minsize(520, 350)

style = ttk.Style()
style.theme_use('default')
style.configure("XP.Horizontal.TProgressbar", thickness=14, bordercolor="#003399", lightcolor="#0066ff", darkcolor="#002288")

# Keyboard shortcuts
root.bind("<Control-l>", lambda e: (address_bar.focus_set(), address_bar.select_range(0, tk.END)))
root.bind("<Control-r>", reload_page)
root.bind("<Control-Shift-r>", reload_ignore_cache)
root.bind("<F5>", reload_page)
root.bind("<F11>", toggle_fullscreen)
root.bind("<Escape>", stop_loading)
root.bind("<Alt-Left>", go_back)
root.bind("<Alt-Right>", go_forward)
root.bind("<Control-d>", lambda e: add_favorite())
root.bind("<Control-f>", find_in_page)
root.bind("<Control-t>", lambda e: create_new_tab())
root.bind("<Control-w>", lambda e: close_current_tab())
root.bind("<Control-u>", view_source)
root.bind("<Control-plus>", lambda e: get_current_tab().zoom_in())
root.bind("<Control-minus>", lambda e: get_current_tab().zoom_out())
root.bind("<Control-0>", lambda e: get_current_tab().zoom_reset())

menu_bar = tk.Menu(root)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Nova Aba (Ctrl+T)", command=create_new_tab)
file_menu.add_command(label="Fechar Aba (Ctrl+W)", command=close_current_tab)
file_menu.add_separator()
file_menu.add_command(label="Página Inicial", command=go_home)
file_menu.add_command(label="Abrir arquivo local...", command=lambda: open_local_file())
file_menu.add_separator()
file_menu.add_command(label="Sair", command=root.quit)
menu_bar.add_cascade(label="Arquivo", menu=file_menu)

nav_menu = tk.Menu(menu_bar, tearoff=0)
nav_menu.add_command(label="Voltar (Alt+←)", command=go_back)
nav_menu.add_command(label="Avançar (Alt+→)", command=go_forward)
nav_menu.add_command(label="Parar (Esc)", command=stop_loading)
nav_menu.add_command(label="Recarregar (F5 / Ctrl+R)", command=reload_page)
nav_menu.add_command(label="Recarregar ignorando cache (Ctrl+Shift+R)", command=reload_ignore_cache)
nav_menu.add_separator()
nav_menu.add_command(label="Histórico Completo", command=lambda: open_link_in_current_tab("browser98://history"))
nav_menu.add_command(label="Limpar Histórico", command=lambda: clear_history_confirm())
nav_menu.add_command(label="Localizar na Página (Ctrl+F)", command=find_in_page)
nav_menu.add_command(label="Ver Código Fonte (Ctrl+U)", command=view_source)
menu_bar.add_cascade(label="Navegação", menu=nav_menu)

view_menu = tk.Menu(menu_bar, tearoff=0)
for name in THEMES:
    view_menu.add_command(label=f"Tema: {name}", command=lambda n=name: set_theme(n))
view_menu.add_separator()
view_menu.add_command(label="Aumentar Zoom (Ctrl++)", command=lambda: get_current_tab().zoom_in())
view_menu.add_command(label="Reduzir Zoom (Ctrl+-)", command=lambda: get_current_tab().zoom_out())
view_menu.add_command(label="Zoom 100% (Ctrl+0)", command=lambda: get_current_tab().zoom_reset())
view_menu.add_command(label="Tela cheia (F11)", command=toggle_fullscreen)
menu_bar.add_cascade(label="Exibir", menu=view_menu)

favorites_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Favoritos", menu=favorites_menu)

settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Configurações...", command=settings_dialog)
settings_menu.add_command(label="Tamanho da fonte...", command=change_font_size)
settings_menu.add_command(label="Pasta de downloads...", command=choose_download_folder)
settings_menu.add_command(label="Limpar cache", command=clear_cache)
settings_menu.add_command(label="Informações do cache", command=lambda: messagebox.showinfo("Cache", cache_info_text()))
settings_menu.add_command(label="Alternar logs", command=toggle_logging)
settings_menu.add_command(label="Alternar verificação TLS padrão", command=toggle_tls)
menu_bar.add_cascade(label="Configurações", menu=settings_menu)

help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Sobre o Browser 98", command=show_about)
menu_bar.add_cascade(label="Ajuda", menu=help_menu)

root.config(menu=menu_bar)

btn_kwargs = {
    "bg": THEMES["Windows 98"]["button"],
    "activebackground": "#ece9d8",
    "relief": tk.RAISED,
    "bd": 2,
    "font": ("Tahoma", 8, "bold"),
    "padx": 4,
    "pady": 1,
}

top_container = tk.Frame(root, bg="#d4d0c8")
top_container.pack(fill=tk.X)

nav_toolbar = tk.Frame(top_container, bg="#d4d0c8", bd=1, relief=tk.RAISED)
nav_toolbar.pack(fill=tk.X)

tk.Button(nav_toolbar, text="Voltar", command=go_back, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(nav_toolbar, text="Avançar", command=go_forward, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(nav_toolbar, text="Parar", command=stop_loading, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(nav_toolbar, text="Recarregar", command=reload_page, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(nav_toolbar, text="Início", command=go_home, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)
tk.Button(nav_toolbar, text="+Aba", command=create_new_tab, **btn_kwargs).pack(side=tk.LEFT, padx=1, pady=2)

address_toolbar = tk.Frame(top_container, bg="#d4d0c8", bd=1, relief=tk.RAISED)
address_toolbar.pack(fill=tk.X)

address_bar = tk.Entry(address_toolbar, font=("Tahoma", 9), bd=2, relief=tk.SUNKEN)
address_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, pady=2)
address_bar.bind("<Return>", lambda e: load_page())

tk.Button(address_toolbar, text="Ir", command=load_page, **btn_kwargs).pack(side=tk.RIGHT, padx=1, pady=2)

progress_bar = ttk.Progressbar(
    top_container, orient="horizontal", mode="indeterminate", length=100, style="XP.Horizontal.TProgressbar"
)

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)
notebook.bind("<<NotebookTabChanged>>", update_address_bar_from_tab)

status_bar = tk.Label(
    root,
    text="Pronto",
    bd=1,
    relief=tk.SUNKEN,
    anchor=tk.W,
    font=("Courier", 9),
)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)


# ============================================================
# Menu helpers that need the GUI to exist
# ============================================================

def build_favorites_menu():
    favorites_menu.delete(0, tk.END)
    favorites_menu.add_command(
        label="⭐ Adicionar aos Favoritos (Ctrl+D)",
        command=add_favorite,
    )
    favorites_menu.add_command(
        label="📁 Abrir Favoritos",
        command=lambda: open_link_in_current_tab("browser98://favorites"),
    )
    favorites_menu.add_command(
        label="✏ Editar favorito",
        command=edit_favorite,
    )
    favorites_menu.add_command(
        label="🗑 Remover favorito",
        command=remove_favorite,
    )
    favorites_menu.add_separator()
    favorites_menu.add_command(label="📤 Exportar...", command=export_bookmarks)
    favorites_menu.add_command(label="📥 Importar...", command=import_bookmarks)
    favorites_menu.add_separator()
    for fav in read_favorites():
        favorites_menu.add_command(
            label=fav,
            command=lambda u=fav: open_link_in_current_tab(u),
        )


def clear_history_confirm():
    if messagebox.askyesno(
        "Histórico",
        "Deseja realmente limpar todo o histórico salvo?",
    ):
        clear_history()
        tab = get_current_tab()
        if tab and tab.current_url == "browser98://history":
            render_internal_history(tab)


def open_local_file():
    path = filedialog.askopenfilename(
        filetypes=[
            ("HTML", "*.html;*.htm;*.xhtml"),
            ("Texto", "*.txt"),
            ("Todos os arquivos", "*.*"),
        ]
    )
    if not path:
        return
    url = "file://" + path.replace("\\", "/")
    if sys.platform.startswith("win") and not url.startswith("file:///"):
        url = "file:///" + path.replace("\\", "/")
    address_bar.delete(0, tk.END)
    address_bar.insert(0, url)
    load_page()


# Load persistent history before creating the first tab.
load_history()
build_favorites_menu()
create_new_tab()

update_status("Pronto. Browser 98 v1.2.")

def on_close():
    for tab in tabs:
        tab.stop_event.set()
    save_config()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
