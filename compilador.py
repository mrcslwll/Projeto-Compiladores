import sys

# ==========================================
# UTILITÁRIOS DE APRESENTAÇÃO (CORES)
# ==========================================
class Cores:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_fase(nome):
    print(f"\n{Cores.HEADER}{'='*40}")
    print(f" {nome}")
    print(f"{'='*40}{Cores.ENDC}")

# ==========================================
# 1. ANÁLISE LÉXICA (O Tokenizador)
# ==========================================
class Token:
    def __init__(self, tipo, valor=None):
        self.tipo = tipo
        self.valor = valor
    
    def __repr__(self):
        return f"Token({self.tipo}, {self.valor})"

class AnalisadorLexico:
    def __init__(self, texto):
        self.texto = texto
        self.posicao = 0
        self.caractere_atual = self.texto[self.posicao] if self.texto else None

    def avancar(self):
        self.posicao += 1
        if self.posicao < len(self.texto):
            self.caractere_atual = self.texto[self.posicao]
        else:
            self.caractere_atual = None

    def pular_espaco_branco(self):
        while self.caractere_atual is not None and self.caractere_atual.isspace():
            self.avancar()

    def inteiro(self):
        resultado = ''
        while self.caractere_atual is not None and self.caractere_atual.isdigit():
            resultado += self.caractere_atual
            self.avancar()
        return int(resultado)

    def identificador(self):
        resultado = ''
        while self.caractere_atual is not None and self.caractere_atual.isalnum():
            resultado += self.caractere_atual
            self.avancar()
        
        # Palavras-chave
        if resultado == 'int': return Token('INT', 'int')
        if resultado == 'print': return Token('PRINT', 'print')
        return Token('ID', resultado)

    def obter_proximo_token(self):
        while self.caractere_atual is not None:
            if self.caractere_atual.isspace():
                self.pular_espaco_branco()
                continue
            
            if self.caractere_atual.isdigit():
                return Token('INTEIRO', self.inteiro())

            if self.caractere_atual.isalpha():
                # Retorna exatamente o token criado (INT, PRINT ou ID)
                return self.identificador()

            if self.caractere_atual == '=':
                self.avancar()
                return Token('ATRIBUICAO', '=')
            if self.caractere_atual == ';':
                self.avancar()
                return Token('PONTO_VIRGULA', ';')
            if self.caractere_atual == '+':
                self.avancar()
                return Token('MAIS', '+')
            if self.caractere_atual == '-':
                self.avancar()
                return Token('MENOS', '-')
            if self.caractere_atual == '*':
                self.avancar()
                return Token('MULT', '*')
            if self.caractere_atual == '/':
                self.avancar()
                return Token('DIV', '/')
            if self.caractere_atual == '(':
                self.avancar()
                return Token('PARENTESE_ESQ', '(')
            if self.caractere_atual == ')':
                self.avancar()
                return Token('PARENTESE_DIR', ')')

            raise Exception(f"Erro Léxico: Caractere inválido '{self.caractere_atual}'")

        return Token('EOF', None)

    def tokenizar(self):
        tokens = []
        while True:
            tok = self.obter_proximo_token()
            tokens.append(tok)
            if tok.tipo == 'EOF':
                break
        return tokens

# ==========================================
# 2. ANÁLISE SINTÁTICA (AST)
# ==========================================
class NoAST: pass

class OperacaoBinaria(NoAST):
    def __init__(self, esquerda, op, direita):
        self.esquerda = esquerda; self.op = op; self.direita = direita
    def __repr__(self): return f"({self.esquerda} {self.op.valor} {self.direita})"

class Numero(NoAST):
    def __init__(self, token): self.valor = token.valor
    def __repr__(self): return str(self.valor)

class Variavel(NoAST):
    def __init__(self, token): self.nome = token.valor
    def __repr__(self): return f"Var({self.nome})"

