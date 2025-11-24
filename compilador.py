import re

# ==========================================
# 1. ANÁLISE LÉXICA (O Tokenizador)
# ==========================================
# Quebra a string de entrada em uma lista de tokens.

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
        """Avança para o próximo caractere no texto de entrada."""
        self.posicao += 1
        if self.posicao < len(self.texto):
            self.caractere_atual = self.texto[self.posicao]
        else:
            self.caractere_atual = None

    def pular_espaco_branco(self):
        """Ignora caracteres de espaço em branco."""
        while self.caractere_atual is not None and self.caractere_atual.isspace():
            self.avancar()

    def inteiro(self):
        """Lê um número inteiro da entrada."""
        resultado = ''
        while self.caractere_atual is not None and self.caractere_atual.isdigit():
            resultado += self.caractere_atual
            self.avancar()
        return int(resultado)

    def identificador(self):
        """Lê identificadores e palavras-chave reservadas."""
        resultado = ''
        while self.caractere_atual is not None and self.caractere_atual.isalnum():
            resultado += self.caractere_atual
            self.avancar()
        
        # Palavras-chave da linguagem
        if resultado == 'int': return Token('INT', 'int')
        if resultado == 'print': return Token('PRINT', 'print')
        return Token('ID', resultado)

    def obter_proximo_token(self):
        """Analisa o caractere atual e retorna o próximo token."""
        while self.caractere_atual is not None:
            if self.caractere_atual.isspace():
                self.pular_espaco_branco()
                continue
            
            if self.caractere_atual.isdigit():
                return Token('INTEIRO', self.inteiro())

            if self.caractere_atual.isalpha():
                return Token('ID', self.identificador().valor)

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
        """Gera uma lista completa de tokens."""
        tokens = []
        while True:
            tok = self.obter_proximo_token()
            tokens.append(tok)
            if tok.tipo == 'EOF':
                break
        return tokens


# ==========================================
# 2. ANÁLISE SINTÁTICA (O Construtor de AST)
# ==========================================
# Constrói uma estrutura de árvore a partir dos tokens.

class NoAST: pass

class OperacaoBinaria(NoAST):
    def __init__(self, esquerda, op, direita):
        self.esquerda = esquerda
        self.op = op
        self.direita = direita
    def __repr__(self): return f"({self.esquerda} {self.op.valor} {self.direita})"

class Numero(NoAST):
    def __init__(self, token):
        self.valor = token.valor
    def __repr__(self): return str(self.valor)

class Variavel(NoAST):
    def __init__(self, token):
        self.nome = token.valor
    def __repr__(self): return f"Var({self.nome})"

class DeclaracaoVar(NoAST):
    def __init__(self, no_var, no_tipo):
        self.no_var = no_var
        self.no_tipo = no_tipo
    def __repr__(self): return f"Decl({self.no_var.nome})"

class Atribuicao(NoAST):
    def __init__(self, esquerda, direita):
        self.esquerda = esquerda
        self.direita = direita
    def __repr__(self): return f"Atrib({self.esquerda.nome} = {self.direita})"

class Impressao(NoAST):
    def __init__(self, expressao):
        self.expressao = expressao
    def __repr__(self): return f"Imprimir({self.expressao})"

class AnalisadorSintatico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicao = 0
        self.token_atual = self.tokens[self.posicao]

    def consumir(self, tipo_token):
        """Verifica se o token atual é do tipo esperado e avança."""
        if self.token_atual.tipo == tipo_token:
            self.posicao += 1
            if self.posicao < len(self.tokens):
                self.token_atual = self.tokens[self.posicao]
        else:
            raise Exception(f"Erro Sintático: Esperado {tipo_token}, encontrado {self.token_atual.tipo}")

    def fator(self):
        """Analisa números, variáveis ou expressões entre parênteses."""
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
        raise Exception(f"Erro Sintático: Fator inválido encontrado '{token.valor}'")

    def termo(self):
        """Analisa multiplicação e divisão."""
        no = self.fator()
        while self.token_atual.tipo in ('MULT', 'DIV'):
            token = self.token_atual
            self.consumir(token.tipo)
            no = OperacaoBinaria(esquerda=no, op=token, direita=self.fator())
        return no

    def expressao(self):
        """Analisa adição e subtração."""
        no = self.termo()
        while self.token_atual.tipo in ('MAIS', 'MENOS'):
            token = self.token_atual
            self.consumir(token.tipo)
            no = OperacaoBinaria(esquerda=no, op=token, direita=self.termo())
        return no

    def instrucao(self):
        """Analisa uma única instrução (declaração, impressão ou atribuição)."""
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
        
        raise Exception(f"Erro Sintático: Instrução desconhecida começando com {self.token_atual}")

    def analisar(self):
        """Executa a análise sintática completa."""
        instrucoes = []
        while self.token_atual.tipo != 'EOF':
            instrucoes.append(self.instrucao())
        return instrucoes


# ==========================================
# 3. ANÁLISE SEMÂNTICA (Verificação de Contexto)
# ==========================================
# Verifica declarações de variáveis e tipos usando a Tabela de Símbolos.

