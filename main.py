import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import sqlite3
import os
import shutil
from datetime import datetime
import sys
import webbrowser
import subprocess
import importlib
import hashlib

def install_dependencies():
    """Instala as dependências necessárias automaticamente"""
    required_packages = {
        'pymupdf': 'fitz',
        'Pillow': 'PIL'
    }
    
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            if import_name == 'PIL':
                importlib.import_module('PIL.Image')
            else:
                importlib.import_module(import_name)
            print(f"✓ {package} já está instalado")
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Instalando dependências faltantes...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} instalado com sucesso")
            except subprocess.CalledProcessError:
                print(f"✗ Erro ao instalar {package}")
                return False
    return True

# Tentar instalar dependências antes de importar
if not install_dependencies():
    print("Não foi possível instalar todas as dependências.")
    input("Pressione Enter para sair...")
    sys.exit(1)

# Agora importar as bibliotecas
try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageTk
    import io
except ImportError as e:
    print(f"Erro crítico: {e}")
    input("Pressione Enter para sair...")
    sys.exit(1)

class ESITronicPDFManager:
    def __init__(self, root):
        self.root = root
        self.root.title("ESI[Tronic] PDF - Gerenciador de Documentações Técnicas")
        self.root.geometry("1300x750")
        self.root.configure(bg='#f0f0f0')
        
        # Configurar ícone (opcional)
        try:
            self.root.iconbitmap("pdf_icon.ico")
        except:
            pass
        
        # REMOVIDO: Variáveis para controle de zoom
        
        # Configuração do banco de dados
        self.setup_database()
        
        # Configuração da interface
        self.setup_ui()
        
        # Carregar PDFs
        self.load_pdfs()

    def setup_database(self):
        """Configura o banco de dados SQLite"""
        self.conn = sqlite3.connect('esitronic_pdf_manager.db')
        self.cursor = self.conn.cursor()
        
        # Criar tabela sem a coluna file_hash inicialmente
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pdfs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                display_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                date_added TEXT,
                tags TEXT,
                aplicacao TEXT
            )
        ''')
        
        # Verificar se a coluna file_hash existe e adicionar se necessário
        try:
            self.cursor.execute("SELECT file_hash FROM pdfs LIMIT 1")
        except sqlite3.OperationalError:
            # A coluna não existe, então adicionar sem constraint UNIQUE
            try:
                self.cursor.execute('ALTER TABLE pdfs ADD COLUMN file_hash TEXT')
                print("Coluna file_hash adicionada com sucesso")
            except sqlite3.OperationalError as e:
                print(f"Erro ao adicionar coluna file_hash: {e}")
        
        # Verificar se a coluna aplicacao existe
        try:
            self.cursor.execute("SELECT aplicacao FROM pdfs LIMIT 1")
        except sqlite3.OperationalError:
            # A coluna não existe, então adicionar
            try:
                self.cursor.execute('ALTER TABLE pdfs ADD COLUMN aplicacao TEXT')
                print("Coluna aplicacao adicionada com sucesso")
            except sqlite3.OperationalError as e:
                print(f"Erro ao adicionar coluna aplicacao: {e}")
        
        self.conn.commit()

    def calculate_file_hash(self, file_path):
        """Calcula o hash MD5 do arquivo para verificar duplicatas"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Erro ao calcular hash: {e}")
            return None

    def is_duplicate_file(self, file_path):
        """Verifica se o arquivo já existe no banco de dados"""
        try:
            # Verificar se a coluna file_hash existe
            self.cursor.execute("SELECT file_hash FROM pdfs LIMIT 1")
        except sqlite3.OperationalError:
            # Coluna não existe, usar verificação por nome como fallback
            filename = os.path.basename(file_path)
            display_name = os.path.splitext(filename)[0]
            self.cursor.execute('SELECT id FROM pdfs WHERE display_name = ?', (display_name,))
            return self.cursor.fetchone() is not None
        
        # Se a coluna file_hash existe, usar verificação por hash
        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return False
            
        self.cursor.execute('SELECT id FROM pdfs WHERE file_hash = ?', (file_hash,))
        return self.cursor.fetchone() is not None

    def setup_ui(self):
        """Configura a interface gráfica moderna"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(main_frame, bg='#2c3e50', height=100)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        # Título
        title_label = tk.Label(header_frame, text="📁 ESI[Tronic] PDF", 
                              font=('Arial', 22, 'bold'),
                              fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(side=tk.LEFT, padx=20, pady=20)

        # Subtítulo
        subtitle_label = tk.Label(header_frame, text="Gerenciador de Documentações Técnicas", 
                                 font=('Arial', 12),
                                 fg='#bdc3c7', bg='#2c3e50')
        subtitle_label.pack(side=tk.LEFT, pady=20)

        # Frame de controles
        controls_frame = tk.Frame(main_frame, bg='#ffffff')
        controls_frame.pack(fill=tk.X, pady=(0, 15))

        # Botões de ação com estilo moderno - EMOJIS ALINHADOS AO LADO DO TEXTO
        button_style = {
            'fg': 'white', 
            'font': ('Arial', 11, 'bold'),
            'bd': 0, 
            'padx': 15,
            'pady': 10,
            'cursor': 'hand2',
            'relief': 'flat'
        }

        # Frame para botões
        buttons_frame = tk.Frame(controls_frame, bg='#ffffff')
        buttons_frame.pack(side=tk.LEFT)

        # Botões com emojis alinhados ao lado do texto
        tk.Button(buttons_frame, text="📄 ADICIONAR PDF", 
                 command=self.add_pdf, bg='#3498db', 
                 **button_style).pack(side=tk.LEFT, padx=3)
        
        # BOTÃO: ABRIR
        tk.Button(buttons_frame, text="🌐 ABRIR", 
                 command=self.open_in_browser, 
                 bg='#1abc9c', **button_style).pack(side=tk.LEFT, padx=3)
        
        # BOTÃO: DOWNLOAD
        tk.Button(buttons_frame, text="📥 DOWNLOAD", 
                 command=self.download_pdf, 
                 bg='#f39c12', **button_style).pack(side=tk.LEFT, padx=3)
        
        # NOVO BOTÃO: APLICAÇÃO
        tk.Button(buttons_frame, text="🔧 APLICAÇÃO", 
                 command=self.edit_aplicacao, 
                 bg='#9b59b6', **button_style).pack(side=tk.LEFT, padx=3)
        
        tk.Button(buttons_frame, text="🗑️ EXCLUIR", 
                 command=self.delete_pdf, 
                 bg='#e74c3c', **button_style).pack(side=tk.LEFT, padx=3)

        # Frame de busca
        search_frame = tk.Frame(controls_frame, bg='#ffffff')
        search_frame.pack(side=tk.RIGHT)
        
        # Container para busca e botão X alinhados
        search_container = tk.Frame(search_frame, bg='#ffffff')
        search_container.pack(side=tk.RIGHT, pady=5)

        # Label de busca com emoji
        search_label = tk.Label(search_container, 
                text="🔍",  # Emoji de lupa
                font=('Arial', 14),  # Tamanho aumentado
                bg='#ffffff')
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(search_container, text="BUSCAR:", 
                font=('Arial', 12, 'bold'), bg='#ffffff').pack(side=tk.LEFT, padx=(0, 8))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var,
                                   font=('Arial', 11), width=30, relief='solid', bd=2,
                                   highlightthickness=1, highlightcolor='#3498db')
        self.search_entry.pack(side=tk.LEFT, padx=8, ipady=6)
        
        # Botão X com emoji
        clear_button = tk.Button(search_container, text="❌",  # Emoji X
                 command=self.clear_search,
                 bg='#95a5a6', fg='white', font=('Arial', 12),  # Fonte aumentada
                 width=3,  # Largura fixa para melhor alinhamento
                 padx=0, pady=0, cursor='hand2', relief='flat')
        clear_button.pack(side=tk.LEFT, padx=5)

        # CORREÇÃO: Usar trace para monitorar mudanças na busca
        self.search_var.trace("w", self.on_search)

        # Frame principal dividido
        content_frame = tk.Frame(main_frame, bg='#ffffff')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Frame da lista de PDFs (esquerda)
        list_frame = tk.Frame(content_frame, bg='#ffffff', width=700)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Frame do visualizador (direita) - inicialmente vazio
        self.viewer_frame = tk.Frame(content_frame, bg='#2c3e50', width=500)
        self.viewer_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.viewer_frame.pack_propagate(False)

        # Label inicial do visualizador com emoji
        self.viewer_label = tk.Label(self.viewer_frame, 
                                   text="👁️\n\nVisualizador de PDF\n\nSelecione um PDF na lista para visualizar",
                                   font=('Arial', 14), 
                                   fg='#ecf0f1', 
                                   bg='#2c3e50',
                                   justify=tk.CENTER)
        self.viewer_label.pack(expand=True)

        # Canvas para mostrar o PDF
        self.pdf_canvas = None
        self.current_pdf = None
        self.current_page = 0
        self.total_pages = 0
        self.current_pdf_id = None  # Para controlar qual PDF está aberto

        # Treeview com estilo moderno
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       background="#ffffff",
                       foreground="#2c3e50",
                       rowheight=30,
                       fieldbackground="#ffffff",
                       font=('Arial', 10))  # Fonte ligeiramente menor para caber mais colunas
        style.configure("Treeview.Heading", 
                       background="#34495e",
                       foreground="white",
                       font=('Arial', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#3498db')])

        # Colunas - ADICIONADA COLUNA 'APLICAÇÃO'
        columns = ('Nome', 'Aplicação', 'Tamanho', 'Data')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=16)

        # Configurar colunas COM MAIOR ESPAÇAMENTO E PADDING
        self.tree.heading('Nome', text='Nome do Documento')
        self.tree.heading('Aplicação', text='Aplicação')
        self.tree.heading('Tamanho', text='Tamanho')
        self.tree.heading('Data', text='Data de Adição')

        # LARGURAS DAS COLUNAS COM MAIS ESPAÇAMENTO E PADDING
        self.tree.column('Nome', width=300, anchor='w', minwidth=250, stretch=tk.YES)
        self.tree.column('Aplicação', width=200, anchor='w', minwidth=150, stretch=tk.YES)
        self.tree.column('Tamanho', width=100, anchor='center', minwidth=80, stretch=tk.NO)
        self.tree.column('Data', width=120, anchor='center', minwidth=100, stretch=tk.NO)

        # Scrollbars para a lista
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Empacotar lista
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind events - AGORA ABRE AUTOMATICAMENTE AO CLICAR
        self.tree.bind('<<TreeviewSelect>>', self.on_item_selected)
        self.tree.bind('<Double-1>', self.open_pdf)  # Duplo-clique abre no programa padrão
        self.tree.bind('<Delete>', lambda e: self.delete_pdf())

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto - Selecione um PDF para visualizar automaticamente")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                             font=('Arial', 10), bg='#ecf0f1', fg='#2c3e50', 
                             anchor=tk.W, relief='sunken', bd=1)
        status_bar.pack(fill=tk.X, pady=(15, 0))

    def on_item_selected(self, event):
        """Chamado automaticamente quando um item é selecionado na lista"""
        selection = self.tree.selection()
        if selection:
            self.view_pdf()

    def view_pdf(self, event=None):
        """Abre o PDF no visualizador integrado - AGORA AUTOMÁTICO"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        # Agora os valores são: Nome, Aplicação, Tamanho, Data
        pdf_name = item['values'][0]
        
        # Precisamos buscar o ID do banco de dados baseado no nome
        try:
            self.cursor.execute('SELECT id, file_path FROM pdfs WHERE display_name = ?', (pdf_name,))
            result = self.cursor.fetchone()
            
            if result:
                pdf_id, file_path = result
                
                # Se já está visualizando este PDF, não faz nada
                if self.current_pdf_id == pdf_id and self.current_pdf is not None:
                    return

                if os.path.exists(file_path):
                    # Limpar visualizador anterior
                    self.clear_viewer()
                    
                    # Abrir PDF com PyMuPDF
                    self.current_pdf = fitz.open(file_path)
                    self.current_pdf_id = pdf_id  # Guardar o ID do PDF atual
                    self.total_pages = len(self.current_pdf)
                    self.current_page = 0
                    
                    # Configurar visualizador
                    self.setup_viewer()
                    
                    # Mostrar primeira página
                    self.show_page()
                    
                    self.status_var.set(f"Visualizando: {pdf_name} - Página 1 de {self.total_pages}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir PDF: {str(e)}")

    def clear_viewer(self):
        """Limpa o visualizador"""
        if self.current_pdf:
            self.current_pdf.close()
            self.current_pdf = None
            self.current_pdf_id = None
        
        if self.pdf_canvas:
            self.pdf_canvas.destroy()
            self.pdf_canvas = None
        
        # Esconder controles se existirem
        if hasattr(self, 'controls_frame'):
            self.controls_frame.destroy()
            del self.controls_frame

        # Mostrar label inicial novamente
        self.viewer_label.pack(expand=True)

    def setup_viewer(self):
        """Configura o visualizador de PDF - REMOVIDO: controles de zoom"""
        # Remover label inicial
        self.viewer_label.pack_forget()
        
        # Frame para controles de navegação (SEM ZOOM)
        self.controls_frame = tk.Frame(self.viewer_frame, bg='#34495e', height=50)
        self.controls_frame.pack(fill=tk.X, side=tk.TOP)
        self.controls_frame.pack_propagate(False)
        
        # Botões de navegação com emojis
        nav_button_style = {
            'bg': '#3498db',
            'fg': 'white',
            'font': ('Arial', 10, 'bold'),
            'bd': 0,
            'padx': 8,
            'pady': 6,
            'cursor': 'hand2'
        }
        
        # Frame para navegação (centralizado)
        nav_frame = tk.Frame(self.controls_frame, bg='#34495e')
        nav_frame.pack(expand=True)  # Centralizado
        
        tk.Button(nav_frame, text="⏮️", 
                 command=self.first_page, **nav_button_style).pack(side=tk.LEFT, padx=2)
        
        tk.Button(nav_frame, text="◀️", 
                 command=self.previous_page, **nav_button_style).pack(side=tk.LEFT, padx=2)
        
        # Label da página atual
        self.page_label = tk.Label(nav_frame, 
                                  text=f"Página 1 de {self.total_pages}",
                                  bg='#34495e', fg='white', font=('Arial', 10, 'bold'))
        self.page_label.pack(side=tk.LEFT, padx=8)
        
        tk.Button(nav_frame, text="▶️", 
                 command=self.next_page, **nav_button_style).pack(side=tk.LEFT, padx=2)
        
        tk.Button(nav_frame, text="⏭️", 
                 command=self.last_page, **nav_button_style).pack(side=tk.LEFT, padx=2)
        
        # Canvas para mostrar o PDF
        self.pdf_canvas = tk.Canvas(self.viewer_frame, bg='#2c3e50', 
                                   highlightthickness=0)
        self.pdf_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind para redimensionamento
        self.pdf_canvas.bind('<Configure>', self.on_canvas_configure)

    # REMOVIDO: Funções de zoom (zoom_in, zoom_out, zoom_reset)

    def on_canvas_configure(self, event=None):
        """Redesenha o PDF quando o canvas é redimensionado"""
        if self.current_pdf:
            self.show_page()

    def show_page(self):
        """Mostra a página atual no canvas - SEM ZOOM"""
        if not self.current_pdf or self.pdf_canvas is None:
            return
        
        try:
            # Limpar canvas
            self.pdf_canvas.delete("all")
            
            # Obter página
            page = self.current_pdf[self.current_page]
            
            # Matriz fixa para qualidade (sem zoom variável)
            zoom_matrix = fitz.Matrix(1.5, 1.5)  # Qualidade fixa
            
            # Renderizar página para imagem
            pix = page.get_pixmap(matrix=zoom_matrix)
            
            # Converter para formato que o Tkinter entende
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # Obter dimensões do canvas
            canvas_width = self.pdf_canvas.winfo_width()
            canvas_height = self.pdf_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calcular proporções para centralizar a imagem
                img_width, img_height = img.size
                
                # Calcular escala para caber no canvas mantendo proporções
                scale_x = canvas_width / img_width
                scale_y = canvas_height / img_height
                scale = min(scale_x, scale_y)
                
                # Aplicar escala se necessário (para imagens muito grandes)
                if scale < 1.0:
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.pdf_img = ImageTk.PhotoImage(img)
            
            # Centralizar imagem no canvas
            x = (canvas_width - img.width) // 2
            y = (canvas_height - img.height) // 2
            
            self.pdf_canvas.create_image(x, y, anchor=tk.NW, image=self.pdf_img)
            
            # Atualizar label da página
            self.page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")
            
        except Exception as e:
            print(f"Erro ao mostrar página: {e}")

    def next_page(self):
        """Próxima página"""
        if self.current_pdf and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page()

    def previous_page(self):
        """Página anterior"""
        if self.current_pdf and self.current_page > 0:
            self.current_page -= 1
            self.show_page()

    def first_page(self):
        """Primeira página"""
        if self.current_pdf:
            self.current_page = 0
            self.show_page()

    def last_page(self):
        """Última página"""
        if self.current_pdf:
            self.current_page = self.total_pages - 1
            self.show_page()

    def edit_aplicacao(self):
        """Edita a aplicação do PDF selecionado"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um PDF para editar a aplicação")
            return
        
        item = self.tree.item(selection[0])
        pdf_name = item['values'][0]
        current_aplicacao = item['values'][1] if len(item['values']) > 1 else ""

        # Criar janela personalizada para aplicação
        aplicacao_window = tk.Toplevel(self.root)
        aplicacao_window.title("Aplicação da Peça")
        aplicacao_window.geometry("500x200")
        aplicacao_window.configure(bg='#f0f0f0')
        aplicacao_window.resizable(True, True)
        aplicacao_window.transient(self.root)
        aplicacao_window.grab_set()
        
        # Centralizar janela
        aplicacao_window.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (200 // 2)
        aplicacao_window.geometry(f"500x200+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(aplicacao_window, bg='#ffffff', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label com instruções
        label = tk.Label(main_frame, 
                        text=f"Adicione a aplicação para a peça:\n{pdf_name}",
                        font=('Arial', 12, 'bold'),
                        bg='#ffffff',
                        justify=tk.LEFT)
        label.pack(anchor='w', pady=(0, 10))
        
        # Campo de entrada
        aplicacao_var = tk.StringVar(value=current_aplicacao)
        entry = tk.Entry(main_frame, textvariable=aplicacao_var, 
                        font=('Arial', 11),
                        width=50)
        entry.pack(fill=tk.X, pady=10)
        entry.focus()
        entry.select_range(0, tk.END)
        
        # Frame para botões
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Botões
        tk.Button(button_frame, text="Cancelar", 
                 command=aplicacao_window.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(button_frame, text="Salvar", 
                 command=lambda: self.save_aplicacao(pdf_name, aplicacao_var.get(), aplicacao_window),
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter para salvar
        aplicacao_window.bind('<Return>', lambda e: self.save_aplicacao(pdf_name, aplicacao_var.get(), aplicacao_window))

    def save_aplicacao(self, pdf_name, aplicacao, window):
        """Salva a aplicação no banco de dados"""
        if not aplicacao.strip():
            aplicacao = "Não informado"
        
        try:
            # Atualizar no banco de dados
            self.cursor.execute(
                'UPDATE pdfs SET aplicacao = ? WHERE display_name = ?', 
                (aplicacao.strip(), pdf_name)
            )
            self.conn.commit()
            
            # Recarregar a lista
            if self.search_var.get().strip():
                self.on_search()
            else:
                self.load_pdfs()
                
            self.status_var.set(f"Aplicação atualizada para: {aplicacao}")
            window.destroy()
            messagebox.showinfo("Sucesso", "Aplicação atualizada com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar aplicação: {str(e)}")

    def format_date(self, date_string):
        """Formata a data para dd-mm-aaaa"""
        try:
            # Converte de YYYY-MM-DD HH:MM:SS para DD-MM-YYYY
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d-%m-%Y")
        except:
            return date_string

    def add_pdf(self):
        """Adiciona um novo PDF ao sistema - COM CAMPO APLICAÇÃO"""
        file_paths = filedialog.askopenfilenames(
            title="Selecionar PDFs",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
        )
        
        if not file_paths:
            return

        success_count = 0
        duplicate_count = 0
        skipped_files = []
        
        for file_path in file_paths:
            try:
                filename = os.path.basename(file_path)
                
                # VERIFICAR SE O ARQUIVO JÁ EXISTE (DUPLICATA)
                if self.is_duplicate_file(file_path):
                    duplicate_count += 1
                    skipped_files.append(filename)
                    print(f"Arquivo duplicado ignorado: {filename}")
                    continue
                
                # SOLICITAR APLICAÇÃO DO USUÁRIO
                aplicacao = self.get_aplicacao_from_user(filename)
                
                # Se o usuário cancelou, pular este arquivo
                if aplicacao is None:
                    continue
                
                # Criar diretório de armazenamento se não existir
                storage_dir = "esitronic_pdf_storage"
                if not os.path.exists(storage_dir):
                    os.makedirs(storage_dir)

                # Gerar nome único para o arquivo armazenado
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stored_filename = f"{timestamp}_{filename}"
                stored_path = os.path.join(storage_dir, stored_filename)

                # Copiar arquivo
                shutil.copy2(file_path, stored_path)
                
                # Obter informações do arquivo
                file_size = os.path.getsize(stored_path)
                date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Usar o nome do arquivo sem extensão como nome de exibição
                display_name = os.path.splitext(filename)[0]
                
                # Calcular hash do arquivo (se a coluna existir)
                file_hash = self.calculate_file_hash(file_path)

                # Inserir no banco de dados
                try:
                    # Tentar inserir com file_hash se a coluna existir
                    self.cursor.execute('''
                        INSERT INTO pdfs (original_filename, stored_filename, display_name, 
                                        file_path, file_size, date_added, file_hash, aplicacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (filename, stored_filename, display_name, stored_path, file_size, date_added, file_hash, aplicacao))
                except sqlite3.OperationalError:
                    # Se falhar (coluna file_hash não existe), inserir sem file_hash
                    self.cursor.execute('''
                        INSERT INTO pdfs (original_filename, stored_filename, display_name, 
                                        file_path, file_size, date_added, aplicacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (filename, stored_filename, display_name, stored_path, file_size, date_added, aplicacao))
                
                success_count += 1
                
            except sqlite3.IntegrityError:
                # Caso o hash já exista (duplicata)
                duplicate_count += 1
                skipped_files.append(filename)
                print(f"Arquivo duplicado (hash): {filename}")
            except Exception as e:
                print(f"Erro ao adicionar {filename}: {str(e)}")

        self.conn.commit()
        
        # Recarregar a lista apropriada (com busca ou completa)
        if self.search_var.get().strip():
            self.on_search()
        else:
            self.load_pdfs()
        
        # Mostrar relatório de adição
        message_parts = []
        if success_count > 0:
            message_parts.append(f"{success_count} PDF(s) adicionado(s) com sucesso!")
            self.status_var.set(f"{success_count} PDF(s) adicionado(s)")
        
        if duplicate_count > 0:
            message_parts.append(f"{duplicate_count} arquivo(s) duplicado(s) ignorado(s).")
            if skipped_files:
                message_parts.append(f"Arquivos ignorados: {', '.join(skipped_files[:5])}" + 
                                   ("..." if len(skipped_files) > 5 else ""))
        
        if message_parts:
            messagebox.showinfo("Resultado da Adição", "\n".join(message_parts))

    def get_aplicacao_from_user(self, filename):
        """Solicita a aplicação do usuário com janela personalizada"""
        # Criar janela personalizada para aplicação
        aplicacao_window = tk.Toplevel(self.root)
        aplicacao_window.title("Aplicação da Peça")
        aplicacao_window.geometry("500x200")
        aplicacao_window.configure(bg='#f0f0f0')
        aplicacao_window.resizable(True, True)
        aplicacao_window.transient(self.root)
        aplicacao_window.grab_set()
        
        # Centralizar janela
        aplicacao_window.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (200 // 2)
        aplicacao_window.geometry(f"500x200+{x}+{y}")
        
        # Variável para armazenar o resultado
        result = [None]  # Usar lista para poder modificar dentro da função
        
        # Frame principal
        main_frame = tk.Frame(aplicacao_window, bg='#ffffff', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label com instruções
        label = tk.Label(main_frame, 
                        text=f"Adicione a aplicação para a peça:\n{filename}",
                        font=('Arial', 12, 'bold'),
                        bg='#ffffff',
                        justify=tk.LEFT)
        label.pack(anchor='w', pady=(0, 10))
        
        # Campo de entrada
        aplicacao_var = tk.StringVar()
        entry = tk.Entry(main_frame, textvariable=aplicacao_var, 
                        font=('Arial', 11),
                        width=50)
        entry.pack(fill=tk.X, pady=10)
        entry.focus()
        
        # Frame para botões
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_save():
            result[0] = aplicacao_var.get().strip() if aplicacao_var.get().strip() else "Não informado"
            aplicacao_window.destroy()
        
        def on_cancel():
            result[0] = None
            aplicacao_window.destroy()
        
        # Botões
        tk.Button(button_frame, text="Cancelar", 
                 command=on_cancel,
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(button_frame, text="Salvar", 
                 command=on_save,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter para salvar
        aplicacao_window.bind('<Return>', lambda e: on_save())
        
        # Aguardar fechamento da janela
        self.root.wait_window(aplicacao_window)
        
        return result[0]

    def load_pdfs(self):
        """Carrega a lista de PDFs do banco de dados - MAIS RECENTES PRIMEIRO"""
        # Limpar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Buscar PDFs do banco - ORDENADO POR DATA DECRESCENTE (MAIS RECENTES PRIMEIRO)
        self.cursor.execute('''
            SELECT id, display_name, aplicacao, file_size, date_added 
            FROM pdfs 
            ORDER BY date_added DESC
        ''')
        
        pdfs = self.cursor.fetchall()
        
        for pdf in pdfs:
            pdf_id, display_name, aplicacao, file_size, date_added = pdf
            formatted_size = self.format_file_size(file_size)
            # Formatar data para dd-mm-aaaa
            formatted_date = self.format_date(date_added)
            # Inserir: Nome, Aplicação, Tamanho, Data
            self.tree.insert('', 'end', values=(display_name, aplicacao, formatted_size, formatted_date))

        self.status_var.set(f"Total de Documentações: {len(pdfs)}")

    def format_file_size(self, size_bytes):
        """Formata o tamanho do arquivo de forma legível"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

    def download_pdf(self):
        """Faz download do PDF selecionado para uma pasta escolhida pelo usuário"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um PDF para fazer download")
            return
        
        item = self.tree.item(selection[0])
        pdf_name = item['values'][0]  # Agora o nome está na primeira posição

        try:
            # Buscar informações do PDF
            self.cursor.execute('SELECT file_path, display_name FROM pdfs WHERE display_name = ?', (pdf_name,))
            result = self.cursor.fetchone()
            
            if result:
                file_path, display_name = result
                
                # Pedir ao usuário onde salvar o arquivo
                download_path = filedialog.asksaveasfilename(
                    title="Salvar PDF como",
                    defaultextension=".pdf",
                    filetypes=[("Arquivos PDF", "*.pdf")],
                    initialfile=f"{display_name}.pdf"
                )
                
                if download_path:
                    # Copiar arquivo para o local escolhido
                    shutil.copy2(file_path, download_path)
                    
                    messagebox.showinfo("Download Concluído", 
                                      f"PDF salvo em:\n{download_path}")
                    self.status_var.set(f"Download concluído: {display_name}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao fazer download: {str(e)}")

    def open_in_browser(self):
        """Abre o PDF no navegador padrão"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um PDF para abrir no navegador")
            return
        
        item = self.tree.item(selection[0])
        pdf_name = item['values'][0]

        try:
            # Buscar caminho do arquivo
            self.cursor.execute('SELECT file_path FROM pdfs WHERE display_name = ?', (pdf_name,))
            result = self.cursor.fetchone()
            
            if result and os.path.exists(result[0]):
                file_path = result[0]
                
                # Converter caminho para URL file://
                file_url = f"file:///{os.path.abspath(file_path).replace(os.sep, '/')}"
                
                # Abrir no navegador padrão
                webbrowser.open(file_url)
                self.status_var.set(f"Abrindo no navegador: {pdf_name}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir no navegador: {str(e)}")

    def open_pdf(self, event=None):
        """Abre o PDF no visualizador padrão do Windows (duplo-clique)"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            pdf_name = item['values'][0]
            
            self.cursor.execute('SELECT file_path FROM pdfs WHERE display_name = ?', (pdf_name,))
            result = self.cursor.fetchone()
            
            if result and os.path.exists(result[0]):
                try:
                    os.startfile(result[0])  # Abre com programa padrão no Windows
                    self.status_var.set(f"Abrindo PDF: {pdf_name}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível abrir o PDF: {str(e)}")

    def delete_pdf(self):
        """Exclui MÚLTIPLOS PDFs selecionados mesmo se estiverem abertos no visualizador"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um ou mais PDFs para excluir")
            return
        
        # Obter nomes dos PDFs selecionados
        pdf_names = []
        for item in selection:
            pdf_name = self.tree.item(item)['values'][0]
            pdf_names.append(pdf_name)

        if len(pdf_names) == 1:
            message = f"Tem certeza que deseja excluir '{pdf_names[0]}'?\n\nEsta ação não pode ser desfeita."
        else:
            message = f"Tem certeza que deseja excluir {len(pdf_names)} PDFs?\n\nEsta ação não pode ser desfeita."

        if messagebox.askyesno("Confirmar Exclusão", message):
            deleted_count = 0
            errors = []
            
            for pdf_name in pdf_names:
                try:
                    # Buscar ID e caminho do arquivo
                    self.cursor.execute('SELECT id, file_path FROM pdfs WHERE display_name = ?', (pdf_name,))
                    result = self.cursor.fetchone()
                    
                    if result:
                        pdf_id, file_path = result
                        
                        # FECHAR O PDF SE ESTIVER ABERTO NO VISUALIZADOR
                        if self.current_pdf_id == pdf_id:
                            self.clear_viewer()
                        
                        # Remover do banco de dados
                        self.cursor.execute('DELETE FROM pdfs WHERE id = ?', (pdf_id,))
                        
                        # Remover arquivo físico
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        
                        deleted_count += 1
                        
                except Exception as e:
                    errors.append(f"Erro ao excluir {pdf_name}: {str(e)}")
            
            self.conn.commit()
            
            # Recarregar a lista apropriada (com busca ou completa)
            if self.search_var.get().strip():
                self.on_search()
            else:
                self.load_pdfs()
            
            # SELECIONAR E ABRIR AUTOMATICAMENTE O PRÓXIMO ARQUIVO
            self.select_and_open_next_after_delete()
            
            # Mostrar resultado
            if errors:
                messagebox.showerror("Erros na Exclusão", "\n".join(errors))
            elif deleted_count > 0:
                if deleted_count == 1:
                    messagebox.showinfo("Sucesso", "PDF excluído com sucesso!")
                else:
                    messagebox.showinfo("Sucesso", f"{deleted_count} PDFs excluídos com sucesso!")

    def select_and_open_next_after_delete(self):
        """Seleciona e abre automaticamente o próximo arquivo após exclusão"""
        # Buscar todos os itens na treeview
        items = self.tree.get_children()
        
        if not items:
            # Se não há mais arquivos, limpar visualizador
            self.clear_viewer()
            self.status_var.set("Nenhum PDF disponível")
            return
        
        # Selecionar o primeiro item da lista (mais recente)
        first_item = items[0]
        self.tree.selection_set(first_item)
        self.tree.focus(first_item)
        self.view_pdf()

    def on_search(self, *args):
        """Filtra a lista de PDFs baseado na busca - MANTÉM RESULTADOS ATÉ CAMPO SER LIMPO"""
        search_term = self.search_var.get().lower().strip()
        
        # Se busca vazia, mostrar todos os itens
        if not search_term:
            self.load_pdfs()
            return
        
        # Limpar a treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # Buscar PDFs filtrados do banco
            self.cursor.execute('''
                SELECT id, display_name, aplicacao, file_size, date_added 
                FROM pdfs 
                WHERE display_name LIKE ? OR original_filename LIKE ? OR aplicacao LIKE ?
                ORDER BY date_added DESC
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            pdfs = self.cursor.fetchall()
            
            for pdf in pdfs:
                pdf_id, display_name, aplicacao, file_size, date_added = pdf
                formatted_size = self.format_file_size(file_size)
                # Formatar data para dd-mm-aaaa
                formatted_date = self.format_date(date_added)
                self.tree.insert('', 'end', values=(display_name, aplicacao, formatted_size, formatted_date))

            self.status_var.set(f"Encontrados {len(pdfs)} PDF(s) para '{search_term}'")
            
            # Se houver resultados, selecionar o primeiro automaticamente
            if pdfs:
                first_item = self.tree.get_children()[0]
                self.tree.selection_set(first_item)
                self.tree.focus(first_item)
                self.view_pdf()
            else:
                self.clear_viewer()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar PDFs: {str(e)}")

    def clear_search(self):
        """Limpa a barra de busca e recarrega a lista completa"""
        self.search_var.set("")
        # A busca será atualizada automaticamente pelo trace

    def __del__(self):
        """Fecha conexão com banco de dados"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    try:
        root = tk.Tk()
        app = ESITronicPDFManager(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar aplicação: {str(e)}")

if __name__ == "__main__":
    main()