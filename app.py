
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from tkcalendar import DateEntry
import datetime
import locale
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from pathlib import Path
from tkinter import Canvas,  PhotoImage 
import pandas as pd
from matplotlib import style
import squarify
import seaborn as sns

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

icon_path = 'tms.ico'

class DatabaseManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.criar_tabelas()
    
    def criar_tabelas(self):
            self.c.execute('''CREATE TABLE IF NOT EXISTS dFiliais (
                FilialID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                NomeFilial TEXT NOT NULL,
                Ativo TEXT NOT NULL,
                Cidade TEXT NOT NULL,
                UF TEXT NOT NULL,
                Tipo TEXT NOT NULL
            )''')

            self.c.execute('''CREATE TABLE IF NOT EXISTS fEntregas (
                EntregaID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                CarroID INTEGER NOT NULL,
                DataColeta DATE NOT NULL,
                DataEsperadaEntrega DATE NOT NULL,
                RotaID INTEGER NOT NULL,
                DataSolicitacaoEntrega DATE NOT NULL,  -- Corrigido o nome da coluna
                ValorCarga REAL NOT NULL,
                StatusID INTEGER NOT NULL,
                UserID INTEGER NOT NULL,
                FOREIGN KEY (StatusID) REFERENCES dStatus(StatusID),
                FOREIGN KEY (CarroID) REFERENCES dCarros(CarroID),
                FOREIGN KEY (RotaID) REFERENCES dFretes(RotaID),
                FOREIGN KEY (UserID) REFERENCES dUsers(UserID)
            )''')

            self.c.execute('''CREATE TABLE IF NOT EXISTS dFretes (
                RotaID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                NomeRota TEXT NOT NULL,
                CidadeColeta INTEGER NOT NULL,
                CidadeEntrega INTEGER NOT NULL,
                SLAemDias INTEGER NOT NULL,
                DistanciaKM INTEGER NOT NULL
            )''')

            self.c.execute('''CREATE TABLE IF NOT EXISTS dCarros (
                CarroID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                TipoCarro TEXT NOT NULL,
                ValorKM REAL NOT NULL,
                Placa TEXT NOT NULL,
                Agregado TEXT NOT NULL
            )''')

            self.c.execute('''CREATE TABLE IF NOT EXISTS dStatus (
                StatusID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                STATUS TEXT NOT NULL
            )''')

            self.c.execute('''CREATE TABLE IF NOT EXISTS dUsers (
                UserID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                Login TEXT NOT NULL,
                Senha TEXT NOT NULL
            )''')

            self.conn.commit()     

    def inserir_usuario(self, login, senha):
        with self.conn:
            self.c.execute("INSERT INTO dUsers (Login, Senha) VALUES (?, ?)", (login, senha))

    def buscar_usuario(self, login):
        self.c.execute("SELECT UserID, Login, Senha FROM dUsers WHERE Login = ?", (login,))
        usuario = self.c.fetchone()
        return usuario

    def atualizar_usuario(self, user_id, novo_login, nova_senha):
        with self.conn:
            self.c.execute("UPDATE dUsers SET Login = ?, Senha = ? WHERE UserID = ?", (novo_login, nova_senha, user_id))

    def deletar_usuario(self, user_id):
        with self.conn:
            self.c.execute("DELETE FROM dUsers WHERE UserID = ?", (user_id,))

    def login_existe(self, login):
        self.c.execute("SELECT * FROM dUsers WHERE Login = ?", (login,))
        return self.c.fetchone() is not None   
    
    def inserir_carro(self, tipo, valor_km, placa, agregado):
        try:
            with self.conn:
                self.c.execute("INSERT INTO dCarros (TipoCarro, ValorKM, Placa, Agregado) VALUES (?, ?, ?, ?)",
                            (tipo, valor_km, placa, agregado))
                self.conn.commit()
        except sqlite3.OperationalError as e:
            print("Erro ao inserir carro no banco de dados:", e)

    def buscar_carros(self):
        self.c.execute("SELECT * FROM dCarros ORDER BY CarroID DESC")
        return self.c.fetchall()

    def atualizar_carro(self, carro_id, tipo, valor_km, placa, agregado):
        with self.conn:
            self.c.execute("""UPDATE dCarros SET TipoCarro = ?, ValorKM = ?, Placa = ?, Agregado = ?
                            WHERE CarroID = ?""", (tipo, valor_km, placa, agregado, carro_id))

    def deletar_carro(self, carro_id):
        with self.conn:
            self.c.execute("DELETE FROM dCarros WHERE CarroID = ?", (carro_id,))

    def buscar_carro_id_por_placa(self, placa):
        query = "SELECT CarroID FROM dCarros WHERE Placa = ?"
        self.c.execute(query, (placa,))
        resultado = self.c.fetchone()
        return resultado[0] if resultado else None

    def inserir_filial(self,nome_filial, ativo, cidade, uf, tipo ):
        try:
            with self.conn:
                self.c.execute("INSERT INTO dFiliais (NomeFilial, Ativo, Cidade, UF , Tipo) VALUES (?, ?, ?, ?, ?)",
                            (nome_filial, ativo, cidade, uf, tipo))
                self.conn.commit()
        except sqlite3.OperationalError as e:
            print("Erro ao inserir filial no banco de dados:", e)

    def buscar_todas_filiais(self):
        self.c.execute("SELECT * FROM dFiliais ORDER BY FilialID DESC")
        return self.c.fetchall()

    def excluir_filial(self, filial_id):
        with self.conn:
            self.c.execute("DELETE FROM dFiliais WHERE FilialID = ?", (filial_id,))
            
    def buscar_filial_por_id(self, filial_id):
        self.c.execute("SELECT * FROM dFiliais WHERE FilialID = ?", (filial_id,))
        return self.c.fetchone()
    
    def atualizar_filial(self, filial_id , nome_filial, ativo, cidade, uf, tipo):
       with self.conn:
            self.c.execute("""UPDATE dFiliais SET NomeFilial = ?, Ativo = ?, Cidade = ?, UF = ? , Tipo = ?
                            WHERE FilialID = ?""", (nome_filial, ativo, cidade, uf, tipo , filial_id ))       

    def buscar_ids_filiais(self):
        self.c.execute("SELECT FilialID FROM dFiliais")
        return [fila[0] for fila in self.c.fetchall()]

    def buscar_cidades_filiais(self):
        self.c.execute("SELECT Cidade, UF FROM dFiliais GROUP BY Cidade")
        return self.c.fetchall()

    def cadastrar_frete(self, nome_rota, cidade_coleta, cidade_entrega, sla_dias, dist_km):
        with self.conn:
            self.c.execute("""INSERT INTO dFretes (NomeRota, CidadeColeta, CidadeEntrega, SLAemDias, DistanciaKM) 
                            VALUES (?, ?, ?, ?, ?)""",
                        (nome_rota, cidade_coleta, cidade_entrega, sla_dias, dist_km))

    def excluir_frete(self, rota_id):
        with self.conn:
            self.c.execute("DELETE FROM dFretes WHERE RotaID = ?", (rota_id,))

    def buscar_todos_fretes(self):
        self.c.execute("SELECT * FROM dFretes ORDER BY RotaID DESC")
        return self.c.fetchall()

    def buscar_frete_por_id(self, id_frete):
        try:
            self.c.execute("SELECT * FROM dFretes WHERE RotaID=?", (id_frete,))
            return self.c.fetchone()
        except Exception as e:
            print(f"Erro ao buscar frete por ID: {e}")
            return None

    def buscar_rota_id_por_nome(self, nome_rota):
        query = "SELECT RotaID FROM dFretes WHERE NomeRota = ?"
        self.c.execute(query, (nome_rota,))
        resultado = self.c.fetchone()
        return resultado[0] if resultado else None

    def atualizar_frete(self, id_frete, nome_rota, cidade_coleta, cidade_entrega, uf_coleta, uf_entrega, sla_dias, dist_km):
        with self.conn:
            self.c.execute("""UPDATE dFretes SET 
                            NomeRota=?, CidadeColeta=?, CidadeEntrega=?,  SLAemDias=?, DistanciaKM=?
                            WHERE RotaID=?""",
                            (nome_rota, cidade_coleta, cidade_entrega, sla_dias, dist_km, id_frete))

    def buscar_tipos_carro(self):
        try:
            self.c.execute("SELECT DISTINCT TipoCarro FROM dCarros ORDER BY TipoCarro ASC")
            tipos_carro = self.c.fetchall()
            tipos_carro = [tipo[0] for tipo in tipos_carro]
            return tipos_carro
        except Exception as e:
            print(f"Erro ao buscar tipos de carro: {e}")
            return []
    
    def buscar_placas_por_tipo(self, tipo_carro):
        self.c.execute("SELECT DISTINCT Placa FROM dCarros WHERE TipoCarro = ?", (tipo_carro,))
        return [placa[0] for placa in self.c.fetchall()]

    def buscar_nomes_rotas(self):
        self.c.execute("SELECT DISTINCT NomeRota FROM dFretes")
        return [nome[0] for nome in self.c.fetchall()]

    def inserir_solicitacao_entrega(self,carro_id, data_coleta, data_entrega, rota_id, data_solicitacao, valor_carga, status_id ,user_id):
        query = """INSERT INTO fEntregas ( CarroID, DataColeta, DataEsperadaEntrega, RotaID, DataSolicitacaoEntrega , ValorCarga ,StatusID ,UserID)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        parametros = ( carro_id, data_coleta, data_entrega, rota_id, data_solicitacao, valor_carga, status_id ,user_id )
        try:
            self.c.execute(query, parametros)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao inserir solicitação de entrega: {e}")
            return False
        
    def buscar_sla_por_rota(self, rota_id): 
        query = "SELECT SLAemDias FROM dFretes WHERE RotaID = ?"
        self.c.execute(query, (rota_id,))
        resultado = self.c.fetchone()
        return resultado[0] if resultado else 0

    def buscar_valor_km_por_carro(self, carro_id):
        query = "SELECT ValorKM FROM dCarros WHERE CarroID = ?"
        self.c.execute(query, (carro_id,))
        resultado = self.c.fetchone()
        return resultado[0] if resultado else 0

    def buscar_distancia_por_rota(self, rota_id):
        query = "SELECT DistanciaKM FROM dFretes WHERE RotaID = ?"
        self.c.execute(query, (rota_id,))
        resultado = self.c.fetchone()
        return resultado[0] if resultado else 0

    def buscar_todas_entregas(self):
            self.c.execute("SELECT * FROM fEntregas ORDER BY EntregaID ASC")
            return self.c.fetchall()

    def buscar_entregas_detalhadas(self):
        query = """
        SELECT fEntregas.EntregaID, dCarros.Placa, dFretes.NomeRota, dStatus.STATUS, dUsers.Login
        FROM fEntregas
        JOIN dCarros ON fEntregas.CarroID = dCarros.CarroID
        JOIN dFretes ON fEntregas.RotaID = dFretes.RotaID
        JOIN dStatus ON fEntregas.StatusID = dStatus.StatusID
        JOIN dUsers ON fEntregas.UserID = dUsers.UserID
        ORDER BY fEntregas.EntregaID DESC
        """
        self.c.execute(query)
        return self.c.fetchall()

    def buscar_entregas_completas(self , entrega_id=None):
        query = """
        SELECT fEntregas.EntregaID, dCarros.CarroID, dCarros.Placa, fEntregas.DataColeta, fEntregas.DataEsperadaEntrega, 
            dFretes.RotaID ,dFretes.NomeRota, fEntregas.DataSolicitacaoEntrega, fEntregas.ValorCarga, 
            fEntregas.StatusID ,dStatus.STATUS, dUsers.UserID,dUsers.Login
        FROM fEntregas
        LEFT JOIN dCarros ON fEntregas.CarroID = dCarros.CarroID
        LEFT JOIN dFretes ON fEntregas.RotaID = dFretes.RotaID
        LEFT JOIN dStatus ON fEntregas.StatusID = dStatus.StatusID
        LEFT JOIN dUsers ON fEntregas.UserID = dUsers.UserID
        """
        if entrega_id:
            query += " WHERE fEntregas.EntregaID = ?"
            self.c.execute(query, (entrega_id,))
        else:
            self.c.execute(query)
        return self.c.fetchall()

    def buscar_dados_entrega_por_id(self, entrega_id):
        query = """
        SELECT EntregaID, Placa, DataColeta, DataEsperadaEntrega, Status 
        FROM fEntregas
        WHERE EntregaID = ?
        """
        self.c.execute(query, (entrega_id,))
        return self.c.fetchone()
    
    def buscar_todos_os_status(self):
        query = "SELECT STATUS FROM dStatus"
        self.c.execute(query)
        return self.c.fetchall()

    def atualizar_status_entrega(self, entrega_id, novo_status):
        self.c.execute("SELECT StatusID FROM dStatus WHERE STATUS = ?", (novo_status,))
        status_id = self.c.fetchone()
        
        if status_id:
            with self.conn:
                self.c.execute("UPDATE fEntregas SET StatusID = ? WHERE EntregaID = ?", (status_id[0], entrega_id))
                self.conn.commit()
                return True
        return False

    def contar_carros(self):
            self.c.execute('SELECT COUNT(*) FROM dCarros')
            count = self.c.fetchone()[0]
            return count

    def contar_rotas(self):
        try:
            self.c.execute('SELECT COUNT(*) FROM dFretes')
            count = self.c.fetchone()[0]
            return count
        except sqlite3.Error as e:
            print(f"Erro ao contar rotas: {e}")
            return 0

    def contar_filiais(self):
        try:
            self.c.execute('SELECT COUNT(*) FROM dFiliais')
            count = self.c.fetchone()[0]
            return count
        except sqlite3.Error as e:
            print(f"Erro ao contar filiais: {e}")
            return 0

    def contar_entregas(self):
        """ Conta o número total de entregas na tabela fEntregas """
        try:
            self.c.execute('SELECT COUNT(*) FROM fEntregas')
            count = self.c.fetchone()[0]
            return count
        except sqlite3.Error as e:
            print(f"Erro ao contar entregas: {e}")
            return 0

    def count_carros_por_agregado(self):
        self.c.execute('SELECT Agregado, COUNT(*) FROM dCarros GROUP BY Agregado')
        return self.c.fetchall()

    def buscar_entregas_por_status(self):
        query = """
        SELECT dStatus.STATUS, COUNT(*) as Quantidade
        FROM fEntregas
        LEFT JOIN dStatus ON fEntregas.StatusID = dStatus.StatusID
        GROUP BY dStatus.STATUS
        ORDER BY Quantidade DESC 
        """
        self.c.execute(query)
        rows = self.c.fetchall()
        df = pd.DataFrame(rows, columns=['STATUS', 'Quantidade'])
        return df

    def buscar_carros_por_agregado(self):
        query = """
        SELECT Agregado, COUNT(*) as Quantidade
        FROM dCarros
        GROUP BY Agregado
        """
        self.c.execute(query)
        rows = self.c.fetchall()
        df = pd.DataFrame(rows, columns=['Agregado', 'Quantidade'])
        return df

    def buscar_rotas_por_cidade(self):
        query = """
        SELECT CidadeEntrega, COUNT(RotaID) as Quantidade
        FROM dFretes
        GROUP BY CidadeEntrega
        ORDER BY Quantidade DESC
        LIMIT 10
        """
        self.c.execute(query)
        rows = self.c.fetchall()
        return rows
    
    def buscar_sla_por_rota_dash(self):
        query = """
        SELECT SLAemDias, COUNT(*) AS Quantidade
        FROM dFretes
        GROUP BY SLAemDias
        """
        self.c.execute(query)
        rows = self.c.fetchall()
        return rows

    def buscar_carros_por_tipo(self):
        query = """
        SELECT TipoCarro, COUNT(*) AS Quantidade
        FROM dCarros
        GROUP BY TipoCarro
        ORDER BY Quantidade DESC
        """
        self.c.execute(query)
        rows = self.c.fetchall()
        return rows

    def buscar_rotas_por_distancia(self):
        query = """
        SELECT DistanciaKM, COUNT(*) AS Quantidade
        FROM dFretes
        GROUP BY DistanciaKM
        """
        self.c.execute(query)
        rows = self.c.fetchall()
        return rows

    def buscar_top_cidades_entrega(self):
        query = """
        SELECT dFretes.CidadeEntrega, COUNT(fEntregas.EntregaID) as Quantidade
        FROM fEntregas
        LEFT JOIN dFretes ON fEntregas.RotaID = dFretes.RotaID
        GROUP BY CidadeEntrega
        ORDER BY Quantidade DESC
        LIMIT 10
        """
        self.c.execute(query)
        rows = self.c.fetchall()
        return rows

    def buscar_informacoes_cards(self):

            # Consulta para Distância Total
            self.c.execute("""
                WITH CalculoDistanciaTotal AS (        
                    SELECT dCarros.ValorKM, dFretes.DistanciaKM,
                        dCarros.ValorKM * dFretes.DistanciaKM AS CustoFrete
                    FROM fEntregas
                    LEFT JOIN dCarros ON fEntregas.CarroID = dCarros.CarroID
                    LEFT JOIN dFretes ON fEntregas.RotaID = dFretes.RotaID
                )
                SELECT SUM(DistanciaKM) AS DistanciaTotal
                FROM CalculoDistanciaTotal
            """)
            distancia_total = self.c.fetchone()[0]

            # Consulta para Custo Total de Frete
            self.c.execute("""
                WITH CalculoCustoFrete AS (
                    SELECT dCarros.ValorKM * dFretes.DistanciaKM AS CustoFrete
                    FROM fEntregas
                    LEFT JOIN dCarros ON fEntregas.CarroID = dCarros.CarroID
                    LEFT JOIN dFretes ON fEntregas.RotaID = dFretes.RotaID
                )
                SELECT SUM(CustoFrete) AS TotalCustoFrete
                FROM CalculoCustoFrete
            """)
            custo_frete_total = self.c.fetchone()[0]

            # Consulta para Valor Total da Carga
            self.c.execute("""
                SELECT SUM(ValorCarga)
                FROM fEntregas
            """)
            valor_carga_total = self.c.fetchone()[0]

            return {
                'total_distance': distancia_total,
                'total_freight_cost': custo_frete_total,
                'total_value_cargo': valor_carga_total
            }

def centralizar_janela_login(janela, largura=300, altura=200):
    # Calcula a posição x e y para centralizar a janela
    pos_x = janela.winfo_screenwidth() // 2 - largura // 2
    pos_y = janela.winfo_screenheight() // 2 - altura // 2

    # Define a posição e dimensão da janela
    janela.geometry(f'{largura}x{altura}+{pos_x}+{pos_y}')

class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("TMS Login")
        self.root.geometry('350x200')
        self.root.resizable(False, False)
        self.db = DatabaseManager('tms.db')
        self.root.iconbitmap(icon_path)
        

        self.root.configure(background='#333333')
        style = ttk.Style()
        style.theme_use('clam')
        
        cor_fundo = '#333333'
        cor_frente = '#ffffff'
        cor_entrada = '#555555'
        cor_botao_entrar = '#4CAF50'
        cor_botao = '#0078D7'
        cor_botao_frente = '#ffffff'
        
        style.configure('TFrame', background=cor_fundo)
        style.configure('TLabel', background=cor_fundo, foreground=cor_frente, font=('Arial', 10))
        style.configure('TEntry', fieldbackground=cor_entrada, foreground=cor_frente, borderwidth=1)
        
        style.configure('Entrar.TButton', background=cor_botao_entrar, foreground=cor_botao_frente, font=('Arial', 10), borderwidth=1)
        style.map('Entrar.TButton', background=[('active', cor_botao_entrar)], foreground=[('active', cor_botao_frente)])
        
        style.configure('TButton', background=cor_botao, foreground=cor_botao_frente, font=('Arial', 10), borderwidth=1)
        style.map('TButton', background=[('active', cor_botao)], foreground=[('active', cor_botao_frente)])

        centralizar_janela_login(self.root, 350, 200)

        container = ttk.Frame(self.root)
        container.pack(padx=10, pady=10, fill='x', expand=True)

        self.placeholder_text = "  Exemplo: alfredo.santos"
        self.placeholder_color = 'grey'
        self.normal_color = 'black'

        ttk.Label(container, text="Login:").pack(fill='x', expand=True)
        self.login_entry = ttk.Entry(container)
        self.login_entry.pack(fill='x', expand=True, pady=5)
        self.login_entry.insert(0, self.placeholder_text)
        self.login_entry.config(foreground=self.placeholder_color)
        self.login_entry.bind("<FocusIn>", self.on_focus_in)
        self.login_entry.bind("<FocusOut>", self.on_focus_out)

        ttk.Label(container, text="Senha:").pack(fill='x', expand=True)
        self.senha_entry = ttk.Entry(container, show="*")
        self.senha_entry.pack(fill='x', expand=True, pady=5)

        button_container = ttk.Frame(container)
        button_container.pack(fill='x', expand=True, pady=10)

        ttk.Button(button_container, text="Entrar", command=self.entrar, style='Entrar.TButton').pack(side='right')
        ttk.Button(button_container, text="Registrar", command=self.registrar).pack(side='right', padx=(0, 5))

    def on_close(self):
        self.root.destroy()
                            
    def on_focus_in(self, event):
        if self.login_entry.get() == self.placeholder_text:
            self.login_entry.delete(0, tk.END)
            self.login_entry.config(foreground=self.normal_color)

    def on_focus_out(self, event):
        if not self.login_entry.get():
            self.login_entry.insert(0, self.placeholder_text)
            self.login_entry.config(foreground=self.placeholder_color)

    def limpar_campos(self):
        self.login_entry.delete(0, tk.END)
        self.senha_entry.delete(0, tk.END)

    def entrar(self):
        login = self.login_entry.get()
        senha = self.senha_entry.get()
        usuario = self.db.buscar_usuario(login)
        if usuario and usuario[2] == senha:
            self.root.destroy()
            user_id = usuario[0]
            root = tk.Tk()
            app = TelaPrincipal(root, usuario_logado=login , user_id=user_id)
            app.run()
            root.mainloop()
        else:
            messagebox.showerror("Login", "Login ou senha inválidos!")
            self.limpar_campos()

    def registrar(self):
        login = self.login_entry.get()
        senha = self.senha_entry.get()
        if not login or not senha:
            messagebox.showerror("Registrar", "Login e senha são obrigatórios!")
            self.limpar_campos()
            return
        if self.db.login_existe(login):
            messagebox.showerror("Registrar", "Login já existente. Escolha outro login.")
            self.limpar_campos()
            return
        try:
            self.db.inserir_usuario(login, senha)
            messagebox.showinfo("Registrar", "Usuário registrado com sucesso!")
        except Exception as e:
            messagebox.showerror("Registrar", f"Erro ao registrar usuário: {e}")
        self.limpar_campos()

class CadastroCarro(tk.Toplevel):
    def __init__(self, master=None , atualizar_callback=None):
        super().__init__(master=master)
        self.title("Cadastro de Carro")
        self.geometry("770x670")
        self.resizable(False, False)
        self.db = DatabaseManager('tms.db')        
        centralizar_janela_login(self,1024, 468)  
        self.configure(background='#333333')
        self.create_widgets()
        self.atualizar()
        self.atualizar_callback = atualizar_callback
        self.iconbitmap(icon_path)
        
    def create_widgets(self):
        # Frame para entradas
        self.entry_frame = ttk.Frame(self, padding="10")
        self.entry_frame.pack(fill='x')

        # Combobox para "Tipo de Carro"
        ttk.Label(self.entry_frame, text="Tipo de Carro:").grid(row=0, column=0, sticky='w')
        self.tipo_carro_combobox = ttk.Combobox(self.entry_frame, 
                                                values=["Fiorino", "Van", "Vuc", "Toco", "3/4", "Truck", "Carreta"],
                                                state="readonly")
        self.tipo_carro_combobox.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.tipo_carro_combobox.set("Selecione uma opção")  
                      
        # Labels e Entries
        labels_text = []
        self.entries = {}
        for idx, text in enumerate(labels_text, start=1):  #
            label = ttk.Label(self.entry_frame, text=text)
            label.grid(row=idx, column=0, sticky='w')
            entry = ttk.Entry(self.entry_frame)
            entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=5)
            self.entries[text] = entry
        self.entry_frame.grid_columnconfigure(1, weight=1)  
        
        # Campo Placa
        placa_label = ttk.Label(self.entry_frame, text="Placa:")
        placa_label.grid(row=2, column=0, sticky='w')
        placa_entry = ttk.Entry(self.entry_frame)
        placa_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        placa_entry.bind('<KeyRelease>', self.on_placa_change)
        self.entries["Placa"] = placa_entry

        # CheckBox Agregado
        self.agregado_var = tk.BooleanVar()
        agregado_checkbox = ttk.Checkbutton(self.entry_frame, text="Agregado", variable=self.agregado_var)
        agregado_checkbox.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        # Frame para botões
        self.button_frame = ttk.Frame(self, padding="10")
        self.button_frame.pack(fill='x')

        # Botões
        self.btn_cadastrar = ttk.Button(self.button_frame, text="Cadastrar", command=self.cadastrar)
        self.btn_editar = ttk.Button(self.button_frame, text="Editar", command=self.editar)
        self.btn_excluir = ttk.Button(self.button_frame, text="Excluir", command=self.excluir)
        self.btn_atualizar = ttk.Button(self.button_frame, text="Atualizar", command=self.atualizar)
        self.btn_cadastrar.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.btn_editar.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.btn_excluir.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        self.btn_atualizar.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
        self.button_frame.grid_columnconfigure(3, weight=1)

        # Frame para o Treeview e Scrollbar
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Treeview para listar os carros
        self.tree = ttk.Treeview(self.tree_frame, columns=("ID","Tipo", "ValorKM", "Placa", "Agregado"), show="headings")
        self.tree.grid(row=0, column=0, sticky='nsew')

        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)  # Você pode ajustar a largura conforme necessário

        # Scrollbar para o Treeview
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Configure o grid do tree_frame para expandir corretamente o Treeview e a Scrollbar
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Campo Valor por KM
        self.setup_valor_km_entry()
       
    def limpar_campos(self):
        # Resetar os campos padrão
        for key, entry in self.entries.items():
            if key != "Valor por KM":  # Trata o campo de Valor por KM separadamente
                entry.delete(0, tk.END)
        
        # Resetar o campo de Valor por KM para "R$ 00,00"
        self.valor_km_var.set("R$ 00,00")

        # Resetar o ComboBox para o placeholder
        self.tipo_carro_combobox.set("Selecione uma opção")
        
        # Desmarcar o checkbox "Agregado"
        self.agregado_var.set(False)

    def setup_agregado_checkbox(self):
        # Configuração do CheckBox para "Agregado"
        self.agregado_var = tk.BooleanVar()
        self.agregado_checkbox = ttk.Checkbutton(self.entry_frame, text="Agregado", variable=self.agregado_var, onvalue=True, offvalue=False)
        
        # Centraliza o checkbox na célula grid ajustando o columnspan e sticky
        self.agregado_checkbox.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
   
    def setup_valor_km_entry(self):
        valor_km_label = ttk.Label(self.entry_frame, text="Valor por KM:")
        valor_km_label.grid(row=1, column=0, sticky='w')

        # Define o valor inicial como "R$ 00,00"
        self.valor_km_var = tk.StringVar(value="R$ 00,00")
        self.valor_km_entry = ttk.Entry(self.entry_frame, textvariable=self.valor_km_var, justify='left')
        self.valor_km_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.valor_km_entry.bind('<KeyRelease>', self.on_value_change)
        self.valor_km_entry.bind('<FocusIn>', self.on_focus_in_valor_km)

    def on_focus_in_valor_km(self, event=None):
        # Move o cursor para o final do texto ao focar no campo
        self.valor_km_entry.select_range(0, tk.END)
        self.valor_km_entry.icursor(tk.END)
           
    def on_value_change(self, event=None):
        current_value = self.valor_km_var.get().replace('R$', '').replace('.', '').replace(',', '')
        if not current_value:
            current_value = '0'
        try:
            formatted_value = 'R$ {:,.2f}'.format(int(current_value) / 100).replace(',', 'X').replace('.', ',').replace('X', '.')
            self.valor_km_var.set(formatted_value)
            self.valor_km_entry.icursor(tk.END)  # Move o cursor para o final após a formatação
        except ValueError:
            print("Erro ao converter o valor.")

    def on_placa_change(self, event=None):
        # Obtém o texto atual do Entry de Placa, converte para maiúsculas e atualiza o Entry
        placa_atual = self.entries["Placa"].get().upper()
        self.entries["Placa"].delete(0, tk.END)
        self.entries["Placa"].insert(0, placa_atual)

    def cadastrar(self):
        tipo = self.tipo_carro_combobox.get()
        valor_km_raw = self.valor_km_var.get().replace("R$ ", "").replace(".", "").replace(",", ".")
        
        try:
            valor_km = float(valor_km_raw)
        except ValueError:
            messagebox.showerror("Erro", "Formato inválido para o valor por KM.")
            self.limpar_campos()
            return
        
        placa = self.entries["Placa"].get()
        agregado = 'Sim' if self.agregado_var.get() else 'Não'


        if tipo == "Selecione uma opção" or not tipo:
            messagebox.showwarning("Atenção", "Por favor, selecione um tipo de carro válido.")
            return
        
        if not valor_km or not placa:
            messagebox.showwarning("Atenção", "Todos os campos são obrigatórios, exceto 'Agregado'.")
            return

        try:
            self.db.inserir_carro(tipo, valor_km, placa, agregado)
            self.atualizar()
            messagebox.showinfo("Sucesso", "Carro cadastrado com sucesso!")
            self.limpar_campos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar carro: {e}")
                               
    def atualizar(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for carro in self.db.buscar_carros():
            self.tree.insert('', 'end', values=carro)

    def obter_carro_selecionado(self):
        """Obtém o carro selecionado na Treeview."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection)
            return item['values']  # Retorna uma lista dos valores das colunas
        else:
            messagebox.showwarning('Aviso', 'Nenhum carro selecionado')
            return None

    def preencher_entradas_com_selecao(self, valores):
        if valores:
            self.entries["Tipo de Carro"].delete(0, tk.END)
            self.entries["Tipo de Carro"].insert(0, valores[1])

            self.entries["Valor por KM"].delete(0, tk.END)
            self.entries["Valor por KM"].insert(0, valores[2])

            self.entries["Placa"].delete(0, tk.END)
            self.entries["Placa"].insert(0, valores[3])

            self.entries["Agregado"].delete(0, tk.END)
            self.entries["Agregado"].insert(0, valores[4])

    def editar(self):
        valores = self.obter_carro_selecionado()
        if valores:
            carro_id, tipo, valor_km, placa, agregado = valores
            janela_edicao = JanelaEdicaoCarro(self, self.db, carro_id, tipo, valor_km, placa, agregado, self.atualizar_callback)
            janela_edicao.grab_set()

    def excluir(self):
        valores = self.obter_carro_selecionado()
        if valores:
            carro_id = valores[0]
            if messagebox.askyesno("Confirmar exclusão", "Tem certeza que deseja excluir este carro?"):
                try:
                    self.db.deletar_carro(carro_id)
                    self.atualizar()
                    messagebox.showinfo("Sucesso", "Carro excluído com sucesso!")
                    self.limpar_campos()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao excluir carro: {e}")