class TabelaDeSimbolos:
    def __init__(self):
        self.simbolos = {} # {nome: tipo}

    def definir(self, nome, tipo):
        if nome in self.simbolos:
            raise Exception(f"Erro Semântico: Variável '{nome}' já foi declarada.")
        self.simbolos[nome] = tipo

    def buscar(self, nome):
        if nome not in self.simbolos:
            raise Exception(f"Erro Semântico: Variável '{nome}' não declarada.")
        return self.simbolos[nome]

class AnalisadorSemantico:
    def __init__(self):
        self.tabela_simbolos = TabelaDeSimbolos()

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
        elif isinstance(no, Numero):
            pass


# ==========================================
# 4. GERAÇÃO DE CÓDIGO INTERMEDIÁRIO (RI)
# ==========================================
# Gera Código de Três Endereços (TAC - Three Address Code)

class InstrucaoTAC:
    def __init__(self, op, arg1, arg2, resultado):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.resultado = resultado
    
    def __repr__(self):
        if self.op == '=':
            return f"{self.resultado} = {self.arg1}"
        elif self.op == 'print':
            return f"print {self.arg1}"
        else:
            return f"{self.resultado} = {self.arg1} {self.op} {self.arg2}"

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
        
        elif isinstance(no, DeclaracaoVar):
            # Declarações não geram código executável nesta RI simples
            pass

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

        elif isinstance(no, Numero):
            return str(no.valor)

        elif isinstance(no, Variavel):
            return no.nome

# ==========================================
# 5. OTIMIZAÇÃO (Dobra de Constantes)
# ==========================================
# Simplifica instruções como t1 = 2 + 3 -> t1 = 5

class Otimizador:
    def otimizar(self, instrucoes):
        otimizado = []

        for instr in instrucoes:
            # Tenta simplificar Operações Binárias
            if instr.op in ['+', '-', '*', '/']:
                # Verifica se argumentos são constantes numéricas
                arg1_e_const = instr.arg1.isdigit()
                arg2_e_const = instr.arg2.isdigit()
                
                if arg1_e_const and arg2_e_const:
                    val1 = int(instr.arg1)
                    val2 = int(instr.arg2)
                    res = 0
                    if instr.op == '+': res = val1 + val2
                    elif instr.op == '-': res = val1 - val2
                    elif instr.op == '*': res = val1 * val2
                    elif instr.op == '/': res = int(val1 / val2)
                    
                    # Cria uma atribuição direta ao invés da operação matemática
                    # ex: t1 = 5 ao invés de t1 = 2 + 3
                    nova_instr = InstrucaoTAC('=', str(res), None, instr.resultado)
                    otimizado.append(nova_instr)
                    continue

            otimizado.append(instr)
        return otimizado


# ==========================================
# 6. GERAÇÃO DE CÓDIGO FINAL (A Máquina Virtual)
# ==========================================
# Executa as instruções TAC.

class MaquinaVirtual:
    def __init__(self):
        self.memoria = {} # Armazena valores das variáveis

    def obter_valor(self, arg):
        if arg.isdigit() or (arg.startswith('-') and arg[1:].isdigit()):
            return int(arg)
        return self.memoria.get(arg, 0)

    def executar(self, instrucoes):
        print("--- SAÍDA DO PROGRAMA ---")
        for instr in instrucoes:
            if instr.op == '=':
                val = self.obter_valor(instr.arg1)
                self.memoria[instr.resultado] = val
            
            elif instr.op == 'print':
                val = self.obter_valor(instr.arg1)
                print(val)
            
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
# PROGRAMA PRINCIPAL
# ==========================================

def main():
    # Código de Exemplo na nossa linguagem MiniCalc
    codigo_fonte = """
    int a;
    a = 10;
    int b;
    b = a + 5 * (2 + 3); 
    print(b);
    """
    
    print(f"Código Fonte:\n{codigo_fonte}\n")

    try:
        # 1. Análise Léxica
        lexico = AnalisadorLexico(codigo_fonte)
        tokens = lexico.tokenizar()
        # print("Tokens:", tokens) 

        # 2. Análise Sintática
        sintatico = AnalisadorSintatico(tokens)
        ast = sintatico.analisar()
        print("AST (Árvore Sintática) construída com sucesso.")

        # 3. Análise Semântica
        semantico = AnalisadorSemantico()
        semantico.visitar(ast)
        print("Verificações Semânticas passaram com sucesso.")

        # 4. Geração de RI (Código Intermediário)
        gerador_ri = GeradorCodigoIntermediario()
        gerador_ri.gerar(ast)
        print("\nRI Gerada (Código de Três Endereços):")
        for i in gerador_ri.instrucoes: print(i)

        # 5. Otimização
        otimizador = Otimizador()
        instrucoes_otimizadas = otimizador.otimizar(gerador_ri.instrucoes)
        print("\nRI Otimizada (Dobra de Constantes):")
        for i in instrucoes_otimizadas: print(i)

        # 6. Execução
        print("\nExecutando...")
        vm = MaquinaVirtual()
        vm.executar(instrucoes_otimizadas)

    except Exception as e:
        print(f"Erro de Compilação: {e}")

if __name__ == "__main__":
    main()