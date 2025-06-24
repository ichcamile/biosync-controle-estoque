# BioSync - Sistema de Controle de Estoque 📊

## Visão Geral

O BioSync é um sistema de controle de estoque simples e eficiente, desenvolvido em Python usando a biblioteca `tkinter` para a interface gráfica e `sqlite3` para o banco de dados. Ele permite o gerenciamento de produtos, registro de movimentações de estoque (entrada e saída) e o controle de usuários com diferentes níveis de acesso (administrador e comum).

-----

## Funcionalidades ✨

  * **Autenticação de Usuários:** Sistema de login com diferentes perfis de acesso. 🔑
  * **Gerenciamento de Produtos:**
      * Adição de novos produtos com nome, descrição e quantidade mínima. ➕
      * Atualização de informações de produtos existentes. 🔄
      * Visualização de todos os produtos em uma tabela interativa. 👀
  * **Movimentação de Estoque:**
      * Registro de entradas de produtos no estoque. 📦➡️
      * Registro de saídas de produtos do estoque. 📦⬅️
  * **Alertas de Estoque Baixo:** Exibição de produtos que estão abaixo da quantidade mínima configurada. 🚨
  * **Gerenciamento de Usuários (Apenas Admin):**
      * Criação de novos usuários com perfis 'admin' ou 'comum'. 🧑‍💻
      * Visualização da lista de usuários registrados. 📋

-----

## Requisitos 💻

  * **Python 3.x**
  * **Bibliotecas Python:**
      * `tkinter` (geralmente incluída com a instalação do Python)
      * `sqlite3` (geralmente incluída com a instalação do Python)
      * `werkzeug` (para criptografia de senhas)

-----

## Instalação ⚙️

1.  **Clone o repositório (ou baixe o arquivo `main.py`):**

    ```bash
    git clone https://github.com/seu-usuario/biosync-estoque.git
    cd biosync-estoque
    ```

2.  **Instale a dependência necessária:**

    ```bash
    pip install Werkzeug
    ```

-----

## Como Rodar ▶️

Execute o arquivo `main.py`:

```bash
python main.py
```

-----

## Uso 🧑‍💻

### Tela de Login

Ao iniciar o aplicativo, você será direcionado para a tela de login.

  * **Usuário Administrador Padrão:**
      * **Usuário:** `admin`
      * **Senha:** `adminpass`

### Interface Principal

Após o login bem-sucedido, a interface principal será carregada, contendo as seguintes abas:

  * **Gerenciar Produtos:** Adicione, edite e visualize seus produtos. 📝
  * **Movimentar Estoque:** Registre entradas e saídas de estoque para os produtos selecionados. 📊
  * **Gerenciar Usuários (Apenas para Admin):** Crie novos usuários e veja a lista de usuários existentes. 🛡️

### Alertas de Estoque Baixo

Na aba "Movimentar Estoque", você verá um alerta em destaque caso algum produto esteja com a quantidade atual menor ou igual à sua quantidade mínima definida. Produtos com estoque baixo também serão destacados em **vermelho** na tabela da aba "Gerenciar Produtos". 🔴

-----

## Estrutura do Banco de Dados 🗄️

O sistema utiliza um banco de dados SQLite (`estoque_biosync.db`) com as seguintes tabelas:

  * `products`: Armazena informações sobre os produtos (nome, descrição, quantidade atual, quantidade mínima). 🏷️
  * `stock_movements`: Registra todas as movimentações de estoque (produto, tipo, quantidade, data). 📈
  * `users`: Armazena os dados de login dos usuários (username, senha criptografada, perfil). 👤

-----

## Desenvolvimento 🛠️

O código é estruturado em uma classe `ControleEstoqueApp`, que encapsula a lógica de banco de dados e a interface gráfica.

  * **Métodos de Banco de Dados (`_get_db_connection`, `_init_db`, `_execute_query`):** Lidam com a conexão e operações no SQLite. 🔗
  * **Métodos de Autenticação e Usuário (`_authenticate_user`, `_register_user`):** Gerenciam o login e o registro de novos usuários. 🔐
  * **Métodos de Produto (`_add_product`, `_get_all_products`, `_update_product`):** Operações CRUD para produtos. 🛒
  * **Métodos de Estoque (`_add_stock`, `_remove_stock`, `_get_low_stock_products`):** Lógica para movimentação e alertas de estoque. 📦
  * **Métodos de UI (`create_login_ui`, `create_main_app_ui`, `create_product_tab_content`, etc.):** Responsáveis pela construção e interação da interface gráfica. 🖥️