class DeclaracaoVar(NoAST):
    def __init__(self, no_var, no_tipo): self.no_var = no_var; self.no_tipo = no_tipo
    def __repr__(self): return f"Decl({self.no_var.nome})"

class Atribuicao(NoAST):
    def __init__(self, esquerda, direita): self.esquerda = esquerda; self.direita = direita
    def __repr__(self): return f"Atrib({self.esquerda.nome} = {self.direita})"

class Impressao(NoAST):
    def __init__(self, expressao): self.expressao = expressao
    def __repr__(self): return f"Imprimir({self.expressao})"

class AnalisadorSintatico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicao = 0
        self.token_atual = self.tokens[self.posicao]

    def consumir(self, tipo_token):
        if self.token_atual.tipo == tipo_token:
            self.posicao += 1
            if self.posicao < len(self.tokens):
                self.token_atual = self.tokens[self.posicao]
        else:
            raise Exception(f"Erro Sintático: Esperado {tipo_token}, encontrado {self.token_atual.tipo}")

    def fator(self):
        token = self.token_atual
        if token.tipo == 'INTEIRO':
            self.consumir('INTEIRO')
            return Numero(token)
        elif token.tipo == 'ID':
            self.consumir('ID')
            return Variavel(token)
        elif token.tipo == 'PARENTESE_ESQ':
            self.consumir('PARENTESE_ESQ')
            no = self.expressao()
            self.consumir('PARENTESE_DIR')
            return no
        raise Exception(f"Erro Sintático: Fator inválido '{token.valor}'")

    def termo(self):
        no = self.fator()
        while self.token_atual.tipo in ('MULT', 'DIV'):
            token = self.token_atual
            self.consumir(token.tipo)
            no = OperacaoBinaria(esquerda=no, op=token, direita=self.fator())
        return no

    def expressao(self):
        no = self.termo()
        while self.token_atual.tipo in ('MAIS', 'MENOS'):
            token = self.token_atual
            self.consumir(token.tipo)
            no = OperacaoBinaria(esquerda=no, op=token, direita=self.termo())
        return no

    def instrucao(self):
        if self.token_atual.tipo == 'INT':
            self.consumir('INT')
            nome_var = self.token_atual
            self.consumir('ID')
            self.consumir('PONTO_VIRGULA')
            return DeclaracaoVar(Variavel(nome_var), 'int')
        
        elif self.token_atual.tipo == 'PRINT':
            self.consumir('PRINT')
            self.consumir('PARENTESE_ESQ')
            no = self.expressao()
            self.consumir('PARENTESE_DIR')
            self.consumir('PONTO_VIRGULA')
            return Impressao(no)

        elif self.token_atual.tipo == 'ID':
            var = Variavel(self.token_atual)
            self.consumir('ID')
            self.consumir('ATRIBUICAO')
            direita = self.expressao()
            self.consumir('PONTO_VIRGULA')
            return Atribuicao(var, direita)
        
        # Ignora pontos e vírgulas extras (para o modo interativo)
        elif self.token_atual.tipo == 'PONTO_VIRGULA':
            self.consumir('PONTO_VIRGULA')
            return None 
            
        raise Exception(f"Erro Sintático: Instrução inválida começando com {self.token_atual}")

    def analisar(self):
        instrucoes = []
        while self.token_atual.tipo != 'EOF':
            res = self.instrucao()
            if res: instrucoes.append(res)
        return instrucoes

# ==========================================
# 3. ANÁLISE SEMÂNTICA
# ==========================================
class TabelaDeSimbolos:
    def __init__(self):
        self.simbolos = {} 

    def definir(self, nome, tipo):
        if nome in self.simbolos:
            raise Exception(f"Erro Semântico: Variável '{nome}' já foi declarada.")
        self.simbolos[nome] = tipo

    def buscar(self, nome):
        if nome not in self.simbolos:
            raise Exception(f"Erro Semântico: Variável '{nome}' não declarada.")
        return self.simbolos[nome]

