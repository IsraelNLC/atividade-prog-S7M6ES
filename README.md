# Documentação da API - Histórias Interativas

A API em questão é um sistema de Geração e Gerenciamento de Histórias Interativas, desenvolvido utilizando o framework FastAPI.

## Instalação 
1. Clone o repositório:
   ```cmd
    git clone https://github.com/seu-usuario/seu-repositorio.git
    cd seu-repositorio
   ```
2. Instale as dependências
 ```cmd
  git clone https://github.com/seu-usuario/seu-repositorio.git
  cd seu-repositorio
  ```
3. Instale as [dependências]("./requirements.txt")
   ```cmd
   pip install -r requirements.txt
   ```
4. Configure as variáveis de ambiente:
   Crie um arquivo .env na raiz do projeto com as variáveis:
```env
SECRET_KEY = "chave_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

BARD_TOKEN='token_bard'
BARD_TOKEN_TS='token_bard_ts'
```
obs.: O token é obtido ao acessar os cookies do aplicativo, na visão de desenvolvedor.

## Rodando a API

Execute o comendo para iniciar a API:
```cmd
uvicorn app:app --reload
```
ou
```cmd
python uvicorn app:app --reload
```
A API estará disponível em **http://localhost:8000**. Acesse a documentação interativa em **http://localhost:8000/docs** para explorar os endpoints.

## Endpoints

`Fique atento, todos os endpoints fora o de criar usuário e de fazer login, requerem o token de aceso! Normalmente ele é enviado pelo próprio navegador, mas em um cenário de testagem, ele deve ser passado manualmente pela ferramenta utilizada.`

### Autenticação

A API suporta autenticação por meio de OAuth2.

Fazer login
* **Método**: `POST`
* **Endpoint**: `/login`
* **Descrição**: Autentica um usuário e gera um token de acesso
* **Parâmetros**:
  * `username` (str): Nome de usuário
  * `password` (str): Senha do uruário

### Usuários (Users)

Obter informações e verificar se o usuário está autenticado
* **Método**: `GET`
* **Endpoint**: `/users/me`
* **Descrição**: Obtém informações sobre o usuário autenticado
* **Parâmetros**: Nenhum

Criar um novo usuário
* **Método**: `POST`
* **Endpoint**: `/user`
* **Descrição**: Cria um novo usuário
* **Parâmetros**:
  * `username` (str): nome de usuário
  * `email` (str, opcional): Endereço de e-mail do usuário
  * `full_name` (str, opcional): Nome completo do usuário
  * `password` (str): Senha do usuário
 
Atualizar inforçaões do usuário
* **Método**: `PATCH`
* **Endpoint**: `/updateuser`
* **Descrição**: Atualiza as informações do usuário autenticado
* **Parâmetros**:
  * `username` (str): Nome de usuário (Não pode ser alterado)
  * `email` (str, opcional): Novo endereço de e-mail do usuário
  * `full_name` (str, opcional): Novo nome completo do usuário
  * `password` (str, opcional): Utilizada apenas para checagem

Excluir usuário
* **Método**: `DELETE`
* **Endpoint**: `/deleteuser`
* **Descrição**: Exclui o usuário autenticado
* **Parâmetros**:
  * `username` (str): Nome de usuário
  * `password` (str): Utilizada para validação

Obter lista de usuários (sem senhas)
* **Método**: `GET`
* **Endpoint**: `/users`
* **Descrição**: Obtém uma lista de todos os usuários (sem as senhas)
* **Parâmetros**: nenhum

Obter lista de uruários (incluindo senhas, para debug)
* **Método**: `GET`
* **Endpoint**: `/usersdebug`
* **Descrição**: Obtém uma lista de todos os usuários, incluindo suas senhas em hash
* **Parâmetros**: nenhum
  

### Histórias (Stories)

Adicionar uma nova história:
* **Método**: `POST`
* **Endpoint**: `/story`
* **Descrição**: Adiciona uma nova história que é completada automaticamente por Inteligência Artificial
* **Parâmetros**:
  * `titulo` (str): Título da história
  * `historia` (str, opcional): Início da história que sera completada pela IA do Google (Bard)
  * `categoria` (str): Categoria da História (também é utilizada na prompt)

Obter lsita de histórias:
 * **Método**: `GET`
* **Endpoint**: `/stories`
* **Descrição**: Obtém uma lista de todas as histórias
* **Parâmetros**: Nenhum

Atualizar história existente
 * **Método**: `PATCH`
* **Endpoint**: `/updatestory`
* **Descrição**: Atualiza o conteúdo de uma história existente
* **Parâmetros**:
  * `titulo` (str): Título da história a ser atualizada
  * `categoria` (str): Categoria da história a ser atualizada
  * `historia` (str): Novo conteúdo da história

Excluir história
 * **Método**: `DELETE`
* **Endpoint**: `/deletestory`
* **Descrição**: Exclui uma história existente
* **Parâmetros**:
  * `titulo` (str): Título da história a ser exluída
  * `categoria` (str): Categoria da hisória a ser exclúida