class JanelaEdicaoCarro(tk.Toplevel):
    def __init__(self, master, db, carro_id, tipo, valor_km, placa, agregado , atualizar_callback):
        super().__init__(master)
        self.db = db
        self.carro_id = carro_id
        self.resizable(False, False)
        self.atualizar_callback = atualizar_callback

        self.geometry("400x300")  
        centralizar_janela_login(self, 300, 255)  
        self.title("Editar Carro")
        self.entries = {} 
        
        # Aplica o estilo da janela principal
        self.configure(background='#333333')
        style = ttk.Style(self)
        style.theme_use('clam')  
        
        # Estilos específicos, se houver, por exemplo:
        style.configure('TButton', background='#0078D7', foreground='#ffffff')
        style.map('TButton', background=[('active', '#0066CC')], foreground=[('active', '#ffffff')])

        # Cria os widgets
        self.create_widgets(tipo, valor_km, placa, agregado)
        self.iconbitmap(icon_path)


    def create_widgets(self, tipo, valor_km, placa, agregado):
        
        self.entry_frame = ttk.Frame(self, padding="10")
        self.entry_frame.pack(padx=10, pady=10, fill='x', expand=True)

        # Label e Combobox para "Tipo de Carro"
        self.tipo_carro_combobox_var = tk.StringVar(value=tipo)
        ttk.Label(self.entry_frame, text="Tipo de Carro:").grid(row=0, column=0, sticky='w')
        self.tipo_carro_combobox = ttk.Combobox(self.entry_frame, 
                                                values=["Fiorino", "Van", "Vuc", "Toco", "3/4", "Truck", "Carreta"],
                                                state="readonly")
        self.tipo_carro_combobox.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.tipo_carro_combobox.set(tipo)  
        self.entries["Tipo de Carro"] = self.tipo_carro_combobox_var

        # Label e Entry para "Valor por KM"
        ttk.Label(self.entry_frame, text="Valor por KM:").grid(row=1, column=0, sticky='w')
        self.valor_km_var = tk.StringVar(value=valor_km)
        self.valor_km_entry = ttk.Entry(self.entry_frame, textvariable=self.valor_km_var, justify='right')
        self.valor_km_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.valor_km_entry.bind('<KeyRelease>', self.on_value_change)

        # Label e Entry para "Placa"
        ttk.Label(self.entry_frame, text="Placa:").grid(row=2, column=0, sticky='w')
        self.placa_var = tk.StringVar(value=placa)
        self.placa_entry = ttk.Entry(self.entry_frame, textvariable=self.placa_var)
        self.placa_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        self.placa_entry.bind('<KeyRelease>', self.on_placa_change)

        # Checkbox para "Agregado"
        ttk.Label(self.entry_frame, text="Agregado:").grid(row=3, column=0, sticky='w')
        self.agregado_var = tk.BooleanVar(value=agregado == 'Sim')
        self.agregado_checkbox = ttk.Checkbutton(self.entry_frame, text="", variable=self.agregado_var)
        self.agregado_checkbox.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # Ajusta colunas do entry_frame para ter o mesmo espaço
        self.entry_frame.grid_columnconfigure(0, weight=1)
        self.entry_frame.grid_columnconfigure(1, weight=3)

        # Frame para o botão de salvar as edições
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=10)

        # Botão Salvar Edições
        save_button = ttk.Button(button_frame, text="Salvar Edições", command=self.salvar_edicao)
        save_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Expande o frame de entrada para preencher o espaço horizontal
        self.entry_frame.grid_columnconfigure(1, weight=1) 

    def on_value_change(self, event=None):
        current_value = self.valor_km_var.get().replace('R$', '').replace('.', '').replace(',', '')
        if not current_value:
            current_value = '0'
        try:
            formatted_value = 'R$ {:,.2f}'.format(int(current_value) / 100).replace(',', 'X').replace('.', ',').replace('X', '.')
            self.valor_km_var.set(formatted_value)
            self.valor_km_entry.icursor(tk.END)  # Move o cursor para o final após a formatação
        except ValueError:
            print("Erro ao converter o valor.")    

    def on_placa_change(self, event=None):
        # Obtém o texto atual do Entry de Placa, converte para maiúsculas e atualiza o Entry
        texto_atual = self.placa_var.get().upper()
        self.placa_entry.delete(0, tk.END)
        self.placa_entry.insert(0, texto_atual)

    def validar_valor_km(self, valor_km_str):
        try:
            # Tenta converter a string para float após remover os símbolos
            valor_float = float(valor_km_str.replace('R$', '').replace('.', '').replace(',', '.'))
            return True, valor_float  # Retorna True e o valor convertido se for bem-sucedido
        except ValueError:
            messagebox.showerror("Erro", "Insira um valor monetário válido para o KM.")
            return False, None  # Retorna False e None se falhar

    def salvar_edicao(self):
        tipo = self.tipo_carro_combobox.get() 
        valor_km_str = self.valor_km_var.get()

        # Valida o valor do KM antes de tentar salvar
        is_valid, valor_km = self.validar_valor_km(valor_km_str)
        if not is_valid:
            self.valor_km_entry.focus_set()  # Coloca o foco no campo Valor por KM se houver erro
            return  # Não continua se o valor não for válido

        # Verifica se o valor de KM é maior que zero
        if valor_km <= 0:
            messagebox.showerror("Erro", "O valor por KM deve ser maior que zero.")
            self.valor_km_entry.focus_set()
            return

        placa = self.placa_var.get().strip()  # Remove espaços em branco
        if not placa:  # Verifica se a placa não está vazia
            messagebox.showerror("Erro", "O campo Placa não pode estar vazio.")
            self.placa_entry.focus_set()
            return

        agregado = 'Sim' if self.agregado_var.get() else 'Não'

        try:
            self.db.atualizar_carro(self.carro_id, tipo, valor_km, placa, agregado)
            messagebox.showinfo("Sucesso", "Carro atualizado com sucesso!")
            self.atualizar_callback()
            self.destroy()  # Fecha a janela de edição  
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar carro: {e}")