class AnalisadorSemantico:
    # CORREÇÃO APLICADA: Usa 'is not None' para evitar recriar a tabela se ela estiver vazia
    def __init__(self, tabela_existente=None):
        self.tabela_simbolos = tabela_existente if tabela_existente is not None else TabelaDeSimbolos()

    def visitar(self, no):
        if isinstance(no, list):
            for stmt in no: self.visitar(stmt)
        elif isinstance(no, DeclaracaoVar):
            self.tabela_simbolos.definir(no.no_var.nome, no.no_tipo)
        elif isinstance(no, Atribuicao):
            self.tabela_simbolos.buscar(no.esquerda.nome)
            self.visitar(no.direita)
        elif isinstance(no, Impressao):
            self.visitar(no.expressao)
        elif isinstance(no, OperacaoBinaria):
            self.visitar(no.esquerda)
            self.visitar(no.direita)
        elif isinstance(no, Variavel):
            self.tabela_simbolos.buscar(no.nome)

# ==========================================
# 4. GERAÇÃO DE CÓDIGO (RI)
# ==========================================
class InstrucaoTAC:
    def __init__(self, op, arg1, arg2, resultado):
        self.op = op; self.arg1 = arg1; self.arg2 = arg2; self.resultado = resultado
    
    def __repr__(self):
        if self.op == '=': return f"{self.resultado} = {self.arg1}"
        elif self.op == 'print': return f"print {self.arg1}"
        else: return f"{self.resultado} = {self.arg1} {self.op} {self.arg2}"

class GeradorCodigoIntermediario:
    def __init__(self):
        self.instrucoes = []
        self.contador_temp = 0

    def novo_temp(self):
        self.contador_temp += 1
        return f"t{self.contador_temp}"

    def gerar(self, no):
        if isinstance(no, list):
            for stmt in no: self.gerar(stmt)
        elif isinstance(no, DeclaracaoVar): pass
        elif isinstance(no, Atribuicao):
            endereco_val = self.gerar(no.direita)
            self.instrucoes.append(InstrucaoTAC('=', endereco_val, None, no.esquerda.nome))
        elif isinstance(no, Impressao):
            endereco_val = self.gerar(no.expressao)
            self.instrucoes.append(InstrucaoTAC('print', endereco_val, None, None))
        elif isinstance(no, OperacaoBinaria):
            addr1 = self.gerar(no.esquerda)
            addr2 = self.gerar(no.direita)
            temp = self.novo_temp()
            self.instrucoes.append(InstrucaoTAC(no.op.valor, addr1, addr2, temp))
            return temp
        elif isinstance(no, Numero): return str(no.valor)
        elif isinstance(no, Variavel): return no.nome

# ==========================================
# 5. OTIMIZADOR
# ==========================================
class Otimizador:
    def otimizar(self, instrucoes):
        otimizado = []
        for instr in instrucoes:
            if instr.op in ['+', '-', '*', '/']:
                arg1_e_const = instr.arg1.isdigit()
                arg2_e_const = instr.arg2.isdigit()
                if arg1_e_const and arg2_e_const:
                    val1, val2 = int(instr.arg1), int(instr.arg2)
                    res = 0
                    if instr.op == '+': res = val1 + val2
                    elif instr.op == '-': res = val1 - val2
                    elif instr.op == '*': res = val1 * val2
                    elif instr.op == '/': res = int(val1 / val2)
                    otimizado.append(InstrucaoTAC('=', str(res), None, instr.resultado))
                    continue
            otimizado.append(instr)
        return otimizado

