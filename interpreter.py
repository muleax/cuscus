import string

KEYWORDS = set(['print', 'while', 'if', 'else', 'bool'])

ADDSUB_OPS = ('+', '-')
MULDIV_OPS = ('*', '/')
CMP_OPS = ('==', '>', '>=', '<', '<=')
LOGIC_OPS = ('&&', '||')
MICS_OPS = ('=', '?', ':', '(', ')', '{', '}')
OPS_TOKENS = set(ADDSUB_OPS + MULDIV_OPS + CMP_OPS + LOGIC_OPS + MICS_OPS)

COMMENT_TOKEN = '//'

OPS_NODES = ADDSUB_OPS + MULDIV_OPS + CMP_OPS + LOGIC_OPS + ('=',)
CUSTOM_NODES = ('num', 'var', 'neg', 'bool', 'ternary', 'print', 'blocklist', 'if', 'while')
AST_NODES = set(OPS_NODES + CUSTOM_NODES)

def check_token(token, expected):
	if token != expected:
		raise ValueError(f"Wrong token: {token} while {expected} expected")
	return token

def check_node(node):
	if not node:
		raise ValueError("Wrong expression")
	return node


def ast_num(ctx):
	token = ctx.front()
	if token and token.isdigit():
		ctx.pop()
		return AstNode('num', None, int(token))

	return None

def ast_var(ctx):
	token = ctx.front()
	if token and token[0].isalpha():
		if token not in KEYWORDS:
			ctx.pop()
			return AstNode('var', None, token)

	return None

def ast_neg(ctx):
	if ctx.front() == '-':
		ctx.pop()
		node = check_node(ast_unit(ctx))
		return AstNode('neg', [node])

	return None

def ast_bool(ctx):
	if ctx.front() == 'bool':
		ctx.pop()
		check_token(ctx.pop(), '(')
		node = check_node(ast_add(ctx))
		check_token(ctx.pop(), ')')
		return AstNode('bool', [node])

	return None

def ast_braced_expr(ctx):
	if ctx.front() == '(':
		ctx.pop()
		node = check_node(ast_expr(ctx))
		check_token(ctx.pop(), ')')
		return node
	
	return None

def ast_unit(ctx):
	node = ast_num(ctx)
	if not node:
		node = ast_var(ctx)
		if not node:
			node = ast_neg(ctx)
			if not node:
				node = ast_bool(ctx)
				if not node:
					node = ast_braced_expr(ctx)

	return node

def ast_muldiv(ctx):
	node = ast_unit(ctx)
	if node and ctx.front() in MULDIV_OPS:
		op = ctx.pop()
		muldiv = check_node(ast_muldiv(ctx))
		node = AstNode(op, [node, muldiv])

	return node
		
def ast_sub(ctx):
	node = ast_muldiv(ctx)
	if node and ctx.front() == '-':
		children = [node]
		while ctx.front() == '-':
			ctx.pop()
			muldiv = check_node(ast_muldiv(ctx))
			children.append(muldiv)
		node = AstNode('-', children)

	return node

def ast_add(ctx):
	node = ast_sub(ctx)
	if node and ctx.front() == '+':
		ctx.pop()
		add = check_node(ast_add(ctx))
		node = AstNode('+', [node, add])

	return node

def ast_cmpadd(ctx):
	node = ast_add(ctx)
	if node and ctx.front() in CMP_OPS:
		op = ctx.pop()
		right = check_node(ast_add(ctx))
		return AstNode(op, [node, right])

	return node

def ast_logic(ctx):
	node = ast_cmpadd(ctx)
	if node and ctx.front() in LOGIC_OPS:
		op = ctx.pop()
		right = check_node(ast_logic(ctx))
		node = AstNode(op, [node, right])
	
	return node

# EXPR := LOGIC [? EXPR : EXPR]
def ast_expr(ctx):
	node = ast_logic(ctx)
	if node and ctx.front() == '?':
		ctx.pop()
		expr2 = check_node(ast_expr(ctx))
		check_token(ctx.pop(), ':')
		expr3 = check_node(ast_expr(ctx))
		node = AstNode('ternary', [node, expr2, expr3])
	
	return node