class CadastroFilial(tk.Toplevel):
    def __init__(self, master=None, atualizar_callback=None):
        super().__init__(master=master)
        self.title("Cadastro de Filial")
        self.geometry("770x670")
        centralizar_janela_login(self,1024, 468)
        self.resizable(False, False)
        self.db = DatabaseManager('tms.db')
        self.configure(background='#333333')
        self.create_widgets()
        self.atualizar()
        self.atualizar_callback = atualizar_callback
        self.iconbitmap(icon_path)
        
    def limpar_campos(self):
        self.nome_filial_var.set('')
        self.ativo_var.set(False)  # Desmarca o checkbox
        self.cidades_combobox.set('')  # Limpa o combobox de cidades
        self.uf_combobox.set('')  # Limpa o combobox de UF
        self.tipo_combobox.set('')  # Limpa o combobox de tipo

    def create_widgets(self):
        self.entry_frame = ttk.Frame(self, padding="10")
        self.entry_frame.pack(fill='x')

        # Nome da Filial
        nome_filial_label = ttk.Label(self.entry_frame, text="Nome Filial:")
        nome_filial_label.grid(row=0, column=0, sticky='w')
        self.nome_filial_var = tk.StringVar()
        nome_filial_entry = ttk.Entry(self.entry_frame, textvariable=self.nome_filial_var)
        nome_filial_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        nome_filial_entry.bind('<KeyRelease>', self.on_nome_filial_change)

        self.dados_uf_cidades = {
            'AM': ['Coari', 'Itacoatiara', 'Manacapuru', 'Manaus', 'Parintins'],
            'BA': ['Camaçari', 'Feira de Santana', 'Itabuna', 'Salvador', 'Vitória da Conquista'],
            'CE': ['Caucaia', 'Fortaleza', 'Juazeiro do Norte', 'Maracanaú', 'Sobral'],
            'GO': ['Anápolis', 'Aparecida de Goiânia', 'Goiânia', 'Luziânia', 'Rio Verde'],
            'MG': ['Belo Horizonte', 'Juiz de Fora', 'Ouro Preto', 'Poços de Caldas', 'Uberlândia'],
            'MT': ['Cuiabá', 'Rondonópolis', 'Sinop', 'Tangará da Serra', 'Várzea Grande'],
            'PA': ['Belém', 'Castanhal', 'Marabá', 'Parauapebas', 'Santarém'],
            'PE': ['Caruaru', 'Garanhuns', 'Olinda', 'Petrolina', 'Recife'],
            'PR': ['Curitiba', 'Foz do Iguaçu', 'Londrina', 'Maringá', 'Ponta Grossa'],
            'RJ': ['Campos dos Goytacazes', 'Niterói', 'Petropolis', 'Rio de Janeiro', 'Volta Redonda'],
            'RS': ['Caxias do Sul', 'Gramado', 'Pelotas', 'Porto Alegre', 'Santa Maria'],
            'SC': ['Blumenau', 'Chapecó', 'Criciúma', 'Florianópolis', 'Joinville'],
            'SP': ['Campinas', 'Ribeirão Preto', 'Santos', 'Sorocaba', 'São Paulo']
        }

        # Combobox para UF
        uf_label = ttk.Label(self.entry_frame, text="UF:")
        uf_label.grid(row=1, column=0, sticky='w')
        self.uf_combobox = ttk.Combobox(self.entry_frame, values=list(self.dados_uf_cidades.keys()), state="readonly")
        self.uf_combobox.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.uf_combobox.bind('<<ComboboxSelected>>', self.on_uf_selecionado)

        # Combobox para Cidades
        cidade_label = ttk.Label(self.entry_frame, text="Cidade:")
        cidade_label.grid(row=2, column=0, sticky='w')
        self.cidades_combobox = ttk.Combobox(self.entry_frame, state="readonly")
        self.cidades_combobox.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

        # Tipo
        tipo_label = ttk.Label(self.entry_frame, text="Tipo:")
        tipo_label.grid(row=3, column=0, sticky='w')
        self.tipo_combobox = ttk.Combobox(self.entry_frame, 
                                          values=["CD", "Loja"], 
                                          state="readonly")
        self.tipo_combobox.grid(row=3, column=1, sticky='ew', padx=5, pady=5)

        # Ativo
        self.ativo_var = tk.BooleanVar()
        ativo_checkbutton = ttk.Checkbutton(self.entry_frame, text="Ativo", variable=self.ativo_var)
        ativo_checkbutton.grid(row=4, column=1, sticky='ew', padx=5, pady=5)

        # Configurar o grid para que os widgets de entrada expandam corretamente
        self.entry_frame.grid_columnconfigure(1, weight=1)

        # Frame para botões
        self.button_frame = ttk.Frame(self, padding="10")
        self.button_frame.pack(fill='x')

        # Botões
        self.btn_cadastrar = ttk.Button(self.button_frame, text="Cadastrar", command=self.cadastrar)
        self.btn_editar = ttk.Button(self.button_frame, text="Editar", command=self.editar)
        self.btn_excluir = ttk.Button(self.button_frame, text="Excluir", command=self.excluir)
        self.btn_atualizar = ttk.Button(self.button_frame, text="Atualizar", command=self.atualizar)
        self.btn_cadastrar.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.btn_editar.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.btn_excluir.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        self.btn_atualizar.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
        self.button_frame.grid_columnconfigure(3, weight=1)

        # Frame para o Treeview e Scrollbar
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Treeview para listar as filiais
        self.tree = ttk.Treeview(self.tree_frame, columns=("ID", "NomeFilial", "Ativo", "Cidade", "UF", "Tipo"), show="headings")
        self.tree.grid(row=0, column=0, sticky='nsew')

        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')

        # Scrollbar para o Treeview
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Configurar o grid do tree_frame para expandir corretamente o Treeview e a Scrollbar
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

    def on_uf_selecionado(self, event):
        uf_selecionado = self.uf_combobox.get()
        self.cidades_combobox['values'] = self.dados_uf_cidades.get(uf_selecionado, [])
        self.cidades_combobox.set('')  # Limpa a cidade selecionada quando a UF muda

    def on_nome_filial_change(self, event):
        # Converte o texto do nome da filial para maiúsculas
        self.nome_filial_var.set(self.nome_filial_var.get().upper())

    def cadastrar(self):
        nome_filial = self.nome_filial_var.get().strip()
        ativo = 'Sim' if self.ativo_var.get() else 'Não'
        cidade = self.cidades_combobox.get().strip()
        uf = self.uf_combobox.get().strip()
        tipo = self.tipo_combobox.get().strip()

        # Verifique se todos os campos necessários estão preenchidos
        if not (nome_filial and cidade and uf and tipo):
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
            return

        try:
            self.db.inserir_filial(nome_filial, ativo, cidade, uf, tipo)
            self.limpar_campos()  # Limpar os campos antes de atualizar pode evitar que o usuário veja dados antigos nos campos após o cadastro
            self.atualizar()  # Atualiza o treeview imediatamente
            messagebox.showinfo("Sucesso", "Filial cadastrada com sucesso!")
            if self.atualizar_callback:
                self.atualizar_callback()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar filial: {e}")

    def atualizar(self):
        # Atualizar a Treeview com os dados do banco de dados
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            filiais = self.db.buscar_todas_filiais()
            for filial in filiais:
                self.tree.insert('', 'end', values=filial)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar filiais: {e}")

    def editar(self):
        # Verifica se há algum item selecionado na Treeview
        selected_item = self.tree.selection()
        if selected_item:
            # Pega o ID da filial que está na primeira coluna da Treeview
            filial_id = self.tree.item(selected_item, 'values')[0]
            # Abre a janela de edição passando o ID da filial selecionada
            janela_edicao = JanelaEdicaoFilial(self, self.db, filial_id, self.atualizar)
            janela_edicao.grab_set()  # Isso faz com que a atenção do usuário esteja voltada para a janela de edição
        else:
            messagebox.showwarning("Atenção", "Por favor, selecione uma filial para editar.")

    def excluir(self):
        # Obter o item selecionado da Treeview
        selected_item = self.tree.selection()[0]
        filial_id = self.tree.item(selected_item)['values'][0]

        # Confirmar ação do usuário
        if messagebox.askyesno("Confirmar", "Deseja excluir esta filial?"):
            try:
                self.db.excluir_filial(filial_id)
                messagebox.showinfo("Sucesso", "Filial excluída com sucesso!")
                self.limpar_campos()
                self.atualizar()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir filial: {e}")

class JanelaEdicaoFilial(tk.Toplevel):
    def __init__(self, master, db, filial_id, atualizar_callback):
        super().__init__(master=master)
        self.db = db
        self.filial_id = filial_id
        self.atualizar_callback = atualizar_callback
        self.configure(background='#333333')
        style = ttk.Style(self)
        style.theme_use('clam')
        self.title("Editar Filial")
        self.geometry("400x300")
        centralizar_janela_login(self, 300, 255) 
        self.resizable(False, False)
 
        self.dados_uf_cidades = {
                'AM': ['Coari', 'Itacoatiara', 'Manacapuru', 'Manaus', 'Parintins'],
                'BA': ['Camaçari', 'Feira de Santana', 'Itabuna', 'Salvador', 'Vitória da Conquista'],
                'CE': ['Caucaia', 'Fortaleza', 'Juazeiro do Norte', 'Maracanaú', 'Sobral'],
                'GO': ['Anápolis', 'Aparecida de Goiânia', 'Goiânia', 'Luziânia', 'Rio Verde'],
                'MG': ['Belo Horizonte', 'Juiz de Fora', 'Ouro Preto', 'Poços de Caldas', 'Uberlândia'],
                'MT': ['Cuiabá', 'Rondonópolis', 'Sinop', 'Tangará da Serra', 'Várzea Grande'],
                'PA': ['Belém', 'Castanhal', 'Marabá', 'Parauapebas', 'Santarém'],
                'PE': ['Caruaru', 'Garanhuns', 'Olinda', 'Petrolina', 'Recife'],
                'PR': ['Curitiba', 'Foz do Iguaçu', 'Londrina', 'Maringá', 'Ponta Grossa'],
                'RJ': ['Campos dos Goytacazes', 'Niterói', 'Petropolis', 'Rio de Janeiro', 'Volta Redonda'],
                'RS': ['Caxias do Sul', 'Gramado', 'Pelotas', 'Porto Alegre', 'Santa Maria'],
                'SC': ['Blumenau', 'Chapecó', 'Criciúma', 'Florianópolis', 'Joinville'],
                'SP': ['Campinas', 'Ribeirão Preto', 'Santos', 'Sorocaba', 'São Paulo']
            }
 
        self.create_widgets()
        self.load_filial_data()
        self.iconbitmap(icon_path)

        
    def create_widgets(self):
        self.entry_frame = ttk.Frame(self, padding="10")
        self.entry_frame.pack(fill='x', padx=10, pady=10)

        self.nome_filial_var = tk.StringVar()
        ttk.Label(self.entry_frame, text="Nome Filial:").grid(row=0, column=0, sticky='w')
        self.nome_filial_entry = ttk.Entry(self.entry_frame, textvariable=self.nome_filial_var)
        self.nome_filial_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.nome_filial_entry.bind('<KeyRelease>', self.on_nome_filial_change)  # Bind ao evento de soltar tecla
 
        # UF
        self.uf_var = tk.StringVar()
        ttk.Label(self.entry_frame, text="UF:").grid(row=1, column=0, sticky='w')
        self.uf_combobox = ttk.Combobox(self.entry_frame, textvariable=self.uf_var,values=list(self.dados_uf_cidades.keys()) , state="readonly")
        self.uf_combobox.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.uf_combobox.bind('<<ComboboxSelected>>', self.on_uf_selecionado)
 
        # Cidade
        self.cidade_var = tk.StringVar()
        ttk.Label(self.entry_frame, text="Cidade:").grid(row=2, column=0, sticky='w')
        self.cidade_combobox = ttk.Combobox(self.entry_frame, textvariable=self.cidade_var ,state="readonly")
        self.cidade_combobox.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
 
        # Tipo
        self.tipo_var = tk.StringVar()
        ttk.Label(self.entry_frame, text="Tipo:").grid(row=3, column=0, sticky='w')
        self.tipo_combobox = ttk.Combobox(self.entry_frame, textvariable=self.tipo_var, values=list(["CD" , "Loja"]), state="readonly")
        self.tipo_combobox.grid(row=3, column=1, sticky='ew', padx=5, pady=5)

        # Ativo
        self.ativo_var = tk.BooleanVar()
        ttk.Label(self.entry_frame, text="Ativo:").grid(row=4, column=0, sticky='w')
        self.ativo_checkbutton = ttk.Checkbutton(self.entry_frame, variable=self.ativo_var)
        self.ativo_checkbutton.grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # Botão Salvar Edições
        save_button = ttk.Button(self, text="Salvar Edições", command=self.salvar_edicao)
        save_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Chamar a função para carregar os dados da filial atual
        self.load_filial_data()

    def load_filial_data(self):
        filial_data = self.db.buscar_filial_por_id(self.filial_id)
        if filial_data:
            # Atualiza os campos com os dados da filial
            self.nome_filial_var.set(filial_data[1])
            self.ativo_var.set(filial_data[2] == 'Sim')
            self.uf_combobox.set(filial_data[4])
            self.on_uf_selecionado()
            self.update_cidade_combobox(filial_data[4])  # Atualiza as cidades baseadas na UF
            self.cidade_combobox.set(filial_data[3])
            self.tipo_combobox.set(filial_data[5])
        else:
            messagebox.showerror("Erro", "Dados da filial não encontrados.")
            self.destroy()

    def update_cidade_combobox(self, uf):
        # Atualiza as opções do combobox de cidades com base na UF
        self.cidade_combobox['values'] = self.dados_uf_cidades.get(uf, [])
        if self.cidade_var.get() not in self.dados_uf_cidades[uf]:
            self.cidade_var.set('')

    def on_uf_selecionado(self, event=None):
        # Atualize o combobox de cidades com base na UF selecionada
        uf_selecionada = self.uf_combobox.get()
        cidades = self.dados_uf_cidades.get(uf_selecionada, [])
        self.cidade_combobox['values'] = cidades
        
        if self.cidade_combobox.get() not in cidades:
            self.cidade_combobox.set('') 

    def on_nome_filial_change(self, event=None):
        # Converte o texto do nome da filial para maiúsculas enquanto o usuário digita
        current_text = self.nome_filial_var.get().upper()
        self.nome_filial_var.set(current_text)  # Atualiza a variável com o texto em maiúsculas

    def salvar_edicao(self):
        # Aqui você coleta os valores dos widgets, valida e atualiza a filial no banco de dados.
        nome_filial = self.nome_filial_var.get().strip()
        ativo = 'Sim' if self.ativo_var.get() else 'Não'
        cidade = self.cidade_combobox.get().strip()
        uf = self.uf_combobox.get().strip()
        tipo = self.tipo_combobox.get().strip()

        # Validação dos campos
        if not (nome_filial and cidade and uf and tipo):
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
            return

        # Atualização no banco de dados
        try:
            self.db.atualizar_filial(self.filial_id, nome_filial, ativo, cidade, uf, tipo)
            messagebox.showinfo("Sucesso", "Filial atualizada com sucesso!")
            self.atualizar_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar filial: {e}")
            
    def atualizar(self):
        # Método para atualizar a Treeview na tela principal, caso seja necessário.
        if self.atualizar_callback:
            self.atualizar_callback()

