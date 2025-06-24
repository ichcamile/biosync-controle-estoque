import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

class ControleEstoqueApp:
    def __init__(self, master):
        self.master = master
        master.title("BioSync - Controle de Estoque")
        master.geometry("800x600")

        self.conn = None
        self._init_db()

        self.current_user_id = None
        self.current_user_role = None
        self.create_login_ui()

    def _get_db_connection(self):
        self.conn = sqlite3.connect('estoque_biosync.db')
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def _init_db(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                current_quantity INTEGER NOT NULL DEFAULT 0,
                min_quantity INTEGER NOT NULL DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                movement_date TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] == 0:
                admin_username = "admin"
                admin_password = "adminpass"
                hashed_password = generate_password_hash(admin_password)

                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (admin_username, hashed_password, 'admin')
                )
                conn.commit()
                print("Usuário administrador padrão criado (admin/adminpass).")
            else:
                print("Usuário administrador já existe.")
        except Exception as e:
            print(f"Erro ao garantir usuário admin: {e}")

        conn.commit()
        conn.close()

    def _execute_query(self, query, params=()):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            results = cursor.fetchall() if query.strip().lower().startswith(('select', 'pragma')) else None
            return results
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Erro de integridade: {e}")
        except Exception as e:
            raise Exception(f"Erro ao executar query: {e}")
        finally:
            if conn:
                conn.close()

    def _authenticate_user(self, username, password):
        user = self._execute_query("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
        if user:
            if check_password_hash(user[0]['password'], password):
                return user[0]['id'], user[0]['role']
        return None, None

    def _register_user(self, username, password, role):
        if not username or not password:
            return False, "Nome de usuário e senha são obrigatórios."

        hashed_password = generate_password_hash(password)
        try:
            self._execute_query(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, role)
            )
            return True, "Usuário registrado com sucesso."
        except ValueError as e:
            if "UNIQUE constraint failed" in str(e):
                return False, "Nome de usuário já existe."
            return False, f"Erro: {e}"
        except Exception as e:
            return False, f"Erro inesperado: {e}"

    def _add_product(self, name, description, min_quantity):
        if not name:
            return False, "Nome do produto é obrigatório."
        try:
            min_quantity = int(min_quantity)
            if min_quantity < 0:
                return False, "Quantidade mínima não pode ser negativa."
        except ValueError:
            return False, "Quantidade mínima deve ser um número inteiro."

        try:
            self._execute_query(
                "INSERT INTO products (name, description, min_quantity) VALUES (?, ?, ?)",
                (name, description, min_quantity)
            )
            return True, "Produto adicionado com sucesso."
        except ValueError as e:
            if "UNIQUE constraint failed" in str(e):
                return False, "Já existe um produto com este nome."
            return False, f"Erro: {e}"
        except Exception as e:
            return False, f"Erro inesperado: {e}"

    def _get_all_products(self):
        return self._execute_query("SELECT id, name, description, current_quantity, min_quantity FROM products")

    def _update_product(self, product_id, name, description, min_quantity):
        if not name:
            return False, "Nome do produto é obrigatório."
        try:
            min_quantity = int(min_quantity)
            if min_quantity < 0:
                return False, "Quantidade mínima não pode ser negativa."
        except ValueError:
            return False, "Quantidade mínima deve ser um número inteiro."

        try:
            self._execute_query(
                "UPDATE products SET name = ?, description = ?, min_quantity = ? WHERE id = ?",
                (name, description, min_quantity, product_id)
            )
            return True, "Produto atualizado com sucesso."
        except ValueError as e:
            if "UNIQUE constraint failed" in str(e):
                return False, "Já existe outro produto com este nome."
            return False, f"Erro: {e}"
        except Exception as e:
            return False, f"Erro inesperado: {e}"

    def _add_stock(self, product_id, quantity):
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return False, "Quantidade de entrada deve ser um número inteiro positivo."
        except ValueError:
            return False, "Quantidade deve ser um número inteiro."

        try:
            product = self._execute_query("SELECT current_quantity FROM products WHERE id = ?", (product_id,))
            if not product:
                return False, "Produto não encontrado."

            current_quantity = product[0]['current_quantity']
            new_quantity = current_quantity + quantity

            self._execute_query("UPDATE products SET current_quantity = ? WHERE id = ?", (new_quantity, product_id))
            self._execute_query(
                "INSERT INTO stock_movements (product_id, type, quantity, movement_date) VALUES (?, ?, ?, ?)",
                (product_id, 'entrada', quantity, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            return True, "Entrada de estoque registrada com sucesso."
        except Exception as e:
            return False, f"Erro ao adicionar estoque: {e}"

    def _remove_stock(self, product_id, quantity):
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return False, "Quantidade de saída deve ser um número inteiro positivo."
        except ValueError:
            return False, "Quantidade deve ser um número inteiro."

        try:
            product = self._execute_query("SELECT current_quantity FROM products WHERE id = ?", (product_id,))
            if not product:
                return False, "Produto não encontrado."

            current_quantity = product[0]['current_quantity']
            if current_quantity < quantity:
                return False, "Quantidade insuficiente em estoque."

            new_quantity = current_quantity - quantity

            self._execute_query("UPDATE products SET current_quantity = ? WHERE id = ?", (new_quantity, product_id))
            self._execute_query(
                "INSERT INTO stock_movements (product_id, type, quantity, movement_date) VALUES (?, ?, ?, ?)",
                (product_id, 'saida', quantity, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            return True, "Saída de estoque registrada com sucesso."
        except Exception as e:
            return False, f"Erro ao remover estoque: {e}"

    def _get_low_stock_products(self):
        return self._execute_query("SELECT id, name, current_quantity, min_quantity FROM products WHERE current_quantity <= min_quantity AND min_quantity > 0")

    def create_login_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.login_frame = ttk.Frame(self.master, padding="20")
        self.login_frame.pack(expand=True)

        ttk.Label(self.login_frame, text="Login", font=("Arial", 24)).pack(pady=20)

        ttk.Label(self.login_frame, text="Usuário:").pack(pady=5)
        self.username_entry = ttk.Entry(self.login_frame, width=30)
        self.username_entry.pack(pady=5)

        ttk.Label(self.login_frame, text="Senha:").pack(pady=5)
        self.password_entry = ttk.Entry(self.login_frame, width=30, show="*")
        self.password_entry.pack(pady=5)

        ttk.Button(self.login_frame, text="Entrar", command=self.perform_login).pack(pady=10)

        ttk.Label(self.login_frame, text="Admin Padrão: admin / adminpass").pack(pady=5)

    def perform_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        user_id, user_role = self._authenticate_user(username, password)

        if user_id and user_role:
            self.current_user_id = user_id
            self.current_user_role = user_role
            messagebox.showinfo("Sucesso", f"Bem-vindo, {username} ({user_role})!")
            self.create_main_app_ui()
        else:
            messagebox.showerror("Erro de Login", "Usuário ou senha inválidos.")

    def create_main_app_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        product_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(product_tab, text="Gerenciar Produtos")
        self.create_product_tab_content(product_tab)

        stock_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(stock_tab, text="Movimentar Estoque")
        self.create_stock_tab_content(stock_tab)

        if self.current_user_role == 'admin':
            user_management_tab = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(user_management_tab, text="Gerenciar Usuários")
            self.create_user_management_tab_content(user_management_tab)

        self.logout_button = ttk.Button(self.master, text="Logout", command=self.perform_logout)
        self.logout_button.place(relx=0.98, rely=0.02, anchor='ne')

        self.update_low_stock_display()

    def perform_logout(self):
        self.current_user_id = None
        self.current_user_role = None
        messagebox.showinfo("Logout", "Você foi desconectado.")
        self.create_login_ui()

    def create_product_tab_content(self, parent_frame):
        product_frame = ttk.LabelFrame(parent_frame, text="Cadastro/Edição de Produtos", padding="10")
        product_frame.pack(side="top", fill="x", padx=5, pady=5)

        ttk.Label(product_frame, text="Nome:").grid(row=0, column=0, sticky='w', pady=2)
        self.product_name_entry = ttk.Entry(product_frame, width=40)
        self.product_name_entry.grid(row=0, column=1, pady=2)

        ttk.Label(product_frame, text="Descrição:").grid(row=1, column=0, sticky='w', pady=2)
        self.product_desc_entry = ttk.Entry(product_frame, width=40)
        self.product_desc_entry.grid(row=1, column=1, pady=2)

        ttk.Label(product_frame, text="Qtd. Mínima:").grid(row=2, column=0, sticky='w', pady=2)
        self.product_min_qty_entry = ttk.Entry(product_frame, width=10)
        self.product_min_qty_entry.grid(row=2, column=1, sticky='w', pady=2)

        button_frame_product = ttk.Frame(product_frame)
        button_frame_product.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame_product, text="Adicionar Produto", command=self.add_product_ui).pack(side='left', padx=5)
        ttk.Button(button_frame_product, text="Atualizar Produto", command=self.update_product_ui).pack(side='left', padx=5)
        ttk.Button(button_frame_product, text="Limpar Campos", command=self._clear_product_form).pack(side='left', padx=5)

        tree_view_frame = ttk.Frame(parent_frame)
        tree_view_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        self.product_tree = ttk.Treeview(tree_view_frame, columns=("ID", "Nome", "Descrição", "Atual", "Mínimo"), show="headings")
        self.product_tree.heading("ID", text="ID")
        self.product_tree.heading("Nome", text="Nome")
        self.product_tree.heading("Descrição", text="Descrição")
        self.product_tree.heading("Atual", text="Qtd. Atual")
        self.product_tree.heading("Mínimo", text="Qtd. Mínima")

        self.product_tree.column("ID", width=50, anchor='center')
        self.product_tree.column("Nome", width=150)
        self.product_tree.column("Descrição", width=200)
        self.product_tree.column("Atual", width=80, anchor='center')
        self.product_tree.column("Mínimo", width=80, anchor='center')

        yscrollbar = ttk.Scrollbar(tree_view_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=yscrollbar.set)
        yscrollbar.pack(side="right", fill="y")
        self.product_tree.pack(side="left", fill="both", expand=True)
        self.product_tree.bind("<<TreeviewSelect>>", self._on_product_select)

        self.load_products_to_tree()

    def create_stock_tab_content(self, parent_frame):
        stock_frame = ttk.LabelFrame(parent_frame, text="Movimentação de Estoque", padding="10")
        stock_frame.pack(side="top", fill="x", padx=5, pady=5)

        ttk.Label(stock_frame, text="Produto Selecionado:").grid(row=0, column=0, sticky='w', pady=2)
        self.selected_product_label = ttk.Label(stock_frame, text="Nenhum")
        self.selected_product_label.grid(row=0, column=1, sticky='w', pady=2)

        ttk.Label(stock_frame, text="Quantidade:").grid(row=1, column=0, sticky='w', pady=2)
        self.stock_quantity_entry = ttk.Entry(stock_frame, width=20)
        self.stock_quantity_entry.grid(row=1, column=1, sticky='w', pady=2)

        button_frame_stock = ttk.Frame(stock_frame)
        button_frame_stock.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame_stock, text="Registrar Entrada", command=self.add_stock_ui).pack(side='left', padx=5)
        ttk.Button(button_frame_stock, text="Registrar Saída", command=self.remove_stock_ui).pack(side='left', padx=5)

        self.low_stock_label = ttk.Label(parent_frame, text="", foreground='red', wraplength=750, font=("Arial", 10, "bold"))
        self.low_stock_label.pack(side="bottom", fill="x", padx=10, pady=5)

    def create_user_management_tab_content(self, parent_frame):
        user_frame = ttk.LabelFrame(parent_frame, text="Cadastrar Novo Usuário", padding="10")
        user_frame.pack(side="top", fill="x", padx=5, pady=5)

        ttk.Label(user_frame, text="Usuário:").grid(row=0, column=0, sticky='w', pady=2)
        self.new_username_entry = ttk.Entry(user_frame, width=30)
        self.new_username_entry.grid(row=0, column=1, pady=2)

        ttk.Label(user_frame, text="Senha:").grid(row=1, column=0, sticky='w', pady=2)
        self.new_password_entry = ttk.Entry(user_frame, width=30, show="*")
        self.new_password_entry.grid(row=1, column=1, pady=2)

        ttk.Label(user_frame, text="Perfil:").grid(row=2, column=0, sticky='w', pady=2)
        self.new_user_role_var = tk.StringVar(value="comum")
        self.new_user_role_dropdown = ttk.OptionMenu(user_frame, self.new_user_role_var, "comum", "admin", "comum")
        self.new_user_role_dropdown.grid(row=2, column=1, sticky='w', pady=2)

        ttk.Button(user_frame, text="Registrar Usuário", command=self.register_user_ui).grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Label(parent_frame, text="Usuários Registrados:", font=("Arial", 10, "bold")).pack(pady=10)
        self.user_tree = ttk.Treeview(parent_frame, columns=("ID", "Usuário", "Perfil"), show="headings")
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("Usuário", text="Usuário")
        self.user_tree.heading("Perfil", text="Perfil")
        self.user_tree.column("ID", width=50, anchor='center')
        self.user_tree.column("Usuário", width=150)
        self.user_tree.column("Perfil", width=100)
        self.user_tree.pack(fill="both", expand=True)

        self.load_users_to_tree()

    def register_user_ui(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        role = self.new_user_role_var.get()

        success, message = self._register_user(username, password, role)
        if success:
            messagebox.showinfo("Sucesso", message)
            self.new_username_entry.delete(0, tk.END)
            self.new_password_entry.delete(0, tk.END)
            self.new_user_role_var.set("comum")
            self.load_users_to_tree()
        else:
            messagebox.showerror("Erro", message)

    def load_users_to_tree(self):
        if not self.current_user_role == 'admin':
            return

        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        conn = self._get_db_connection()
        cursor = conn.cursor()
        users = cursor.execute("SELECT id, username, role FROM users").fetchall()
        conn.close()

        for u in users:
            self.user_tree.insert("", "end", values=(u['id'], u['username'], u['role']))

    def _clear_product_form(self):
        self.product_name_entry.delete(0, tk.END)
        self.product_desc_entry.delete(0, tk.END)
        self.product_min_qty_entry.delete(0, tk.END)
        self.selected_product_id = None
        self.selected_product_label.config(text="Nenhum")

    def _on_product_select(self, event):
        selected_item = self.product_tree.focus()
        if selected_item:
            values = self.product_tree.item(selected_item, 'values')
            self.selected_product_id = int(values[0])

            self.product_name_entry.delete(0, tk.END)
            self.product_name_entry.insert(0, values[1])
            self.product_desc_entry.delete(0, tk.END)
            self.product_desc_entry.insert(0, values[2])
            self.product_min_qty_entry.delete(0, tk.END)
            self.product_min_qty_entry.insert(0, values[4])

            self.selected_product_label.config(text=f"{values[1]} (ID: {values[0]})")

    def load_products_to_tree(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        products = self._get_all_products()
        for p in products:
            tags = ()
            if p['current_quantity'] <= p['min_quantity'] and p['min_quantity'] > 0:
                tags = ('low_stock',)
            self.product_tree.insert("", "end", values=(p['id'], p['name'], p['description'], p['current_quantity'], p['min_quantity']), tags=tags)

        self.product_tree.tag_configure('low_stock', background='red', foreground='white')

    def add_product_ui(self):
        name = self.product_name_entry.get()
        description = self.product_desc_entry.get()
        min_qty_str = self.product_min_qty_entry.get()

        success, message = self._add_product(name, description, min_qty_str)
        if success:
            messagebox.showinfo("Sucesso", message)
            self.load_products_to_tree()
            self.update_low_stock_display()
            self._clear_product_form()
        else:
            messagebox.showerror("Erro", message)

    def update_product_ui(self):
        if not hasattr(self, 'selected_product_id') or not self.selected_product_id:
            messagebox.showerror("Erro", "Selecione um produto na lista para atualizar.")
            return

        name = self.product_name_entry.get()
        description = self.product_desc_entry.get()
        min_qty_str = self.product_min_qty_entry.get()

        success, message = self._update_product(self.selected_product_id, name, description, min_qty_str)
        if success:
            messagebox.showinfo("Sucesso", message)
            self.load_products_to_tree()
            self.update_low_stock_display()
            self._clear_product_form()
        else:
            messagebox.showerror("Erro", message)

    def add_stock_ui(self):
        if not hasattr(self, 'selected_product_id') or not self.selected_product_id:
            messagebox.showerror("Erro", "Selecione um produto na lista para movimentar o estoque.")
            return

        qty_str = self.stock_quantity_entry.get()
        success, message = self._add_stock(self.selected_product_id, qty_str)
        if success:
            messagebox.showinfo("Sucesso", message)
            self.load_products_to_tree()
            self.update_low_stock_display()
            self.stock_quantity_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", message)

    def remove_stock_ui(self):
        if not hasattr(self, 'selected_product_id') or not self.selected_product_id:
            messagebox.showerror("Erro", "Selecione um produto na lista para movimentar o estoque.")
            return

        qty_str = self.stock_quantity_entry.get()
        success, message = self._remove_stock(self.selected_product_id, qty_str)
        if success:
            messagebox.showinfo("Sucesso", message)
            self.load_products_to_tree()
            self.update_low_stock_display()
            self.stock_quantity_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", message)

    def update_low_stock_display(self):
        low_stock_products = self._get_low_stock_products()
        if low_stock_products:
            alert_text = "ALERTA DE ESTOQUE BAIXO: \n"
            for p in low_stock_products:
                alert_text += f"- {p['name']} (Atual: {p['current_quantity']}, Mínimo: {p['min_quantity']})\n"
            self.low_stock_label.config(text=alert_text)
        else:
            self.low_stock_label.config(text="Todos os produtos estão em nível de estoque adequado.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ControleEstoqueApp(root)
    root.mainloop()