# IF := if (EXPR) BLOCK [else BLOCK]
def ast_if(ctx):
	if ctx.front() == 'if':
		ctx.pop()
		check_token(ctx.pop(), '(')
		cond = check_node(ast_expr(ctx))
		check_token(ctx.pop(), ')')
		children = [cond, check_node(ast_block(ctx))]
		if ctx.front() == 'else':
			ctx.pop()
			children.append(check_node(ast_block(ctx)))
		return AstNode('if', children)
	
	return None

# WHILE := while (EXPR) BLOCK
def ast_while(ctx):
	if ctx.front() == 'while':
		ctx.pop()
		check_token(ctx.pop(), '(')
		cond = check_node(ast_expr(ctx))
		check_token(ctx.pop(), ')')
		body = check_node(ast_block(ctx))
		return AstNode('while', [cond, body])
	
	return None

def ast_print(ctx):
	if ctx.front() == 'print':
		ctx.pop()
		expr = ast_expr(ctx)
		if not expr:
			raise ValueError("ast_print: wrong expr")

		return AstNode('print', [expr])
	
	return None

def ast_assign(ctx):
	ctx.tag()
	var = ast_var(ctx)
	if var and ctx.front() == '=':
		ctx.pop()
		expr = ast_expr(ctx)
		if not expr:
			raise ValueError("ast_assign: wrong expr for " + var)

		return AstNode('=', [expr], var.payload)
	
	ctx.revert()
	return None

def ast_cmd(ctx):
	node = ast_assign(ctx)
	if not node:
		node = ast_print(ctx)

	return node

def ast_braced_blocklist(ctx):
	if ctx.front() == '{':
		ctx.pop()
		
		node = ast_blocklist(ctx)		
		
		token = ctx.pop()
		if token != '}':
			raise ValueError("ast_braced_blocklist: wrong token " + token)
			
		return node

	return None

# BLOCK := CMD|IF|WHILE|'{'BLOCKLIST'}'
def ast_block(ctx):
	block = ast_cmd(ctx)
	if not block:
		block = ast_if(ctx)
		if not block:
			block = ast_while(ctx)
			if not block:
				block = ast_braced_blocklist(ctx)

	return block

def ast_blocklist(ctx):
	blocklist = []
	block = ast_block(ctx)
	while block:
		blocklist.append(block)
		block = ast_block(ctx)

	return AstNode('blocklist', blocklist)

class AstNode:
	def __init__(self, type, children = None, payload = None):
		if type not in AST_NODES:
			raise ValueError(f"Wrong AstNode type: {type}")
		self.type = type
		self.children = children
		self.payload = payload

	def print(self, offset = ''):
		payload_str = str(self.payload) if (self.payload is not None) else ""
		print(f"{offset}{self.type} {payload_str}")
		if self.children:
			for child in self.children:
				child.print(offset + '    ')

class BuildContext:
	def __init__(self, tokens):
		self.tokens = tokens
		self.i = 0

	def pop(self):
		self.i += 1
		return self.tokens[self.i - 1]

	def push(self):
		self.i -= 1

	def tag(self):
		self.tagIndex = self.i

	def revert(self):
		self.i = self.tagIndex

	def front(self):
		return self.tokens[self.i] if self.has() else None

	def has(self):
		return self.i < len(self.tokens)

def is_valid_interger(token):
	return token.isdigit()

def is_valid_var(token):
	if not token:
		return False

	if not (token[0].isalpha() or token[0] == '_'):
		return False
	
	return all(c == '_' or c.isalpha() or c.isdigit() for c in token)

def check_is_valid_token(token):
	if token not in OPS_TOKENS:
		if token not in KEYWORDS:
			if not is_valid_interger(token):
				if not is_valid_var(token):
					raise ValueError(f"Wrong token {token}")

def tokenize(source):
	LITERAL_SYMBOLS = set(string.ascii_letters + string.digits + '_')
	tokens = []
	token = None
	for line in source.splitlines():
		for c in line:
			if c in ' \t\n':
				if token:
					check_is_valid_token(token)
					tokens.append(token)
					token = None
				continue

			if not token:
				token = c
				continue

			isLiteral = c in LITERAL_SYMBOLS
			prevIsLiteral = token[0] in LITERAL_SYMBOLS

			if isLiteral != prevIsLiteral:
				check_is_valid_token(token)
				tokens.append(token)
				token = c
				continue

			if not isLiteral:
				newToken = token + c
				if newToken == COMMENT_TOKEN:
					token = None
					break

				if newToken in OPS_TOKENS:
					tokens.append(newToken)
					token = None
					continue

				if token in OPS_TOKENS:
					tokens.append(token)
					token = c
					continue
				
			token += c

		if token:
			check_is_valid_token(token)
			tokens.append(token)
			token = None

	return tokens

