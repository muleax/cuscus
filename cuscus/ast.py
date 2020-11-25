from cuscus.definition import *
import cuscus.lexer


OPS_NODES = ADDSUB_OPS + MULDIV_OPS + CMP_OPS + LOGIC_OPS + ('=',)
CUSTOM_NODES = ('num', 'var', 'neg', 'bool', 'ternary', 'print', 'cmdlist',
				'if', 'while', 'for', 'continue', 'break', 'return', 'fundef', 'funcall')
AST_NODES = set(OPS_NODES + CUSTOM_NODES)


class AstNode:
	def __init__(self, node_type, children=None, payload=None):
		if node_type not in AST_NODES:
			raise ValueError(f"Wrong AstNode type: {node_type}")
		self.type = node_type
		self.children = children
		self.payload = payload

	def print(self, offset=''):
		payload_str = str(self.payload) if (self.payload is not None) else ""
		print(f"{offset}{self.type} {payload_str}")
		if self.children:
			for child in self.children:
				child.print(offset + '    ')

class TokenStack:
	def __init__(self, token_list):
		self.tokens = token_list
		self.i = 0

	def pop(self, expected=None):
		token = self.front()
		if (expected is not None) and (token != expected):
			source = ' '.join(self.front_range(16))
			raise ValueError(f"Wrong token \'{token}\' while \'{expected}\' expected: \'{source}...\'")
		self.i += 1
		return token

	def push(self):
		self.i -= 1

	def tag(self):
		return self.i

	def revert(self, tag):
		self.i = tag

	def front(self):
		return self.tokens[self.i] if self.has() else None

	def front_range(self, n):
		return self.tokens[self.i: self.i + n]

	def has(self):
		return self.i < len(self.tokens)