# ==========================================
# 6. MÁQUINA VIRTUAL
# ==========================================
class MaquinaVirtual:
    # CORREÇÃO APLICADA: Usa 'is not None' para garantir persistência da memória
    def __init__(self, memoria_existente=None):
        self.memoria = memoria_existente if memoria_existente is not None else {}

    def obter_valor(self, arg):
        if arg.isdigit() or (arg.startswith('-') and arg[1:].isdigit()):
            return int(arg)
        return self.memoria.get(arg, 0)

    def executar(self, instrucoes):
        print(f"{Cores.OKGREEN}>>> SAÍDA DO PROGRAMA:{Cores.ENDC}")
        for instr in instrucoes:
            if instr.op == '=':
                val = self.obter_valor(instr.arg1)
                self.memoria[instr.resultado] = val
            elif instr.op == 'print':
                val = self.obter_valor(instr.arg1)
                print(f"   {Cores.BOLD}{val}{Cores.ENDC}")
            elif instr.op in ['+', '-', '*', '/']:
                val1 = self.obter_valor(instr.arg1)
                val2 = self.obter_valor(instr.arg2)
                res = 0
                if instr.op == '+': res = val1 + val2
                elif instr.op == '-': res = val1 - val2
                elif instr.op == '*': res = val1 * val2
                elif instr.op == '/': res = int(val1 / val2)
                self.memoria[instr.resultado] = res

# ==========================================
# DRIVERS DE EXECUÇÃO
# ==========================================

def compilar_e_executar(codigo_fonte, tabela_simbolos=None, memoria=None, verbose=True):
    try:
        # Pipeline Completo
        tokens = AnalisadorLexico(codigo_fonte).tokenizar()
        ast = AnalisadorSintatico(tokens).analisar()
        
        # Se passar tabelas, usa elas (Modo Interativo), senão cria novas (Modo Demo)
        semantico = AnalisadorSemantico(tabela_simbolos)
        semantico.visitar(ast)
        
        gerador_ri = GeradorCodigoIntermediario()
        gerador_ri.gerar(ast)
        
        otimizador = Otimizador()
        instrucoes_otimizadas = otimizador.otimizar(gerador_ri.instrucoes)
        
        if verbose:
            print(f"{Cores.OKCYAN}[1] Tokens: {len(tokens)} gerados.{Cores.ENDC}")
            print(f"{Cores.OKCYAN}[2] AST: Estrutura montada.{Cores.ENDC}")
            print(f"{Cores.OKCYAN}[3] Semântica: Verificação OK.{Cores.ENDC}")
            print(f"{Cores.OKCYAN}[4] Otimização: {len(gerador_ri.instrucoes)} instr -> {len(instrucoes_otimizadas)} instr.{Cores.ENDC}")
        
        vm = MaquinaVirtual(memoria)
        vm.executar(instrucoes_otimizadas)
        
        return True
    except Exception as e:
        print(f"{Cores.FAIL}Erro: {e}{Cores.ENDC}")
        return False

def modo_interativo():
    print_fase("MODO INTERATIVO (Digite 'sair' para encerrar)")
    print("Exemplos: 'int a;', 'a = 10;', 'print(a);'")
    
    # Persistência de estado
    tabela_global = TabelaDeSimbolos()
    memoria_global = {}
    
    while True:
        try:
            entrada = input(f"{Cores.OKBLUE}MiniCalc > {Cores.ENDC}")
            if entrada.lower() in ['sair', 'exit']: break
            if not entrada.strip(): continue
            
            # Compila a linha mantendo o histórico de variáveis
            compilar_e_executar(entrada, tabela_global, memoria_global, verbose=False)
            
        except KeyboardInterrupt:
            break

def main():
    print(f"{Cores.HEADER}COMPILADOR MINICALC 2.0{Cores.ENDC}")
    print("1. Executar Demonstração Completa")
    print("2. Abrir Modo Interativo (Shell)")
    
    escolha = input("Escolha uma opção (1 ou 2): ")
    
    if escolha == '2':
        modo_interativo()
    else:
        print_fase("DEMONSTRAÇÃO AUTOMÁTICA")
        codigo_demo = """
        int x;
        x = 10;
        int y;
        y = x + 5 * (2 + 3); 
        print(y);
        """
        print(f"Código Fonte:{Cores.WARNING}{codigo_demo}{Cores.ENDC}")
        compilar_e_executar(codigo_demo)

if __name__ == "__main__":
    main()