class CadastroFrete (tk.Toplevel):
    def __init__(self, master=None, atualizar_callback=None):
        super().__init__(master=master)
        self.grab_set()       
        self.title("Cadastro de Fretes")
        self.geometry("770x670")
        centralizar_janela_login(self,1024, 468) 
        self.resizable(False, False)
        self.atualizar_callback = atualizar_callback
        self.db = DatabaseManager('tms.db')
        self.configure(background='#333333')
        self.create_widgets()
        self.atualizar()
        self.iconbitmap(icon_path)
        
    def create_widgets(self):
        # Estrutura do formulário
        self.entry_frame = ttk.Frame(self, padding="10")
        self.entry_frame.pack(fill='x', padx=10, pady=10)
        
        style = ttk.Style()
        style.configure("Disabled.TEntry", foreground="#b3b3b3", background="#e6e6e6")
        
        # Campo Nome da Rota
        ttk.Label(self.entry_frame, text="Nome Rota:").grid(row=0, column=0, sticky='w')
        self.nome_rota_var = tk.StringVar()
        self.nome_rota_var.trace_add("write", lambda *args: self.on_nome_rota_change())
        nome_rota_entry = ttk.Entry(self.entry_frame, textvariable=self.nome_rota_var)
        nome_rota_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5 , columnspan=3)

        # Combobox Cidade Coleta
        ttk.Label(self.entry_frame, text="Cidade de Coleta:").grid(row=1, column=0, sticky='w')
        self.cidade_coleta_var = tk.StringVar()
        self.cidade_coleta_cb = ttk.Combobox(self.entry_frame, textvariable=self.cidade_coleta_var, state="readonly")
        self.cidade_coleta_cb['values'] = self.get_nomes_cidades_filiais()
        self.cidade_coleta_cb.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.cidade_coleta_cb.bind('<<ComboboxSelected>>', self.on_cidade_coleta_selecionada)

        # Label e Entry para UF de Coleta
        self.uf_coleta_var = tk.StringVar()
        ttk.Label(self.entry_frame, text="UF de Coleta:").grid(row=1, column=2, sticky='w')
        self.uf_coleta_entry = ttk.Entry(self.entry_frame, textvariable=self.uf_coleta_var, state="readonly" , style="Disabled.TEntry")
        self.uf_coleta_entry.grid(row=1, column=3, sticky='ew', padx=5, pady=5)

        # Combobox Cidade Entrega
        ttk.Label(self.entry_frame, text="Cidade de Entrega:").grid(row=2, column=0, sticky='w')
        self.cidade_entrega_var = tk.StringVar()
        self.cidade_entrega_cb = ttk.Combobox(self.entry_frame, textvariable=self.cidade_entrega_var, state="readonly")
        self.cidade_entrega_cb['values'] = self.get_nomes_cidades_filiais()
        self.cidade_entrega_cb.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        self.cidade_entrega_cb.bind('<<ComboboxSelected>>', self.on_cidade_entrega_selecionada)

        # Adicione um campo somente leitura para UF de Entrega
        self.uf_entrega_var = tk.StringVar()
        ttk.Label(self.entry_frame, text="UF de Entrega:").grid(row=2, column=2, sticky='w')
        self.uf_entrega_entry = ttk.Entry(self.entry_frame, textvariable=self.uf_entrega_var, state="readonly" ,  style="Disabled.TEntry")
        self.uf_entrega_entry.grid(row=2, column=3, sticky='ew', padx=5, pady=5)

        # Campo SLA em Dias
        ttk.Label(self.entry_frame, text="SLA em Dias:").grid(row=3, column=0, sticky='w')
        self.sla_dias_var = tk.StringVar()
        sla_dias_entry = ttk.Entry(self.entry_frame, textvariable=self.sla_dias_var, validate="key", validatecommand=(self.register(self.validate_integer), '%P'))
        sla_dias_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5 , columnspan=3)

        # Campo Distância em KM
        ttk.Label(self.entry_frame, text="Distância em KM:").grid(row=4, column=0, sticky='w')
        self.dist_km_var = tk.StringVar()
        dist_km_entry = ttk.Entry(self.entry_frame, textvariable=self.dist_km_var, validate="key", validatecommand=(self.register(self.validate_integer), '%P'))
        dist_km_entry.grid(row=4, column=1, sticky='ew', padx=5, pady=5 , columnspan=3)

        # Frame para botões
        self.button_frame = ttk.Frame(self, padding="10")
        self.button_frame.pack(fill='x')

        # Botões
        self.btn_cadastrar = ttk.Button(self.button_frame, text="Cadastrar", command=self.cadastrar_frete)
        self.btn_editar = ttk.Button(self.button_frame, text="Editar", command=self.editar_frete)
        self.btn_excluir = ttk.Button(self.button_frame, text="Excluir", command=self.excluir_frete)
        self.btn_atualizar = ttk.Button(self.button_frame, text="Atualizar", command=self.atualizar_frete)
        self.btn_cadastrar.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.btn_editar.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.btn_excluir.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        self.btn_atualizar.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
        self.button_frame.grid_columnconfigure(3, weight=1)

        # Adicionando o Treeview
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(self.tree_frame, columns=("ID", "NomeRota", "CidadeColeta", "CidadeEntrega", "SLA", "Distancia"), show='headings')
        self.tree.pack(side='left', fill='both', expand=True)
        
        # Definindo os cabeçalhos
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column("ID", anchor="center", width=50, minwidth=50)
            self.tree.column("NomeRota", anchor="center", width=150, minwidth=100)
            self.tree.column("CidadeColeta", anchor="center", width=150, minwidth=100)
            self.tree.column("CidadeEntrega", anchor="center", width=150, minwidth=100)
            self.tree.column("SLA", anchor="center", width=80, minwidth=50)
            self.tree.column("Distancia", anchor="center", width=80, minwidth=50, stretch=tk.NO)
        
        # Adicionando a Scrollbar
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscroll=self.scrollbar.set)
        
        # Carrega dados iniciais para o Treeview
        self.atualizar_frete()

        # Configurar o grid para que os widgets de entrada expandam corretamente
        self.entry_frame.grid_columnconfigure(1, weight=1)

        # Botão de Cadastrar
        cadastrar_button = ttk.Button(self, text="Cadastrar", command=self.cadastrar_frete)
        cadastrar_button.pack(fill='x', padx=10, pady=10)   

    def on_nome_rota_change(self):
        # Atualiza o valor da variável para ser sempre em maiúsculas
        self.nome_rota_var.set(self.nome_rota_var.get().upper())

    def on_cidade_coleta_selecionada(self, event=None):
        # Método chamado quando uma cidade é selecionada no combobox de coleta
        cidade_coleta = self.cidade_coleta_cb.get()
        uf_coleta = self.get_uf_da_cidade(cidade_coleta)
        self.uf_coleta_var.set(uf_coleta)
        self.atualizar_cidades_entrega(cidade_coleta)
        # Remover a cidade selecionada para coleta das opções de entrega
        self.atualizar_cidade_entrega_opcoes(cidade_coleta)

    def on_cidade_entrega_selecionada(self, event=None):
        # Método chamado quando uma cidade é selecionada no combobox de entrega
        cidade_entrega = self.cidade_entrega_cb.get()
        uf_entrega = self.get_uf_da_cidade(cidade_entrega)
        self.uf_entrega_var.set(uf_entrega)
        # Remover a cidade selecionada para entrega das opções de coleta
        self.atualizar_cidade_coleta_opcoes(cidade_entrega)

    def atualizar_cidade_entrega_opcoes(self, cidade_excluida):
        # Atualiza as opções do combobox de cidades de entrega, excluindo a cidade de coleta
        cidades = self.get_nomes_cidades_filiais()
        cidades = [cidade for cidade in cidades if cidade != cidade_excluida]
        self.cidade_entrega_cb['values'] = cidades
        if self.cidade_entrega_cb.get() == cidade_excluida:
            self.cidade_entrega_cb.set('')

    def atualizar_cidade_coleta_opcoes(self, cidade_excluida):
        # Atualiza as opções do combobox de cidades de coleta, excluindo a cidade de entrega
        cidades = self.get_nomes_cidades_filiais()
        cidades = [cidade for cidade in cidades if cidade != cidade_excluida]
        self.cidade_coleta_cb['values'] = cidades
        if self.cidade_coleta_cb.get() == cidade_excluida:
            self.cidade_coleta_cb.set('')

    def atualizar_cidades_entrega(self, cidade_excluida):
        # Atualiza as opções do combobox de cidades de entrega, excluindo a cidade de coleta
        cidades = self.get_nomes_cidades_filiais()
        cidades = [cidade for cidade in cidades if cidade != cidade_excluida]
        self.cidade_entrega_cb['values'] = cidades

    def get_uf_da_cidade(self, cidade):
        # Método para obter o UF da cidade selecionada
        cidades_ufs = self.db.buscar_cidades_filiais()  # Supondo que retorna uma lista de tuplas (Cidade, UF)
        for cidade_uf in cidades_ufs:
            if cidade == cidade_uf[0]:
                return cidade_uf[1]  # Retorna o UF correspondente à cidade
        return ''  # Retorna string vazia se a cidade não for encontrada
    
    def get_filiais(self):
        try:
            return self.db.buscar_ids_filiais()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar filiais: {e}")
            return []

    def get_nomes_cidades_filiais(self):
        cidades_ufs = self.db.buscar_cidades_filiais()
        return [cidade_uf[0] for cidade_uf in cidades_ufs]  # Ajuste para retornar apenas as cidades

    def validate_integer(self, value_if_allowed):
        if value_if_allowed == '':
            return True
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False        
        
    def cadastrar_frete(self):
        nome_rota = self.nome_rota_var.get().strip()
        cidade_coleta = self.cidade_coleta_var.get().strip()
        cidade_entrega = self.cidade_entrega_var.get().strip()
        sla_dias = self.sla_dias_var.get().strip()
        dist_km = self.dist_km_var.get().strip()
        

        if not all([nome_rota, cidade_coleta, cidade_entrega, sla_dias, dist_km]):
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
            return
        try:
            self.db.cadastrar_frete(nome_rota, cidade_coleta, cidade_entrega, sla_dias, dist_km)
            messagebox.showinfo("Sucesso", "Frete cadastrado com sucesso!")
            self.atualizar_frete()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar frete: {e}")

    def editar_frete(self):
        selected_item = self.tree.selection()
        if selected_item:
            # Obtenha o ID do frete selecionado
            id_frete = self.tree.item(selected_item, 'values')[0]
            # Crie a janela de edição passando o ID e o callback para atualizar
            janela_edicao = EdicaoFrete(self.master, id_frete, self.atualizar_frete)
            janela_edicao.grab_set()
        else:
            messagebox.showwarning("Atenção", "Selecione um frete para editar.")

    def excluir_frete(self):
        selected_item = self.tree.selection()
        if selected_item:
            rota_id = self.tree.item(selected_item, 'values')[0]
            if messagebox.askyesno("Confirmar", "Deseja excluir este frete?"):
                try:
                    self.db.excluir_frete(rota_id)
                    self.atualizar_frete()
                    messagebox.showinfo("Sucesso", "Frete excluído com sucesso!")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao excluir frete: {e}")

    def atualizar_frete(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            fretes = self.db.buscar_todos_fretes()
            for frete in fretes:
                self.tree.insert('', 'end', values=frete)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar fretes: {e}")

    def atualizar(self):
        if self.atualizar_callback is not None:
            self.atualizar_callback()

class EdicaoFrete(tk.Toplevel):
    def __init__(self, master, id_frete, atualizar_callback):
        super().__init__(master)
        self.grab_set()      
        self.id_frete = id_frete
        self.atualizar_callback = atualizar_callback
        self.db = DatabaseManager('tms.db')
        self.configure(background='#333333')
        style = ttk.Style(self)
        style.theme_use('clam')
        self.title("Editar Frete")
        self.geometry("400x300")
        centralizar_janela_login(self, 300, 315) 
        self.resizable(False, False)
        self.iconbitmap(icon_path)
        
           
        def validate_integer(value_if_allowed):
            if value_if_allowed == '':
                return True
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False

        self.vcmd = (self.register(validate_integer), '%P')

        self.dados_uf_cidades = {
                'AM': ['Coari', 'Itacoatiara', 'Manacapuru', 'Manaus', 'Parintins'],
                'BA': ['Camaçari', 'Feira de Santana', 'Itabuna', 'Salvador', 'Vitória da Conquista'],
                'CE': ['Caucaia', 'Fortaleza', 'Juazeiro do Norte', 'Maracanaú', 'Sobral'],
                'GO': ['Anápolis', 'Aparecida de Goiânia', 'Goiânia', 'Luziânia', 'Rio Verde'],
                'MG': ['Belo Horizonte', 'Juiz de Fora', 'Ouro Preto', 'Poços de Caldas', 'Uberlândia'],
                'MT': ['Cuiabá', 'Rondonópolis', 'Sinop', 'Tangará da Serra', 'Várzea Grande'],
                'PA': ['Belém', 'Castanhal', 'Marabá', 'Parauapebas', 'Santarém'],
                'PE': ['Caruaru', 'Garanhuns', 'Olinda', 'Petrolina', 'Recife'],
                'PR': ['Curitiba', 'Foz do Iguaçu', 'Londrina', 'Maringá', 'Ponta Grossa'],
                'RJ': ['Campos dos Goytacazes', 'Niterói', 'Petropolis', 'Rio de Janeiro', 'Volta Redonda'],
                'RS': ['Caxias do Sul', 'Gramado', 'Pelotas', 'Porto Alegre', 'Santa Maria'],
                'SC': ['Blumenau', 'Chapecó', 'Criciúma', 'Florianópolis', 'Joinville'],
                'SP': ['Campinas', 'Ribeirão Preto', 'Santos', 'Sorocaba', 'São Paulo']
            }

        self.nome_rota_var = tk.StringVar()
        self.cidade_coleta_var = tk.StringVar()
        self.cidade_entrega_var = tk.StringVar()
        self.uf_coleta_var = tk.StringVar()  
        self.uf_entrega_var = tk.StringVar()  
        self.sla_dias_var = tk.StringVar()
        self.dist_km_var = tk.StringVar()

        # Dados para os comboboxes de cidades e UFs
        self.lista_cidades = [cidade for cidade, uf in self.dados_uf_cidades]
        
        self.create_widgets()

        self.load_frete_data()
                
    def create_widgets(self):
        self.entry_frame = ttk.Frame(self, padding="10")
        self.entry_frame.pack(fill='x', padx=10, pady=10)
        style = ttk.Style()
        style.configure("Disabled.TEntry", foreground="#b3b3b3", background="#e6e6e6")

        # Label e Entry para Nome da Rota
        ttk.Label(self.entry_frame, text="Nome da Rota:").grid(row=0, column=0, sticky='w')
        nome_rota_entry = ttk.Entry(self.entry_frame, textvariable=self.nome_rota_var)
        nome_rota_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        nome_rota_entry.bind('<KeyRelease>', self.nome_rota_to_upper)
        
        # Combobox para Cidade de Coleta
        ttk.Label(self.entry_frame, text="Cidade de Coleta:").grid(row=1, column=0, sticky='w')
        self.cidade_coleta_combobox = ttk.Combobox(self.entry_frame, textvariable=self.cidade_coleta_var, state="readonly")
        self.cidade_coleta_combobox['values'] = self.get_nomes_cidades_filiais()
        self.cidade_coleta_combobox.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.cidade_coleta_combobox.bind('<<ComboboxSelected>>', self.on_cidade_coleta_selecionada)
      
        # Entry somente leitura para UF de Coleta com estilo aplicado
        ttk.Label(self.entry_frame, text="UF de Coleta:").grid(row=2, column=0, sticky='w')
        self.uf_coleta_var = tk.StringVar()
        uf_coleta_entry = ttk.Entry(self.entry_frame, textvariable=self.uf_coleta_var, state="readonly", style="Disabled.TEntry")
        uf_coleta_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

        # Combobox para Cidade de Entrega
        ttk.Label(self.entry_frame, text="Cidade de Entrega:").grid(row=3, column=0, sticky='w')
        self.cidade_entrega_combobox = ttk.Combobox(self.entry_frame, textvariable=self.cidade_entrega_var, state="readonly")
        self.cidade_entrega_combobox['values'] = self.get_nomes_cidades_filiais()
        self.cidade_entrega_combobox.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        self.cidade_entrega_combobox.bind('<<ComboboxSelected>>', self.on_cidade_entrega_selecionada)   

        # Entry somente leitura para UF de Entrega com estilo aplicado
        ttk.Label(self.entry_frame, text="UF de Entrega:").grid(row=4, column=0, sticky='w')
        self.uf_entrega_var = tk.StringVar()
        uf_entrega_entry = ttk.Entry(self.entry_frame, textvariable=self.uf_entrega_var, state="readonly", style="Disabled.TEntry")
        uf_entrega_entry.grid(row=4, column=1, sticky='ew', padx=5, pady=5)

        # Entry para SLA em Dias com validação
        ttk.Label(self.entry_frame, text="SLA em Dias:").grid(row=5, column=0, sticky='w')
        self.sla_dias_entry = ttk.Entry(self.entry_frame, textvariable=self.sla_dias_var, validate="key", validatecommand=self.vcmd)
        self.sla_dias_entry.grid(row=5, column=1, sticky='ew', padx=5, pady=5)

        # Entry para Distância em KM com validação
        ttk.Label(self.entry_frame, text="Distância em KM:").grid(row=6, column=0, sticky='w')
        self.dist_km_entry = ttk.Entry(self.entry_frame, textvariable=self.dist_km_var, validate="key", validatecommand=self.vcmd)
        self.dist_km_entry.grid(row=6, column=1, sticky='ew', padx=5, pady=5)
        
        # Configurar o grid para que os widgets de entrada expandam corretamente
        self.entry_frame.grid_columnconfigure(1, weight=1)
        
        # Botão Salvar
        save_button = ttk.Button(self, text="Salvar Edições", command=self.salvar_edicoes)
        save_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def nome_rota_to_upper(self, event=None):
        self.nome_rota_var.set(self.nome_rota_var.get().upper())
            
    def get_nomes_cidades_filiais(self):
        cidades_ufs = self.db.buscar_cidades_filiais()
        lista_cidades = [cidade_uf[0] for cidade_uf in cidades_ufs]  # Extrai apenas as cidades
        return lista_cidades

    def on_cidade_coleta_selecionada(self, event=None):
        cidade_coleta_selecionada = self.cidade_coleta_combobox.get()
        uf_correspondente = self.obter_uf_da_cidade(cidade_coleta_selecionada)
        self.uf_coleta_var.set(uf_correspondente)
        self.atualizar_cidade_entrega_combobox(cidade_excluida=cidade_coleta_selecionada)

    def on_cidade_entrega_selecionada(self, event=None):
        cidade_entrega_selecionada = self.cidade_entrega_combobox.get()
        uf_correspondente = self.obter_uf_da_cidade(cidade_entrega_selecionada)
        self.uf_entrega_var.set(uf_correspondente)
        self.atualizar_cidade_coleta_combobox(cidade_excluida=cidade_entrega_selecionada)

    def atualizar_cidade_entrega_combobox(self, cidade_excluida):
        cidades = self.get_nomes_cidades_filiais()
        cidades_filtradas = [cidade for cidade in cidades if cidade != cidade_excluida]
        self.cidade_entrega_combobox['values'] = cidades_filtradas

    def atualizar_cidade_coleta_combobox(self, cidade_excluida):
        cidades = self.get_nomes_cidades_filiais()
        cidades_filtradas = [cidade for cidade in cidades if cidade != cidade_excluida]
        self.cidade_coleta_combobox['values'] = cidades_filtradas

    def obter_uf_da_cidade(self, cidade_selecionada):
        for cidade_uf in self.db.buscar_cidades_filiais():
            if cidade_uf[0] == cidade_selecionada:
                return cidade_uf[1]
        return ''  # Retorna string vazia se a cidade não for encontrada
       
    def load_frete_data(self):
        frete_data = self.db.buscar_frete_por_id(self.id_frete)
        if frete_data:
            # Atualize os campos com os dados do frete
            self.nome_rota_var.set(frete_data[1]) 
            self.cidade_coleta_var.set(frete_data[2])
            self.cidade_entrega_var.set(frete_data[3])
            self.sla_dias_var.set(frete_data[4])
            self.dist_km_var.set(frete_data[5])
            self.on_cidade_coleta_selecionada()
            self.on_cidade_entrega_selecionada()
        else:
            messagebox.showerror("Erro", "Dados do frete não encontrados.")
            self.destroy()

    def salvar_edicoes(self):
        nome_rota = self.nome_rota_var.get()
        cidade_coleta = self.cidade_coleta_var.get()
        cidade_entrega = self.cidade_entrega_var.get()
        uf_coleta = self.uf_coleta_var.get()
        uf_entrega = self.uf_entrega_var.get()
        sla_dias = self.sla_dias_var.get()
        dist_km = self.dist_km_var.get()

        try:
            self.db.atualizar_frete(self.id_frete, nome_rota, cidade_coleta, cidade_entrega, uf_coleta, uf_entrega, sla_dias, dist_km)
            messagebox.showinfo("Sucesso", "Frete atualizado com sucesso!")
            self.atualizar_callback()  # Chame o callback para atualizar a visualização na tela principal, se necessário
            self.destroy()  # Fecha a janela de edição
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar frete: {e}")

class CadastroSolicitacaoEntrega(tk.Toplevel):
    def __init__(self, master, login, user_id=None):
        super().__init__(master)
        self.withdraw()
        self.db = DatabaseManager('tms.db')
        self.usuario_logado = login
        self.user_id = user_id
        style = ttk.Style(self)
        style.theme_use('clam')
        self.configure(background='#333333')
        self.title("Cadastro de Solicitação de Entrega")
        self.geometry("600x400")
        centralizar_janela_login(self , 1024 , 568)
        self.resizable(False, False)
        self.iconbitmap(icon_path)
        self.create_widgets()
        
        self.update_idletasks()
        self.after(10, self.mostrar_janela)

    def mostrar_janela(self):
        self.deiconify()

    def create_widgets(self):
        self.entry_frame = ttk.Frame(self, padding="10")
        self.entry_frame.pack(fill='x', padx=10, pady=10)
        self.entry_frame.grid_rowconfigure(13, weight=1)
        self.entry_frame.grid_columnconfigure(1, weight=1)

        # Tipo de Carro
        ttk.Label(self.entry_frame, text="Tipo de Carro:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.tipo_carro_var = tk.StringVar()
        self.tipo_carro_cb = ttk.Combobox(self.entry_frame, textvariable=self.tipo_carro_var, state="readonly")
        self.tipo_carro_cb.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.carregar_tipos_carro()
        self.tipo_carro_var.set("Escolha o Carro") 
        self.tipo_carro_cb.bind("<<ComboboxSelected>>", self.on_tipo_carro_selected)

        # Placa
        ttk.Label(self.entry_frame, text="Placa:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.placa_var = tk.StringVar()
        self.placa_cb = ttk.Combobox(self.entry_frame, textvariable=self.placa_var, state="readonly")
        self.placa_cb.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.tipo_carro_cb.bind('<<ComboboxSelected>>', self.on_tipo_carro_selected)
        self.placa_cb.bind('<<ComboboxSelected>>', self.atualizar_carro_id)
        self.tipo_carro_var.set("Escolha o Carro") 

        # Data Coleta
        ttk.Label(self.entry_frame, text="Data Coleta:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.data_coleta = DateEntry(self.entry_frame, locale='pt_BR' , date_pattern='dd-mm-yyyy', width=6, background='silver',
                                               foreground='dimgray', borderwidth=1, state="readonly")
        self.data_coleta.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

        # Data Esperada da Entrega
        ttk.Label(self.entry_frame, text="Data Esperada da Entrega:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.data_esperada_entrega = DateEntry(self.entry_frame, locale='pt_BR' , date_pattern='dd-mm-yyyy', width=6, background='silver',
                                               foreground='dimgray', borderwidth=1, state="readonly")
        self.data_esperada_entrega.grid(row=3, column=1, sticky='ew', padx=5, pady=5)

        # Nome da Rota
        ttk.Label(self.entry_frame, text="Nome da Rota:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.nome_rota_var = tk.StringVar()
        self.nome_rota_cb = ttk.Combobox(self.entry_frame, textvariable=self.nome_rota_var, state="readonly")
        self.nome_rota_cb.grid(row=4, column=1, sticky='ew', padx=5, pady=5)
        self.carregar_nomes_rota()
        self.setup_placeholder_rota()
        self.nome_rota_cb.bind("<<ComboboxSelected>>", self.atualizar_rota_id)

       # Valor da Carga
        ttk.Label(self.entry_frame, text="Valor da Carga:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        self.valor_carga_var = tk.StringVar(value="R$0,00")
        self.valor_carga_entry = ttk.Entry(self.entry_frame, textvariable=self.valor_carga_var)  # Defina a variável aqui
        self.valor_carga_entry.grid(row=5, column=1, sticky='ew', padx=5, pady=5)
        self.valor_carga_entry.bind('<KeyRelease>', self.on_value_change)
        self.valor_carga_entry.bind('<FocusIn>', self.on_focus_in_valor_carga)

        # Carro ID
        ttk.Label(self.entry_frame, text="Carro ID:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        self.carro_id_var = tk.StringVar()
        ttk.Entry(self.entry_frame, textvariable=self.carro_id_var, state="readonly", foreground="gray").grid(row=6, column=1, sticky='ew', padx=5, pady=5)

        # Rota ID
        ttk.Label(self.entry_frame, text="Rota ID:").grid(row=7, column=0, sticky='w', padx=5, pady=5)
        self.rota_id_var = tk.StringVar()
        ttk.Entry(self.entry_frame, textvariable=self.rota_id_var, state="readonly", foreground="gray").grid(row=7, column=1, sticky='ew', padx=5, pady=5)

        # Data da Solicitação
        ttk.Label(self.entry_frame, text="Data da Solicitação:").grid(row=8, column=0, sticky='w', padx=5, pady=5)
        self.data_solicitacao_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(self.entry_frame, textvariable=self.data_solicitacao_var, state="readonly", foreground="gray").grid(row=8, column=1, sticky='ew', padx=5, pady=5)
        
        # Status
        ttk.Label(self.entry_frame, text="Status:").grid(row=9, column=0, sticky='w', padx=5, pady=5)
        self.status_var = tk.StringVar(value="SOLICITADO")
        ttk.Entry(self.entry_frame, textvariable=self.status_var, state="readonly", foreground="gray").grid(row=9, column=1, sticky='ew', padx=5, pady=5)

        # Status ID
        ttk.Label(self.entry_frame, text="Status ID:").grid(row=10, column=0, sticky='w', padx=5, pady=5)
        self.status_id_var = tk.StringVar(value="0")
        ttk.Entry(self.entry_frame, textvariable=self.status_id_var, state="readonly", foreground="gray").grid(row=10, column=1, sticky='ew', padx=5, pady=5)

        # UserID
        ttk.Label(self.entry_frame, text="User ID:").grid(row=11, column=0, sticky='w', padx=5, pady=5)
        self.user_id_var = tk.StringVar(value=self.user_id)
        ttk.Entry(self.entry_frame, textvariable=self.user_id_var, state="readonly", foreground="gray").grid(row=11, column=1, sticky='ew', padx=5, pady=5)

        # Espaço após os widgets atuais e antes do botão Salvar
        self.info_frame = ttk.Frame(self.entry_frame, padding="10")
        self.info_frame.grid(row=13, column=0, columnspan=3, pady=(10, 0), sticky='ew')

        # SLA da Rota
        ttk.Label(self.info_frame, text="             Previsão de Entrega:" ,font=('Arial', 14)).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.sla_var = tk.StringVar(value="")
        self.sla_label = ttk.Entry(self.info_frame, textvariable=self.sla_var, font=('Arial', 14), foreground='ghostwhite' , state="readonly")
        self.sla_label.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        # Valor do Frete
        ttk.Label(self.info_frame, text="  Valor do Frete:" , font=('Arial', 14)).grid(row=0, column=3, sticky='w', padx=5, pady=5)
        self.frete_var = tk.StringVar(value="")
        self.frete_label = ttk.Entry(self.info_frame, textvariable=self.frete_var, font=('Arial', 14), foreground='ghostwhite' , state="readonly")
        self.frete_label.grid(row=0, column=4, sticky='e', padx=5, pady=5)

        # Botão para salvar a solicitação
        self.botao_salvar = ttk.Button(self.entry_frame, text="Salvar Solicitação", command=self.salvar_solicitacao)
        self.botao_salvar.grid(row=12, column=0, columnspan=2, pady=10, sticky='ew')
     
    def atualizar_carro_id(self , event=None):
        placa_selecionada = self.placa_var.get()
        carro_id = self.db.buscar_carro_id_por_placa(placa_selecionada)
        self.carro_id_var.set(carro_id if carro_id else "Desconhecido")
        self.atualizar_sla_e_frete()

    def carregar_placas(self):
        placas = self.db.buscar_placas_por_tipo(self.tipo_carro_var.get())
        self.placa_cb['values'] = placas
        if placas:
            self.placa_cb.set(placas[0])
            self.atualizar_carro_id()

    def carregar_tipos_carro(self):
        tipos_carro = self.db.buscar_tipos_carro()
        self.tipo_carro_cb['values'] = tipos_carro

    def on_tipo_carro_selected(self, event):
        tipo_carro_selecionado = self.tipo_carro_var.get()
        placas = self.db.buscar_placas_por_tipo(tipo_carro_selecionado)
        self.placa_cb['values'] = placas
        if placas:
            self.placa_cb.set(placas[0])
            self.atualizar_carro_id()
        else:
            self.placa_cb.set('')
            self.carro_id_var.set('')

    def setup_placeholder(self):
        self.tipo_carro_cb.set("Escolha o Carro")  
        self.tipo_carro_cb.bind("<FocusIn>", lambda event: self.clear_placeholder(event, "Selecione o Carro"))
        self.tipo_carro_cb.bind("<FocusOut>", lambda event: self.restore_placeholder(event, "Selecione o Carro"))

    def clear_placeholder(self, event, placeholder):
        if self.tipo_carro_cb.get() == placeholder:
            self.tipo_carro_cb.set("")  

    def restore_placeholder(self, event, placeholder):
        if not self.tipo_carro_cb.get():
            self.tipo_carro_cb.set(placeholder)  

    def carregar_nomes_rota(self):
        nomes_rotas = self.db.buscar_nomes_rotas()
        self.nome_rota_cb['values'] = nomes_rotas
        self.nome_rota_cb.set("Selecione a Rota")

    def setup_placeholder_rota(self):
        self.nome_rota_cb.bind("<FocusIn>", lambda event: self.clear_placeholder(event, self.nome_rota_cb, "Selecione a Rota"))
        self.nome_rota_cb.bind("<FocusOut>", lambda event: self.restore_placeholder(event, self.nome_rota_cb, "Selecione a Rota"))

    def clear_placeholder(self, event, combobox, placeholder):
        if combobox.get() == placeholder:
            combobox.set('')  

    def restore_placeholder(self, event, combobox, placeholder):
        if not combobox.get():
            combobox.set(placeholder) 
             
    def on_focus_in_valor_carga(self, event=None):
        self.valor_carga_entry.select_range(0, tk.END)
        self.valor_carga_entry.icursor(tk.END)

    def on_click_valor_carga(self, event=None):
        # Posiciona o cursor no final do texto
        self.valor_carga_entry.focus()
        self.valor_carga_entry.icursor(tk.END)

    def on_value_change(self, *args):
        # Remove a formatação atual para obter apenas números.
        stripped_value = self.valor_carga_var.get().replace('R$', '').replace('.', '').replace(',', '')
        # Trata o caso de string vazia atribuindo '0'.
        stripped_value = '0' if stripped_value == '' else stripped_value
        # Converte para inteiro (centavos) para facilitar manipulações.
        current_value = int(stripped_value)
        try:
            formatted_value = 'R$ {:,.2f}'.format(current_value / 100.0).replace(',', 'X').replace('.', ',').replace('X', '.')
            self.valor_carga_var.set(formatted_value)
            self.valor_carga_entry.icursor(tk.END)
        except ValueError:
            # Trata o caso de valores inválidos.
            self.valor_carga_var.set("R$0,00")

    def atualizar_rota_id(self, event=None):
        nome_rota_selecionada = self.nome_rota_var.get()
        rota_id = self.db.buscar_rota_id_por_nome(nome_rota_selecionada)
        self.rota_id_var.set(rota_id if rota_id else "Desconhecido")
        self.atualizar_sla_e_frete()
           
    def salvar_solicitacao(self):
        tipo_carro = self.tipo_carro_var.get()
        placa = self.placa_var.get()
        data_coleta = self.data_coleta.get_date().strftime('%Y-%m-%d')
        data_entrega = self.data_esperada_entrega.get_date().strftime('%Y-%m-%d')
        nome_rota = self.nome_rota_var.get()
        data_solicitacao = self.data_solicitacao_var.get()
        user_id = int(self.user_id_var.get())
        valor_carga = self.valor_carga_var.get().replace('R$', '').replace('.', '')
        status_id = int(self.status_id_var.get())

        try:
            user_id = int(self.user_id_var.get()) if self.user_id_var.get() else 0
            status_id = int(self.status_id_var.get()) if self.status_id_var.get() else 0
            carro_id = int(self.carro_id_var.get()) if self.carro_id_var.get() else 0
            rota_id = int(self.rota_id_var.get()) if self.rota_id_var.get() else 0
        except ValueError as e:
            messagebox.showerror("Erro", "Por favor, insira valores válidos nos campos numéricos.")
            return

        # Verifica se algum campo obrigatório está vazio ou com valor padrão
        if tipo_carro == "Escolha o Carro" or placa == "Escolha a Placa" or nome_rota == "Selecione a Rota" or not valor_carga or not carro_id or not rota_id:
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos obrigatórios.")
            return
        else:
            # Converte as datas para objetos datetime para comparação
            data_coleta_date = datetime.datetime.strptime(data_coleta, '%Y-%m-%d')
            data_entrega_date = datetime.datetime.strptime(data_entrega, '%Y-%m-%d')
            
            # Verifica se a data de coleta é maior ou igual à data de entrega
            if data_coleta_date >= data_entrega_date:
                messagebox.showwarning("Aviso", "A data esperada de Entrega deve ser maior que a data de Coleta.")
                return      
            
        try:
            valor_carga_limpo = valor_carga.replace('R$', '').replace('.', '').replace(',', '.')
            valor_carga_numerico = float(valor_carga_limpo)
            if valor_carga_numerico <= 0:
                messagebox.showwarning("Aviso", "O valor da carga deve ser maior que 0.")
                return
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor válido para a carga.")
            return
        
        # Mensagem personalizada
        mensagem = (f"Olá {user_id}, você está prestes a solicitar uma entrega com o carro {tipo_carro} de placa {placa} "
                    f"para coleta no dia {data_coleta} e entrega no dia {data_entrega} "
                    f"para a Rota {nome_rota}, deseja confirmar solicitação?")

        # Mostra o popup de confirmação
        resposta = messagebox.askquestion("Confirmar Solicitação", mensagem)
        
        if resposta == 'yes':
            try:
                sucesso = self.db.inserir_solicitacao_entrega(carro_id, data_coleta, data_entrega, rota_id, data_solicitacao, valor_carga, status_id, user_id)
                if sucesso:
                    messagebox.showinfo("Sucesso", "Solicitação de entrega cadastrada com sucesso!")
                    self.limpar_campos()
                else:
                    raise Exception("Falha ao inserir no banco de dados.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar solicitação de entrega: {e}")

    def atualizar_sla_e_frete(self):
        rota_id = self.rota_id_var.get()
        carro_id = self.carro_id_var.get()

        # Só procede se ambos IDs estiverem disponíveis
        if rota_id and carro_id:
            # Buscar SLA da rota
            sla = self.db.buscar_sla_por_rota(rota_id)
            self.sla_var.set(f"{sla} Dias" if sla is not None else "N/A")

            # Buscar valor do km do carro e distância da rota
            valor_km = self.db.buscar_valor_km_por_carro(carro_id)
            distancia = self.db.buscar_distancia_por_rota(rota_id)

            if valor_km is not None and distancia is not None:
                # Calcular valor do frete
                valor_frete = valor_km * distancia
                self.frete_var.set(f"R$ {valor_frete:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            else:
                self.frete_var.set("N/A")
        else:
            # Se os IDs não estiverem disponíveis, resetar os valores
            self.sla_var.set("")
            self.frete_var.set("")

    def limpar_campos(self):
        # Define os valores padrões para os campos após limpeza
        self.tipo_carro_var.set("Escolha o Carro")  # ou ""
        self.placa_var.set("Escolha a Placa")  # ou ""
        self.data_coleta.set_date(datetime.datetime.now())  # Define a data atual
        self.data_esperada_entrega.set_date(datetime.datetime.now())  # Define a data atual
        self.nome_rota_var.set("Selecione a Rota")  # ou ""
        self.valor_carga_var.set("R$ 0,00")
        self.carro_id_var.set("")
        self.rota_id_var.set("")
        self.status_var.set("SOLICITADO")
        self.status_id_var.set("0")
        self.user_id_var.set(self.usuario_logado)
        self.sla_var.set("")
        self.frete_var.set("")

class GerenciamentoEntregas(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Gerenciamento de Entregas")
        self.db = DatabaseManager('tms.db')
        style = ttk.Style(self)
        style.theme_use('clam')
        self.configure(background='#333333')
        centralizar_janela_login(self , 1368 , 568)
        self.resizable(False, False)

        self.create_widgets()
        self.preencher_comboboxes()
        self.atualizar_treeview()
        self.iconbitmap(icon_path)
        
    def create_widgets(self):
        # Frame de Filtros
        self.filtros_frame = ttk.Frame(self)
        self.filtros_frame.pack(fill='x', padx=10, pady=10)

        # Campo de Filtro para EntregaID
        ttk.Label(self.filtros_frame, text="                     ID da Entrega:").pack(side='left', padx=(0, 10))
        self.entrega_id_cb = ttk.Combobox(self.filtros_frame, width=15 , state="readonly")
        self.entrega_id_cb.pack(side='left')

        # Campo de Filtro para Placa
        ttk.Label(self.filtros_frame, text="Placa:").pack(side='left', padx=(10, 10))
        self.placa_cb = ttk.Combobox(self.filtros_frame, width=15, state="readonly")
        self.placa_cb.pack(side='left')

        # Campo de Filtro para Nome da Rota
        ttk.Label(self.filtros_frame, text="Nome da Rota:").pack(side='left', padx=(10, 10))
        self.nome_rota_cb = ttk.Combobox(self.filtros_frame, width=15, state="readonly")
        self.nome_rota_cb.pack(side='left')
        
        # Campo de Filtro para STATUS
        ttk.Label(self.filtros_frame, text="Status:").pack(side='left', padx=(10, 10))
        self.status_cb = ttk.Combobox(self.filtros_frame, width=15, state="readonly")
        self.status_cb.pack(side='left')
        
        # Campo de Filtro para USer
        ttk.Label(self.filtros_frame, text="Usuario:").pack(side='left', padx=(10, 10))
        self.user_cb = ttk.Combobox(self.filtros_frame, width=15, state="readonly")
        self.user_cb.pack(side='left')

        # Botão de Pesquisa
        style = ttk.Style(self)
        style.configure('Green.TButton', foreground='white', background='#4CAF50')
        self.pesquisar_button = ttk.Button(self.filtros_frame, text="Pesquisar", command=self.pesquisar , style='Green.TButton')
        self.pesquisar_button.pack(side='left', padx=(100, 0))

        # Treeview
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("EntregaID","CarroID", "Placa", "DataColeta", "DataEsperadaEntrega", "RotaID", 
                                                   "NomeRota", "DataSolicitacaoEntrega", "ValorCarga", "StatusID",
                                                   "STATUS", "UserID","Login"), show="headings")
        self.tree.column("EntregaID", width=40)
        self.tree.column("CarroID", width=35)
        self.tree.column("RotaID", width=35)
        self.tree.column("StatusID", width=35)
        self.tree.column("UserID", width=35)
        self.tree.column("Placa", width=45)
               
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            if col not in ["EntregaID" , "CarroID" , "RotaID" , "StatusID" , "UserID","Placa"]:
                self.tree.column(col, width=100)

        # Scrollbar para o Treeview
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree_scroll.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree.pack(fill='both', expand=True)

        # Botão para editar o StatusID
        style = ttk.Style(self)
        style.configure('edit.TButton', foreground='white',  font=('Arial', 12, 'bold'))
        self.editar_status_button = ttk.Button(self, text="Editar Status", command=self.editar_status ,style='edit.TButton')
        self.editar_status_button.pack(fill='x', padx=10, pady=10)

    def pesquisar(self):
        # Obtém os valores selecionados nos comboboxes
        entrega_id = self.entrega_id_cb.get() if self.entrega_id_cb.get() != 'Todos' else None
        placa = self.placa_cb.get() if self.placa_cb.get() != 'Todos' else None
        nome_rota = self.nome_rota_cb.get() if self.nome_rota_cb.get() != 'Todos' else None
        status = self.status_cb.get() if self.status_cb.get() != 'Todos' else None
        usuario = self.user_cb.get() if self.user_cb.get() != 'Todos' else None

        # Verifica se todos os comboboxes estão vazios
        if not entrega_id and not placa and not nome_rota and not status and not usuario:
            # Se estiverem, busca todas as entregas
            entregas_completas = self.db.buscar_entregas_completas()
        else:
            # Caso contrário, constrói uma consulta filtrando pelos valores selecionados
            filtros = []
            parametros = []
            if entrega_id:
                filtros.append("EntregaID = ?")
                parametros.append(entrega_id)
            if placa:
                filtros.append("Placa = ?")
                parametros.append(placa)
            if nome_rota:
                filtros.append("NomeRota = ?")
                parametros.append(nome_rota)
            if status:
                filtros.append("STATUS = ?")
                parametros.append(status)
            if usuario:
                filtros.append("Login = ?")
                parametros.append(usuario)
            
            # Monta a consulta SQL com os filtros
            query = """
            SELECT fEntregas.EntregaID, dCarros.CarroID, dCarros.Placa, fEntregas.DataColeta, fEntregas.DataEsperadaEntrega, 
                dFretes.RotaID, dFretes.NomeRota, fEntregas.DataSolicitacaoEntrega, fEntregas.ValorCarga, 
                dStatus.StatusID, dStatus.STATUS, dUsers.UserID, dUsers.Login
            FROM fEntregas
            LEFT JOIN dCarros ON fEntregas.CarroID = dCarros.CarroID
            LEFT JOIN dFretes ON fEntregas.RotaID = dFretes.RotaID
            LEFT JOIN dStatus ON fEntregas.StatusID = dStatus.StatusID
            LEFT JOIN dUsers ON fEntregas.UserID = dUsers.UserID
            """
            
            if filtros:
                query += " WHERE " + " AND ".join(filtros)
            
            # Executa a consulta
            self.db.c.execute(query, parametros)
            entregas_completas = self.db.c.fetchall()

        # Limpa a treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Insere os novos dados na treeview
        for entrega in entregas_completas:
            self.tree.insert("", "end", values=entrega)

    def atualizar_treeview(self):
        # Primeiro, limpe a treeview
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        # Agora busque as entregas completas e insira na treeview
        entregas_completas = self.db.buscar_entregas_completas()
        for entrega in entregas_completas:
            # Formata as datas
            data_coleta = datetime.datetime.strptime(entrega[3], '%Y-%m-%d').strftime('%d/%m/%Y')
            data_esperada_entrega = datetime.datetime.strptime(entrega[4], '%Y-%m-%d').strftime('%d/%m/%Y')
            data_solicitacao_entrega = datetime.datetime.strptime(entrega[7], '%Y-%m-%d').strftime('%d/%m/%Y')
            
            # Converte e formata o valor da carga se não for uma string vazia
            valor_carga = entrega[8]
            if valor_carga:
                valor_carga = valor_carga.replace('.', '').replace(',', '.')
                valor_carga = locale.currency(float(valor_carga), grouping=True)
            else:
                valor_carga = locale.currency(0, grouping=True)
            
            # Cria uma nova tupla com os valores formatados
            entrega_formatada = (entrega[0], entrega[1], entrega[2], data_coleta, data_esperada_entrega, entrega[5],
                                 entrega[6], data_solicitacao_entrega, valor_carga, entrega[9], entrega[10], entrega[11], entrega[12])
            
            self.tree.insert('', 'end', values=entrega_formatada)

    def preencher_comboboxes(self):
        # Buscar todos os dados completos das entregas
        entregas_completas = self.db.buscar_entregas_completas()

        # Extrair dados únicos para cada combobox e converter todos os valores para strings
        ids_unicos = {str(entrega[0]) for entrega in entregas_completas}
        placas_unicas = {entrega[2] for entrega in entregas_completas}
        nomes_rotas_unicos = {entrega[6] for entrega in entregas_completas}
        status_unicos = {entrega[10] for entrega in entregas_completas}
        users_unicos = {entrega[12] for entrega in entregas_completas}

        # Adiciona 'Todos' na primeira posição de cada lista e ordena os valores
        self.entrega_id_cb['values'] = ['Todos'] + sorted(ids_unicos)
        self.placa_cb['values'] = ['Todos'] + sorted(placas_unicas)
        self.nome_rota_cb['values'] = ['Todos'] + sorted(nomes_rotas_unicos)
        self.status_cb['values'] = ['Todos'] + sorted(status_unicos)
        self.user_cb['values'] = ['Todos'] + sorted(users_unicos)

        # Garantir que os comboboxes comecem com 'Todos' selecionado
        self.entrega_id_cb.set('Todos')
        self.placa_cb.set('Todos')
        self.nome_rota_cb.set('Todos')
        self.status_cb.set('Todos')
        self.user_cb.set('Todos')
        
    def buscar_dados_entrega_id(self):
        # Implementação do método que buscará os dados de EntregaID no banco de dados
        # Deve retornar uma lista dos IDs de entrega
        pass

    def editar_status(self):
        selected_item = self.tree.selection()
        if not selected_item:  # Se nenhum item estiver selecionado
            messagebox.showwarning("Aviso", "Por favor, selecione uma entrega para editar o status.")
        else:
            item = self.tree.item(selected_item)
            entrega_id = item["values"][0]
            
            # Abre uma nova janela ou diálogo para editar o StatusID (implemente a janela de diálogo separadamente)
            edit_window = EditarStatusWindow(entrega_id, self.db, self.atualizar_treeview,master=self)
            edit_window.grab_set()  
            
class EditarStatusWindow(tk.Toplevel):
    def __init__(self, entrega_id ,db, atualizar_treeview ,master=None):
        super().__init__(master)
        self.entrega_id = entrega_id
        self.atualizar_treeview = atualizar_treeview
        self.title("")
        self.db = db
        style = ttk.Style(self)
        style.theme_use('clam')
        self.configure(background='#333333')
        centralizar_janela_login(self , 225 , 225)
        self.resizable(False, False)
        
        self.create_widgets()
        self.preencher_informacoes()
        self.iconbitmap(icon_path)
    
    def create_widgets(self):
        # Criação dos widgets
        self.info_label = ttk.Label(self, text="")
        self.info_label.pack(pady=10)

        self.status_cb = ttk.Combobox(self, state="readonly")
        self.status_cb.pack(pady=10)

        style = ttk.Style(self)
        style.configure('Red.TButton', foreground='white', background='#D2691E', font=('Arial', 10) )
        self.salvar_button = ttk.Button(self, text="Salvar Alterações", command=self.salvar_alteracoes , style='Red.TButton')
        self.salvar_button.pack(pady=10)

    def preencher_informacoes(self):
        # Preenchimento das informações da entrega e status do combobox
        dados_entrega = self.db.buscar_entregas_completas(self.entrega_id)[0]
        status_possiveis = self.db.buscar_todos_os_status()

        info_text = f"Entrega ID: {dados_entrega[0]}\n" \
                        f"Placa: {dados_entrega[2]}\n" \
                        f"Data Coleta: {dados_entrega[3]}\n" \
                        f"Data Entrega: {dados_entrega[4]}\n" \
                        f"Status Atual: {dados_entrega[10]}"

        self.info_label.config(text=info_text)
        
        # Para os status possíveis, também ajuste conforme necessário para acessar o índice correto
        self.status_cb['values'] = ['Selecione um status'] + [status[0] for status in status_possiveis]
        self.status_cb.set('Selecione um status')
    
    def salvar_alteracoes(self):
        # Implementação da lógica para salvar as alterações no banco de dados
        novo_status = self.status_cb.get()
        if novo_status != 'Selecione um status':
            # Atualizar no banco de dados
            self.db.atualizar_status_entrega(self.entrega_id, novo_status)
            # Feedback para o usuário
            messagebox.showinfo("Sucesso", "Status atualizado com sucesso.")
            self.atualizar_treeview()
            self.destroy()
        else:
            messagebox.showerror("Erro", "Por favor, selecione um status válido.")

def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return f'{pct:.1f}%\n({val:d})'
    return my_format

class Dashboard(tk.Toplevel):
    def __init__(self , master=None, **kw):
        super().__init__(master=master, **kw)
        self.withdraw()

        self.title("Dashboard")

        self.configure(bg="#333333")
        self.assets_path = Path(__file__).parent / "assets"
        centralizar_janela_login(self , 1080 , 800)
        self.resizable(False, False)
        self.db = DatabaseManager('tms.db')
        
        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.fechar_dashboard)
        self.iconbitmap(icon_path)
        
        self.update_idletasks()
        self.after(50, self.mostrar_janela)

    def mostrar_janela(self):
        self.deiconify()
        
    def fechar_dashboard(self):
        # Este loop destrói todos os widgets filhos, garantindo que recursos sejam liberados
        for widget in self.winfo_children():
            widget.destroy()
        self.destroy()
 
    def create_widgets(self):
        self.canvas = Canvas(
            self,
            bg="#333333",
            height=800,
            width=1080,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
               
        image_path = self.assets_path / "image_1.png"
        self.image_image_1 = PhotoImage(file=str(image_path))
        self.image_1 = self.canvas.create_image(
            934.0, 649.0,
            image=self.image_image_1
        )
        
        image_path = self.assets_path / "image_2.png"
        self.image_image_2 = PhotoImage(file=str(image_path))
        self.image_2 = self.canvas.create_image(
            934.0, 533.0,
            image=self.image_image_2
        )

        self.canvas.create_text(
            837.2257080078125,
            522.0,
            anchor="nw",
            text="Importante",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )

        image_path = self.assets_path / "image_3.png"
        self.image_image_3 = PhotoImage(file=str(image_path))
        self.image_3 = self.canvas.create_image(
            672.0,    650.0,
            image=self.image_image_3
        )        
        
        image_path = self.assets_path / "image_4.png"
        self.image_image_4 = PhotoImage(file=str(image_path))
        self.image_4 = self.canvas.create_image(
            672.0,    534.1322631835938,
            image=self.image_image_4
        )
        
        self.canvas.create_text(
            574.817138671875,
            523.13232421875,
            anchor="nw",
            text="Top10 Cidades de Entrega",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )       

        image_path = self.assets_path / "image_5.png"
        self.image_image_5 = PhotoImage(file=str(image_path))
        self.image_5 = self.canvas.create_image(
            410.0,    649.0,
            image=self.image_image_5
        )  

        image_path = self.assets_path / "image_6.png"
        self.image_image_6 = PhotoImage(file=str(image_path))
        self.image_6 = self.canvas.create_image(
            410.0,    533.0,
            image=self.image_image_6
        )  

        self.canvas.create_text(
            312.4085388183594,
            522.0,
            anchor="nw",
            text="Rota por Distância",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )

        image_path = self.assets_path / "image_7.png"
        self.image_image_7 = PhotoImage(file=str(image_path))
        self.image_7 = self.canvas.create_image(
            147.0,    649.0,
            image=self.image_image_7
        )  

        image_path = self.assets_path / "image_8.png"
        self.image_image_8 = PhotoImage(file=str(image_path))
        self.image_8 = self.canvas.create_image(
            147.0,    533.0,
            image=self.image_image_8
        ) 

        self.canvas.create_text(
            50.0,
            522.0,
            anchor="nw",
            text="Carros por Tipo",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )
        
        image_path = self.assets_path / "image_9.png"
        self.image_image_9 = PhotoImage(file=str(image_path))
        self.image_9 = self.canvas.create_image(
            932.0,    379.0,
            image=self.image_image_9
        )
        
        image_path = self.assets_path / "image_10.png"
        self.image_image_10 = PhotoImage(file=str(image_path))
        self.image_10 = self.canvas.create_image(
            932.0,    253.0,
            image=self.image_image_10
        )

        self.canvas.create_text(
            843.2915649414062,
            243.13223266601562,
            anchor="nw",
            text="Entregas por Status",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )   
        
        image_path = self.assets_path / "image_11.png"
        self.image_image_11 = PhotoImage(file=str(image_path))
        self.image_11 = self.canvas.create_image(
            670.0,    380.0,
            image=self.image_image_11
        )

        image_path = self.assets_path / "image_12.png"
        self.image_image_12 = PhotoImage(file=str(image_path))
        self.image_12 = self.canvas.create_image(
            670.0,    254.13223266601562,
            image=self.image_image_12
        )

        self.canvas.create_text(
            580.8829956054688,
            244.26446533203125,
            anchor="nw",
            text="Distribuição do SLA por Rotas",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )

        image_path = self.assets_path / "image_13.png"
        self.image_image_13 = PhotoImage(file=str(image_path))
        self.image_13 = self.canvas.create_image(
            407.0,    378.0,
            image=self.image_image_13
        )

        image_path = self.assets_path / "image_14.png"
        self.image_image_14 = PhotoImage(file=str(image_path))
        self.image_14 = self.canvas.create_image(
            407.0,    253.0,
            image=self.image_image_14
        )    

        self.canvas.create_text(
            318.4743957519531,
            243.13223266601562,
            anchor="nw",
            text="Top10 Cidades por Rotas",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )

        image_path = self.assets_path / "image_15.png"
        self.image_image_15 = PhotoImage(file=str(image_path))
        self.image_15 = self.canvas.create_image(
           145.0,    379.0,
            image=self.image_image_15
        )    

        image_path = self.assets_path / "image_16.png"
        self.image_image_16 = PhotoImage(file=str(image_path))
        self.image_16 = self.canvas.create_image(
           145.0,    253.0,
            image=self.image_image_16
        )  

        self.canvas.create_text(
            56.06585693359375,
            243.13223266601562,
            anchor="nw",
            text="Participação do Agregado",
            fill="#FFFFFF",
            font=("Arial", 13 * -1)
        )
        
        image_path = self.assets_path / "image_17.png"
        self.image_image_17 = PhotoImage(file=str(image_path))
        self.image_17 = self.canvas.create_image(
            944.0,    146.0,
            image=self.image_image_17
        )  

        self.canvas.create_text(
            880.0,
            85.0,
            anchor="nw",
            text="Entregas",
            fill="#575859",
            font=("Arial Medium", 32 * -1)
        )

        self.canvas.create_text(
            912.0,
            140.0,
            anchor="nw",
            text="",
            fill="#333333",
            font=("Inter Medium", 32 * -1)
        )

        image_path = self.assets_path / "image_18.png"
        self.image_image_18 = PhotoImage(file=str(image_path))
        self.image_18 = self.canvas.create_image(
            848.9473876953125,    144.0,
            image=self.image_image_18
        )  

        image_path = self.assets_path / "image_19.png"
        self.image_image_19 = PhotoImage(file=str(image_path))
        self.image_19 = self.canvas.create_image(
            675.0,    146.0,
            image=self.image_image_19
        )  

        self.canvas.create_text(
            620.0,
            85.0,
            anchor="nw",
            text="Filiais",
            fill="#575859",
            font=("Arial Medium", 32 * -1)
        )

        self.canvas.create_text(
            646.0,
            140.0,
            anchor="nw",
            text="",
            fill="#333333",
            font=("Inter Medium", 32 * -1)
        )

        image_path = self.assets_path / "image_20.png"
        self.image_image_20 = PhotoImage(file=str(image_path))
        self.image_20 = self.canvas.create_image(
            579.9473876953125,    144.0,
            image=self.image_image_20
        )  

        image_path = self.assets_path / "image_21.png"
        self.image_image_21 = PhotoImage(file=str(image_path))
        self.image_21 = self.canvas.create_image(
            406.0,    146.0,
            image=self.image_image_21
        )  

        self.canvas.create_text(
            351.0,
            85.0,
            anchor="nw",
            text="Rotas",
            fill="#575859",
            font=("Arial Medium", 32 * -1)
        )

        self.canvas.create_text(
            374.0,
            140.0,
            anchor="nw",
            text="",
            fill="#333333",
            font=("Inter Medium", 32 * -1)
        )

        image_path = self.assets_path / "image_22.png"
        self.image_image_22 = PhotoImage(file=str(image_path))
        self.image_22 = self.canvas.create_image(
            310.9473876953125,    144.0,
            image=self.image_image_22
        )  

        image_path = self.assets_path / "image_23.png"
        self.image_image_23 = PhotoImage(file=str(image_path))
        self.image_23 = self.canvas.create_image(
            137.0,    146.0,
            image=self.image_image_23
        )  

        self.canvas.create_text(
            74.5,
            85.0,
            anchor="nw",
            text="Carros",
            fill="#575858",
            font=("Arial Medium", 32 * -1)
        )

        self.canvas.create_text(
            101.0,
            140.0,
            anchor="nw",
            text="",
            fill="#333333",
            font=("Inter Medium", 32 * -1)
        )
        image_path = self.assets_path / "image_24.png"
        self.image_image_24 = PhotoImage(file=str(image_path))
        self.image_24 = self.canvas.create_image(
             41.9473876953125,    144.0,
            image=self.image_image_24
        )  

        image_path = self.assets_path / "image_25.png"
        self.image_image_25 = PhotoImage(file=str(image_path))
        self.image_25 = self.canvas.create_image(
             540.0,    31.0,
            image=self.image_image_25
        )  
        
        image_path = self.assets_path / "image_26.png"
        self.image_image_26 = PhotoImage(file=str(image_path))
        self.image_26 = self.canvas.create_image(
             379.0,    31.0,
            image=self.image_image_26
        )  

        image_path = self.assets_path / "image_27.png"
        self.image_image_27 = PhotoImage(file=str(image_path))
        self.image_27 = self.canvas.create_image(
             39.0,    31.0,
            image=self.image_image_27
        )  

        image_path = self.assets_path / "image_28.png"
        self.image_image_28 = PhotoImage(file=str(image_path))
        self.image_28 = self.canvas.create_image(
              224.0,    198.0,
            image=self.image_image_28
        )  
        
        image_path = self.assets_path / "image_29.png"
        self.image_image_29 = PhotoImage(file=str(image_path))
        self.image_29 = self.canvas.create_image(
                 494.0,    198.0,
            image=self.image_image_29
        )  

        image_path = self.assets_path / "image_30.png"
        self.image_image_30 = PhotoImage(file=str(image_path))
        self.image_30 = self.canvas.create_image(
                 767.0,    195.0,
            image=self.image_image_30
        )  

        image_path = self.assets_path / "image_31.png"
        self.image_image_31 = PhotoImage(file=str(image_path))
        self.image_31 = self.canvas.create_image(
                 1034.0,    195.0,
            image=self.image_image_31
        )  

        self.create_status_chart()
        self.create_carros_agregado_chart()
        self.create_rota_cidade_chart()
        self.create_sla_chart()
        self.create_carros_tipo_chart()
        self.create_rota_distancia_chart()
        self.create_top_cidades_entrega_chart()
        self.create_info_cards()
        self.create_cards()
        
    def formatar_valor_monetario(self,valor):
        return locale.currency(valor, grouping=True)

    def formatar_distancia(self,valor):
        return f"{int(valor):n}".replace(',', '.')

    def prepare_sla_data(self):
        rows = self.db.buscar_sla_por_rota_dash()
        df = pd.DataFrame(rows, columns=['SLAemDias', 'RotaID'])
        return df

    def place_sla_chart(self, sla_data):     
        fig = Figure(figsize=(2.2, 2.2), tight_layout=True)
        ax = fig.add_subplot(111)
            
        fig.set_facecolor('#D9D9D9')  
        ax.set_facecolor('#D9D9D9') 

        sla_data['SLAemDias'] = sla_data['SLAemDias'].astype(str)
    
        # Criar o gráfico de linha com a fonte dos números do eixo X ainda menor
        ax.plot(sla_data['SLAemDias'], sla_data['RotaID'], marker='o', linestyle='-', color='#2C7E8C', linewidth=0.7, markersize=3)

        ax.set_position([0, 0, 1, 1])

        # Remover rótulos do eixo Y e título
        ax.set_yticks([])
        ax.set_title("")

        # Adicionar quantidade acima do marcador com fonte menor
        for i, txt in enumerate(sla_data['RotaID']):
            ax.annotate(txt, (sla_data['SLAemDias'][i], sla_data['RotaID'][i]), textcoords="offset points", xytext=(0,5), ha='center', fontsize=7)

        # Ajustar os números (ticks) do eixo X com fonte menor (4)
        ax.tick_params(axis='x', labelsize=7)
        ax.set_xlabel('SLA em Dias', fontsize=6)

        # Ajustar spines para serem mais finos
        ax.spines['top'].set_linewidth(0)
        ax.spines['right'].set_linewidth(0)
        ax.spines['left'].set_linewidth(0)
        ax.spines['bottom'].set_linewidth(0.5)

        # Melhorar o layout
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
         
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().place(x=565, y=268)

    def create_sla_chart(self):
        sla_data = self.prepare_sla_data()
        self.place_sla_chart(sla_data)

    def prepare_rota_cidade_data(self):
        rows = self.db.buscar_rotas_por_cidade()
        df = pd.DataFrame(rows, columns=['CidadeEntrega', 'Quantidade'])
        df = df.nlargest(10, 'Quantidade')
        return df

    def place_rota_cidade_chart(self, rota_cidade_counts):
        fig = Figure(figsize=(2.29, 2.18), dpi=100 , tight_layout=False)
        fig.patch.set_facecolor('#D9D9D9')
        ax = fig.add_subplot(111,facecolor='#D9D9D9' , frameon=False)
        
        palette = list(reversed(sns.color_palette("crest", len(rota_cidade_counts))))
      
        sns.barplot(x='Quantidade', y='CidadeEntrega', data=rota_cidade_counts, ax=ax, palette=palette)
        
        ax.set_yticklabels(ax.get_yticklabels(), fontsize=7 , color='#333232')
        
        ax.set_title('')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        sns.despine(left=True, bottom=True)
        for p in ax.patches:
            ax.annotate(f"{int(p.get_width())}", 
                        (p.get_width(), p.get_y() + p.get_height() / 2), 
                        xytext=(6, -0.5), 
                        textcoords='offset points', 
                        ha='center', 
                        va='center', 
                        fontsize=9, 
                        color='#333232')
            
        for i, p in enumerate(ax.patches):
            width = p.get_width()
            ax.annotate(f"{rota_cidade_counts['CidadeEntrega'][i]}", 
                        (width / 2, p.get_y() + p.get_height() / 2), 
                        xytext=(0, 0),
                        textcoords='offset points', 
                        ha='center', 
                        va='center', 
                        fontsize=7, 
                        color='white')   
                
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        canvas = FigureCanvasTkAgg(fig, master=self) 
        canvas.draw()
        canvas_width = int(fig.bbox.bounds[2])
        canvas_height = int(fig.bbox.bounds[3])

        canvas.get_tk_widget().config(width=canvas_width, height=canvas_height)
        canvas.get_tk_widget().place(x=295, y=268)

    def create_rota_cidade_chart(self):
        df_rota_cidade = self.prepare_rota_cidade_data()
        self.place_rota_cidade_chart(df_rota_cidade)

    def create_carros_agregado_chart(self):
        # Carrega os dados para o gráfico de status
        df_agregado = self.prepare_carros_agregado_data()
        # Cria o gráfico de status
        self.place_carros_agregado_chart(df_agregado)

    def prepare_carros_agregado_data(self):
        df = self.db.buscar_carros_por_agregado()
        return df

    def place_carros_agregado_chart(self, agregado_counts):
        style.use('seaborn-v0_8-dark')
        
        fig = Figure(figsize=(2.26, 2.23), facecolor="#D9D9D9", tight_layout=False)
        ax = fig.add_subplot()
        
        colors = list(sns.color_palette("crest",3))

        pie_wedges = ax.pie(agregado_counts['Quantidade'],
                            labels=agregado_counts['Agregado'],
                            autopct=autopct_format(agregado_counts['Quantidade']),
                            startangle=90,
                            colors=colors)

        for wedge, text in zip(pie_wedges[0], pie_wedges[2]):
            text.set_color('black')
            text.set_fontsize(8)
            text.set_bbox(dict(facecolor='white', alpha=0.5, edgecolor='none'))
    
        centre_circle = plt.Circle((0,0),0.50,fc='#D9D9D9')
        fig.gca().add_artist(centre_circle)

        # Iguala o aspecto ratio para que o 'pie' seja desenhado como um círculo.
        ax.axis('equal')
  
        # Ajusta o subplot para que o gráfico de pizza preencha melhor o espaço disponível
        ax.set_position([0.01, 0.01, 0.99, 0.99])
        
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().place(x=35, y=268)
    
    def create_status_chart(self):
        # Carrega os dados para o gráfico de status
        df_status = self.prepare_status_data()
        # Cria o gráfico de status
        self.place_status_chart(df_status)

    def prepare_status_data(self):
        df_status = self.db.buscar_entregas_por_status()
        return df_status

    def place_status_chart(self, status_counts):
        # style.use('seaborn-v0_8-dark')
        fig = Figure(figsize=(2.2, 2.2) , facecolor="#D9D9D9" , tight_layout=False )
        ax = fig.add_subplot()

        colors = list(reversed(sns.color_palette("crest", len(status_counts))))
        
        bars = ax.bar(status_counts['STATUS'], status_counts['Quantidade'], color=colors)

       # Adiciona rótulos de dados em cada barra
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, yval/1.5, int(yval), verticalalignment='top', ha='center', fontsize=7, color='white' , zorder=4)
            
        # Removendo bordas da área de plotagem
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(True)
        ax.spines['bottom'].set_color('white')
        ax.spines['bottom'].set_linewidth(0.5)  

        # Removendo o rótulo do eixo Y
        ax.yaxis.set_visible(False)
        
        ax.set_facecolor("#D9D9D9")

        # ax.set_title('Quantidade por STATUS')
        ax.set_xlabel('Status' , fontsize=7 , color='#333333')
        ax.xaxis.set_visible(False)
    
        # Esconder os nomes dos status no eixo X
        ax.tick_params(axis='x', which='both', length=0)  # Remover os ticks do eixo X
        ax.set_xticks([])  # Remover os rótulos do eixo X

        # Colocando os nomes das cidades dentro das barras
        for bar, label in zip(bars, status_counts['STATUS']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05*max(status_counts['Quantidade']), label, 
            ha='center', va='bottom', rotation=90, fontsize=7, color='#333333', zorder=3)

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().place(x=815, y=268)

    def prepare_carros_tipo_data(self):
        # Busca os dados usando a função da classe DatabaseManager
        rows = self.db.buscar_carros_por_tipo()
        # Cria um DataFrame com os resultados
        df = pd.DataFrame(rows, columns=['TipoCarro', 'Quantidade'])
        # Retorna o DataFrame
        return df

    def place_carros_tipo_chart(self, df_tipo):
        # Gera o gráfico TreeMap
        fig, ax = plt.subplots(figsize=(2.2, 2.18))
        fig.patch.set_facecolor('#D9D9D9')
        ax.set_facecolor('#D9D9D9')
        
         # Calcula a soma total de todas as categorias
        total = df_tipo['Quantidade'].sum()
        
        labels = ["{}\n{}\n({:.0f}%)".format(tipo, valor, (valor / total * 100)) for tipo, 
                  valor in zip(df_tipo['TipoCarro'], df_tipo['Quantidade'])]
        
        # Definir o tamanho da fonte
        font_size = 8  # Ajuste este valor conforme necessário para se adequar ao seu design
        text_kwargs = dict(color="white", fontsize=font_size)
        
        palette = list(reversed(sns.color_palette("crest",7)))
        
        # A função squarify.plot() irá criar o gráfico TreeMap
        squarify.plot(sizes=df_tipo['Quantidade'],  label=labels , alpha=0.8,
                      color=palette,
                      text_kwargs=text_kwargs,linewidth=0.5, edgecolor='white')
        plt.axis('off')  # Desativa os eixos

        ax.set_position([0.05, 0.05, 0.9, 0.9]) 
        
        # Adiciona o gráfico ao Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self)  # Use o nome correto do seu master/frame
        canvas.draw()
        canvas.get_tk_widget().place(x=35, y=548)

    def create_carros_tipo_chart(self):
        # Busca e prepara os dados
        df_tipo = self.prepare_carros_tipo_data()
        # Cria e coloca o gráfico
        self.place_carros_tipo_chart(df_tipo)

    def prepare_rota_distancia_data(self):
        rows = self.db.buscar_rotas_por_distancia()
        df = pd.DataFrame(rows, columns=['DistanciaKM', 'Quantidade'])
        return df

    def place_rota_distancia_chart(self, df_distancia):
        fig = Figure(figsize=(2.2, 2.18), tight_layout=True)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor('#D9D9D9')
        ax.set_facecolor('#D9D9D9')

        ax.hist(df_distancia['DistanciaKM'], bins=17, weights=df_distancia['Quantidade'], rwidth=0.7 , color='#2C7E8C')
        ax.set_xlabel('Distância em KM', fontsize=7)
        ax.set_ylabel('Quantidade', fontsize=7)
        ax.tick_params(axis='both', which='major', labelsize=7)

        ax.set_position([0.05, 0.05, 0.9, 0.9]) 

        canvas = FigureCanvasTkAgg(fig, master=self) 
        canvas.draw()
        canvas.get_tk_widget().place(x=298, y=548)
   
    def create_rota_distancia_chart(self):
        df_distancia = self.prepare_rota_distancia_data()
        self.place_rota_distancia_chart(df_distancia)

    def prepare_top_cidades_entrega_data(self):
        # A query foi ajustada para buscar apenas o Top 10
        rows = self.db.buscar_top_cidades_entrega()
        # Transforma os dados em um DataFrame e ordena para garantir o Top 10
        df = pd.DataFrame(rows, columns=['CidadeEntrega', 'Quantidade']).head(10)
        return df

    def place_top_cidades_entrega_chart(self, df_top_cidades):
        fig = Figure(figsize=(2.29, 2.18), dpi=100 , tight_layout=False)
        fig.patch.set_facecolor('#D9D9D9')
        ax = fig.add_subplot(111,facecolor='#D9D9D9' , frameon=False)
        
        palette = list(reversed(sns.color_palette("crest", len(df_top_cidades))))
        
        sns.barplot(x='Quantidade', y='CidadeEntrega', data=df_top_cidades, ax=ax, palette=palette)
        
        ax.set_yticklabels(ax.get_yticklabels(), fontsize=7 , color='#333232')
        
        ax.set_title('')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        sns.despine(left=True, bottom=True)
        for p in ax.patches:
            ax.annotate(f"{int(p.get_width())}", 
                        (p.get_width(), p.get_y() + p.get_height() / 2), 
                        xytext=(6, -0.5), 
                        textcoords='offset points', 
                        ha='center', 
                        va='center', 
                        fontsize=9, 
                        color='#333232')
            
        for i, p in enumerate(ax.patches):
            width = p.get_width()
            ax.annotate(f"{df_top_cidades['CidadeEntrega'][i]}", 
                        (width / 2, p.get_y() + p.get_height() / 2), 
                        xytext=(0, 0),
                        textcoords='offset points', 
                        ha='center', 
                        va='center', 
                        fontsize=7, 
                        color='white')   
                
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        canvas = FigureCanvasTkAgg(fig, master=self) 
        canvas.draw()
        canvas_width = int(fig.bbox.bounds[2])
        canvas_height = int(fig.bbox.bounds[3])

        canvas.get_tk_widget().config(width=canvas_width, height=canvas_height)
        canvas.get_tk_widget().place(x=559, y=548)  

    def create_top_cidades_entrega_chart(self):
        df_top_cidades = self.prepare_top_cidades_entrega_data()
        self.place_top_cidades_entrega_chart(df_top_cidades)

    def prepare_info_cards_data(self):
        info_data = self.db.buscar_informacoes_cards()
        return info_data

    def place_info_cards(self, card_data):
        # Definições de estilo para o cartão
        title_fontsize = 10
        value_fontsize = 13

        # Cores e tamanhos dos cartões
        card_color = '#D9D9D9'
        card_width = 2.18
        card_height = 0.7  # Divida a altura total por 3
        x_position = 830
        y_positions = {
            'total_distance': 548,
            'total_freight_cost': 548 + card_height * 100 + 2,  # Adiciona a altura do cartão mais o espaçamento
            'total_value_cargo': 548 + (card_height * 100 + 2) * 2  # Adiciona a altura de dois cartões mais o espaçamento
        }

        # Para cada dado, crie um cartão e adicione ao layout do Tkinter
        for key, value in card_data.items():
            fig, ax = plt.subplots(figsize=(card_width, card_height))
            ax.axis('off')

            # Aplica formatação customizada baseada na chave
            if key == 'total_value_cargo':
                title = "Valor Total Transportado"
                formatted_value = self.formatar_valor_monetario(value)
            elif key == 'total_freight_cost':
                title = "Frete Total das Viagens"
                formatted_value = self.formatar_valor_monetario(value)
            elif key == 'total_distance':
                title = "Distância das Viagens (Km)"
                formatted_value = self.formatar_distancia(value)

            ax.text(0.5, 0.95, title, fontsize=title_fontsize, ha='center')
            ax.text(0.5, 0.25, formatted_value, fontsize=value_fontsize, weight='bold', ha='center')

            fig.patch.set_facecolor(card_color)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self)
            canvas.draw()
            canvas.get_tk_widget().place(x=x_position, y=y_positions[key])

    def create_info_cards(self):
        card_data = self.prepare_info_cards_data()
        self.place_info_cards(card_data)

    def place_info_card(self, value, x_pos, y_pos):
        fig, ax = plt.subplots(figsize=(1, 0.54))  # Dimensões para um único card
        ax.axis('off')

        formatted_value = f"{value}"  # A formatação vai depender do tipo de dado
        ax.text(0.5, 0.3, formatted_value, fontsize=22, weight='bold', ha='center',color="#333333")

        fig.patch.set_facecolor('#D9D9D9')
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().place(x=x_pos, y=y_pos)

    def create_cards(self):
        total_carros = self.db.contar_carros()
        total_rotas = self.db.contar_rotas()
        total_filiais = self.db.contar_filiais()
        total_entregas = self.db.contar_entregas()

        self.place_info_card(total_carros, x_pos=71, y_pos=130)  # Atualize os valores x_pos e y_pos conforme necessário
        self.place_info_card(total_rotas, x_pos=343, y_pos=130)
        self.place_info_card(total_filiais, x_pos=613, y_pos=130)
        self.place_info_card(total_entregas, x_pos=882, y_pos=130)
    
class TelaPrincipal:
    def __init__(self, master, usuario_logado ,user_id=None ):
        self.master = master

        self.usuario_logado = usuario_logado
        self.user_id = user_id
        self.master.title("TMSLite")
        self.master.geometry('800x600')  # Tamanho maior para a tela principal
        centralizar_janela_login(self.master, 800, 600)
        master.iconbitmap(icon_path)
        self.master.resizable(False, False)
        
        background_image_path = 'assets/image_32.png'

        self.background_image = PhotoImage(file=background_image_path)

        # Cria um label e coloca a imagem de fundo nele
        self.background_label = ttk.Label(self.master, image=self.background_image)
        self.background_label.place(x=-0.98, y=0, relwidth=1.02, relheight=1)
        
        # Aplica tema escuro e configura estilos, semelhante à tela de login
        self.master.configure(background='#D9D9D9')
        style = ttk.Style(self.master)
        style.theme_use('clam') 

        # Definição de cores e estilos
        cor_fundo = '#333333'
        cor_frente = '#ffffff'
        cor_entrada = '#555555'
        cor_botao = '#0078D7'
        cor_botao_frente = '#ffffff'

        style.configure('TFrame', background=cor_fundo)
        style.configure('TLabel', background=cor_fundo, foreground=cor_frente, font=('Arial', 10))
        style.configure('TEntry', fieldbackground=cor_entrada, foreground=cor_frente, borderwidth=1)
        style.configure('TButton', background=cor_botao, foreground=cor_botao_frente, font=('Arial', 10), borderwidth=1)
        style.map('TButton', background=[('active', cor_botao)], foreground=[('active', cor_botao_frente)])
        
        centralizar_janela_login(self.master, 900, 600)
        # self.mostrar_boas_vindas()       
        self.configurar_menu()

    def on_close(self):
        if messagebox.askokcancel("Sair", "Deseja sair da aplicação?"):
            # self.db.close_connection()  # Presumindo que você tenha um método para fechar a conexão
            self.master.destroy()  # Encerra o loop principal do Tkinter e todas as janelas
            exit()  # Encerra completamente o aplicativo
    
    def run(self):
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.deiconify()  # Mostra a janela principal
        self.master.mainloop()        

    def configurar_menu(self):
        # Cria uma barra de menu
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # Adiciona menu 'Cadastro'
        menu_cadastro = tk.Menu(self.menubar, tearoff=0)
        menu_cadastro.add_command(label="Cadastro de Carro", command=self.cadastro_carro)
        menu_cadastro.add_command(label="Cadastro de Filial", command=self.cadastro_filial)
        menu_cadastro.add_command(label="Cadastro de Frete", command=self.cadastro_frete)
        self.menubar.add_cascade(label="Cadastro", menu=menu_cadastro)

        # Adiciona menu 'Gestão de Entrega'
        menu_gestao_entrega = tk.Menu(self.menubar, tearoff=0)
        menu_gestao_entrega.add_command(label="Cadastro de Solicitação de Entrega", command=self.cadastro_solicitacao_entrega)
        menu_gestao_entrega.add_command(label="Atualização de Status de Entrega", command=self.gereciamento_entrega)
        self.menubar.add_cascade(label="Gestão de Entrega", menu=menu_gestao_entrega)

        # Adiciona menu 'Painel'
        menu_painel = tk.Menu(self.menubar, tearoff=0)
        menu_painel.add_command(label="Painel de Controle", command=self.abrir_dashboard)
        self.menubar.add_cascade(label="Dashboard", menu=menu_painel)

    def mostrar_boas_vindas(self):
        # Define uma fonte maior para a saudação
        fonte_boas_vindas = ('Arial', 30, 'bold')

        boas_vindas = ttk.Label(self.master, text=f'Bem-vindo(a), {self.usuario_logado}!', font=fonte_boas_vindas, background='#333333', foreground='#ffffff')

        # Centraliza o texto de saudação
        boas_vindas.pack(pady=10, expand=True)

    def atualizar_treeview(self):
        self.cadastro_carro.atualizar()    
        
    def cadastro_carro(self):
        self.cadastro_carro = CadastroCarro(self.master, self.atualizar_treeview)  # Passa o callback
        self.cadastro_carro.transient(self.master)
        self.cadastro_carro.grab_set()
            
    def cadastro_filial(self):
        janela_cadastro_filial = CadastroFilial(self.master)  
        janela_cadastro_filial.transient(self.master)  
        janela_cadastro_filial.grab_set()  

    def cadastro_frete(self):
        janela_cadastro_frete = CadastroFrete(self.master, atualizar_callback=None)  # Passa None ou uma função de callback adequada
        janela_cadastro_frete.transient(self.master)  
        janela_cadastro_frete.grab_set()

    def cadastro_solicitacao_entrega(self):
        cadastro_solicitacao_entrega = CadastroSolicitacaoEntrega(self.master, self.usuario_logado , self.user_id)
        cadastro_solicitacao_entrega.transient(self.master)  
        cadastro_solicitacao_entrega.grab_set()

    def gereciamento_entrega(self):
        gereciamento_entrega = GerenciamentoEntregas(self.master)
        gereciamento_entrega.transient(self.master)  
        gereciamento_entrega.grab_set()

    def abrir_dashboard(self):
        dashboard = Dashboard(self.master)
        dashboard.transient(self.master)  
        dashboard.grab_set()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginScreen(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
    
    
    #Aplicação desenvolvida por Alfredo Gonçalves de Souza Santos.
    