class AstBuilder:
	def __init__(self):
		pass

	def build_ast(self, token_stack):
		self.tokens = token_stack

		ast = self.build('cmdlist', accept_fail=False)
		if self.tokens.has():
			source = ' '.join(self.tokens.front_range(16))
			raise ValueError(f"Failed to parse: {source}...")
		return ast

	def build(self, builder_name, accept_fail=True):
		if accept_fail:
			tag = self.tokens.tag()
			node = getattr(self, builder_name)()
			if not node:
				self.tokens.revert(tag)
		else:
			node = getattr(self, builder_name)()
			if not node:
				source = ' '.join(self.tokens.front_range(16))
				raise ValueError(f"Wrong expression for \'{builder_name}\': \'{source}...\'")
		return node
	# OUT := <open_brace> NONTERMINAL <close_brace>
	def build_braced(self, open_brace, builder_name, close_brace, accept_fail=True):
		if accept_fail:
			tag = self.tokens.tag()
			if self.tokens.pop() == open_brace:
				node = getattr(self, builder_name)()
				if node:
					if self.tokens.pop() == close_brace:
						return node
			self.tokens.revert(tag)
			return None
		else:
			self.tokens.pop(expected=open_brace)
			node = self.build(builder_name, accept_fail=False)
			self.tokens.pop(expected=close_brace)
			return node

	# NUM := 1-9 {0-9}
	def num(self):
		token = self.tokens.front()
		if token and token.isdigit():
			self.tokens.pop()
			return AstNode('num', None, int(token))
		return None

	# VAR := a-z|_ {a-z|0-9|_} except print, while, for, if, else
	def var(self):
		token = self.tokens.front()
		if token and token[0].isalpha():
			if token not in KEYWORDS:
				self.tokens.pop()
				return AstNode('var', None, token)
		return None

	# NEG := -UNIT
	def neg(self):
		if self.tokens.front() == '-':
			self.tokens.pop()
			node = self.build('unit', accept_fail=False)
			return AstNode('neg', [node])
		return None

	# BOOL := bool (EXPR)
	def bool(self):
		if self.tokens.front() == 'bool':
			self.tokens.pop()
			node = self.build_braced('(', 'add', ')', accept_fail=False)
			return AstNode('bool', [node])
		return None

	# UNIT := FUNCALL|NUM|VAR|NEG|BOOL|(EXPR)
	def unit(self):
		node = self.build('funcall')
		if not node:
			node = self.build('num')
			if not node:
				node = self.build('var')
				if not node:
					node = self.build('neg')
					if not node:
						node = self.build('bool')
						if not node:
							node = self.build_braced('(', 'expr', ')')
		return node

	# MULDIV := UNIT [*|/|% MULDIV]
	def muldiv(self):
		node = self.build('unit')
		if node and self.tokens.front() in MULDIV_OPS:
			op = self.tokens.pop()
			muldiv = self.build('muldiv', accept_fail=False)
			node = AstNode(op, [node, muldiv])
		return node

	# SUB := MULDIV {- MULDIV}
	def sub(self):
		node = self.build('muldiv')
		if node and self.tokens.front() == '-':
			children = [node]
			while self.tokens.front() == '-':
				self.tokens.pop()
				muldiv = self.build('muldiv', accept_fail=False)
				children.append(muldiv)
			node = AstNode('-', children)
		return node

	# ADD := SUB [+ ADD]
	def add(self):
		node = self.build('sub')
		if node and self.tokens.front() == '+':
			self.tokens.pop()
			add = self.build('add', accept_fail=False)
			node = AstNode('+', [node, add])
		return node

	# CMPADD := ADD [==|!=|>|>=|<|<= ADD]
	def cmpadd(self):
		node = self.build('add')
		if node and self.tokens.front() in CMP_OPS:
			op = self.tokens.pop()
			right = self.build('add', accept_fail=False)
			return AstNode(op, [node, right])
		return node

	# LOGIC := CMPADD [&&||| LOGIC]
	def logic(self):
		node = self.build('cmpadd')
		if node and self.tokens.front() in LOGIC_OPS:
			op = self.tokens.pop()
			right = self.build('logic', accept_fail=False)
			node = AstNode(op, [node, right])
		return node

	# EXPR := LOGIC [? EXPR : EXPR]
	def expr(self):
		node = self.build('logic')
		if node and self.tokens.front() == '?':
			self.tokens.pop()
			expr2 = self.build('expr', accept_fail=False)
			self.tokens.pop(expected=':')
			expr3 = self.build('expr', accept_fail=False)
			node = AstNode('ternary', [node, expr2, expr3])
		return node

	# IF := if (EXPR) CMD [else CMD]
	def if_statement(self):
		if self.tokens.front() == 'if':
			self.tokens.pop()
			cond = self.build_braced('(', 'expr', ')', accept_fail=False)
			true_body = self.build('cmd', accept_fail=False)
			children = [cond, true_body]

			if self.tokens.front() == 'else':
				self.tokens.pop()
				false_body = self.build('cmd', accept_fail=False)
				children.append(false_body)

			return AstNode('if', children)
		return None

	# WHILE := while (EXPR) CMD
	def while_loop(self):
		if self.tokens.front() == 'while':
			self.tokens.pop()
			cond = self.build_braced('(', 'expr', ')', accept_fail=False)
			body = self.build('cmd', accept_fail=False)
			return AstNode('while', [cond, body])
		return None

	# FOR := for (STATEMENT; EXPR; STATEMENT) CMD
	def for_loop(self):
		if self.tokens.front() == 'for':
			self.tokens.pop()

			self.tokens.pop(expected='(')
			init = self.build('statement', accept_fail=False)
			self.tokens.pop(expected=';')
			cond = self.build('expr', accept_fail=False)
			self.tokens.pop(expected=';')
			inc = self.build('statement', accept_fail=False)
			self.tokens.pop(expected=')')

			body = self.build('cmd', accept_fail=False)

			return AstNode('for', [init, cond, inc, body])
		return None

	# PRINT := print EXPR
	def print(self):
		if self.tokens.front() == 'print':
			self.tokens.pop()
			expr = self.build('expr', accept_fail=False)
			return AstNode('print', [expr])
		return None

	# ASSIGN := VAR = EXPR
	def assign(self):
		var = self.build('var')
		if var and self.tokens.front() == '=':
			self.tokens.pop()
			expr = self.build('expr', accept_fail=False)
			return AstNode('=', [expr], var.payload)
		return None

	# STATEMENT := ASSIGN|PRINT|EXPR
	def statement(self):
		cmd = self.build('assign')
		if not cmd:
			cmd = self.build('print')
			if not cmd:
				cmd = self.build('expr')
		return cmd

	# CONTROL := return[EXPR]|break|continue
	def control(self):
		if self.tokens.front() == 'return':
			self.tokens.pop()
			ret_expr = self.build('expr')
			children = [ret_expr] if ret_expr else None
			return AstNode('return', children)

		if self.tokens.front() == 'break':
			self.tokens.pop()
			return AstNode('break')

		if self.tokens.front() == 'continue':
			self.tokens.pop()
			return AstNode('continue')

		return None

	# FUNDEF := fun VAR ([VAR {,VAR}]) CMD
	def fundef(self):
		if self.tokens.front() == 'fun':
			self.tokens.pop()
			name = self.build('var', accept_fail=False)

			args_body = []
			self.tokens.pop(expected='(')
			arg = self.build('var')
			if arg:
				args_body.append(arg)
				while self.tokens.front() == ',':
					self.tokens.pop()
					arg = self.build('var', accept_fail=False)
					args_body.append(arg)

			self.tokens.pop(expected=')')

			body = self.build('cmd', accept_fail=False)
			# body goes last in children list
			args_body.append(body)

			return AstNode('fundef', args_body, name.payload)
		return None

	# FUNCALL := VAR ([EXPR {,EXPR}])
	def funcall(self):
		name = self.build('var')
		if name and self.tokens.front() == '(':
			self.tokens.pop()
			args = []
			arg = self.build('expr')
			if arg:
				args.append(arg)
				while self.tokens.front() == ',':
					self.tokens.pop()
					arg = self.build('expr', accept_fail=False)
					args.append(arg)
			self.tokens.pop(expected=')')

			return AstNode('funcall', args, name.payload)
		return None

	# CMD := STATEMENT;|CONTROL;|IF|WHILE|FOR|FUNDEF|'{'CMDLIST'}'
	def cmd(self):
		cmd = self.build('statement')
		if not cmd:
			cmd = self.build('control')
		if cmd:
			self.tokens.pop(expected=';')
			return cmd

		cmd = self.build('if_statement')
		if not cmd:
			cmd = self.build('while_loop')
			if not cmd:
				cmd = self.build('for_loop')
				if not cmd:
					cmd = self.build('fundef')
					if not cmd:
						cmd = self.build_braced('{', 'cmdlist', '}')

		return cmd

	# CMDLIST := {CMD}
	def cmdlist(self):
		cmdlist = []
		cmd = self.build('cmd')
		while cmd:
			cmdlist.append(cmd)
			cmd = self.build('cmd')
		return AstNode('cmdlist', cmdlist)


def build_ast(source):
	tokens = cuscus.lexer.tokenize(source)
	token_stack = TokenStack(tokens)
	return AstBuilder().build_ast(token_stack)