def build_ast(source):
	tokens = tokenize(source)
	ctx = BuildContext(tokens)
	return ast_blocklist(ctx)


def eval_num(ctx, _, num):
	return num

def eval_var(ctx, _, varname):
	return ctx.env[varname]

def eval_print(ctx, children, _):
	print(' '.join(str(eval_ast(ctx, node)) for node in children))

def eval_assign(ctx, children, varname):
	ctx.env[varname] = eval_ast(ctx, children[0])
	
def eval_blocklist(ctx, children, _):
	ret = None
	for child in children:
		ret = eval_ast(ctx, child)
	return ret

def eval_ternary(ctx, children, _):
	if eval_ast(ctx, children[0]):
		return eval_ast(ctx, children[1])
	else:
		return eval_ast(ctx, children[2])

def eval_eq(ctx, children, _):
	return eval_ast(ctx, children[0]) == eval_ast(ctx, children[1])

def eval_gt(ctx, children, _):
	return eval_ast(ctx, children[0]) > eval_ast(ctx, children[1])

def eval_ge(ctx, children, _):
	return eval_ast(ctx, children[0]) >= eval_ast(ctx, children[1])

def eval_lt(ctx, children, _):
	return eval_ast(ctx, children[0]) < eval_ast(ctx, children[1])

def eval_le(ctx, children, _):
	return eval_ast(ctx, children[0]) <= eval_ast(ctx, children[1])

def eval_and(ctx, children, _):
	return eval_ast(ctx, children[0]) and eval_ast(ctx, children[1])

def eval_or(ctx, children, _):
	return eval_ast(ctx, children[0]) or eval_ast(ctx, children[1])

def eval_if(ctx, children, _):
	if eval_ast(ctx, children[0]):
		eval_ast(ctx, children[1])
	elif len(children) == 3:
		eval_ast(ctx, children[2])

def eval_while(ctx, children, _):
	cond, body = children
	while eval_ast(ctx, cond):
		eval_ast(ctx, body)

def eval_bool(ctx, children, _):
	return bool(eval_ast(ctx, children[0]))

def eval_neg(ctx, children, _):
	return -eval_ast(ctx, children[0])

def eval_add(ctx, children, _):
	return eval_ast(ctx, children[0]) + eval_ast(ctx, children[1])

def eval_sub(ctx, children, _):
	ret = eval_ast(ctx, children[0])
	for i in range(1, len(children)):
		ret -= eval_ast(ctx, children[i])
	return ret

def eval_mul(ctx, children, _):
	return eval_ast(ctx, children[0]) * eval_ast(ctx, children[1])

def eval_div(ctx, children, _):
	divisor = eval_ast(ctx, children[1])
	if divisor == 0:
		raise ValueError("eval_div: devision by zero")
	return eval_ast(ctx, children[0]) / divisor

class EvalContext:
	def __init__(self):
		self.env = {}

OPERATIONS = {
	'num':			eval_num,
	'var': 			eval_var,
	'print':		eval_print,
	'=':			eval_assign,
	'bool': 		eval_bool,
	'neg': 			eval_neg,
	'+': 			eval_add,
	'-': 			eval_sub,
	'*': 			eval_mul,
	'/': 			eval_div,
	'ternary':		eval_ternary,
	'==':			eval_eq,
	'>':			eval_gt,
	'>=':			eval_ge,
	'<':			eval_lt,
	'<=':			eval_le,
	'&&':			eval_and,
	'||':			eval_or,
	'if':			eval_if,
	'while':		eval_while,
	'blocklist':	eval_blocklist
}

if set(OPERATIONS.keys()) != AST_NODES:
	diff = AST_NODES.symmetric_difference(OPERATIONS.keys())
	raise ValueError(f"Inconsistent operation set: {diff}")

def eval_ast(ctx, ast):
	return OPERATIONS[ast.type](ctx, ast.children, ast.payload)

def evaluate(source):
	ast = build_ast(source)
	return eval_ast(EvalContext(), ast)
