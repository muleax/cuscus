from copy import deepcopy
from functools import partial
import cuscus.ast

# Ast node name -> operator name
OPERATIONS = {
	'num':		'num',
	'var':		'var',
	'print':	'print',
	'=': 		'assign',
	'bool':		'bool',
	'neg':		'neg',
	'+':		'add',
	'-':		'sub',
	'*':		'mul',
	'/':		'div',
	'%':		'mod',
	'ternary':	'ternary',
	'==':		'eq',
	'!=':		'ne',
	'>':		'gt',
	'>=':		'ge',
	'<':		'lt',
	'<=':		'le',
	'&&':		'and_op',
	'||':		'or_op',
	'if':		'if_statement',
	'while':	'while_loop',
	'for':		'for_loop',
	'return':	'return_cmd',
	'break':	'break_cmd',
	'continue':	'continue_cmd',
	'fundef':	'fundef',
	'funcall':	'funcall',
	'cmdlist':	'cmdlist'
}

if set(OPERATIONS.keys()) != cuscus.ast.AST_NODES:
	diff = cuscus.ast.AST_NODES.symmetric_difference(OPERATIONS.keys())
	raise ValueError(f"Inconsistent operation set: {diff}")


class Interpreter:
	def __init__(self):
		pass

	def evaluate_ast(self, ast):
		# create eval function for each node in advance
		ast = deepcopy(ast)
		s = [ast]
		while s:
			node = s.pop()
			node.eval = partial(getattr(self, OPERATIONS[node.type]), node)
			if node.children:
				s += node.children

		self.scope_stack = [{}]
		self.fundef_scope = {}
		self.control_signal = None
		self.retval = None
		return ast.eval()

	def num(self, node):
		return node.payload
	
	def var(self, node):
		for scope in reversed(self.scope_stack):
			ret = scope.get(node.payload)
			if ret is not None:
				return ret
		raise ValueError(f"Variable {node.payload} is not defined")
	
	def print(self, node):
		print(' '.join(str(child.eval()) for child in node.children))
	
	def assign(self, node):
		self.scope_stack[-1][node.payload] = node.children[0].eval()

	def fundef(self, node):
		self.fundef_scope[node.payload] = node

	def funcall(self, node):
		fun = self.fundef_scope.get(node.payload)
		if fun is None:
			raise ValueError(f"Function {node.payload} is not defined")

		args_body = fun.children
		if len(args_body) - 1 != len(node.children):
			raise ValueError(f"Function {node.payload} requires {len(args_body) - 1} arguments, {len(node.children)} given")

		fun_scope = {}
		for name, expr in zip(args_body, node.children):
			fun_scope[name.payload] = expr.eval()

		self.scope_stack.append(fun_scope)
		args_body[-1].eval()
		self.scope_stack.pop()

		ret = self.retval
		self.retval = None
		self.control_signal = None
		return ret

	def cmdlist(self, node):
		for child in node.children:
			child.eval()
			if self.control_signal:
				break

	def ternary(self, node):
		cond, true_expr, false_expr = node.children
		if cond.eval():
			return true_expr.eval()
		else:
			return false_expr.eval()
	
	def eq(self, node):
		l, r = node.children
		return l.eval() == r.eval()
	
	def ne(self, node):
		l, r = node.children
		return l.eval() != r.eval()
	
	def gt(self, node):
		l, r = node.children
		return l.eval() > r.eval()
	
	def ge(self, node):
		l, r = node.children
		return l.eval() >= r.eval()
	
	def lt(self, node):
		l, r = node.children
		return l.eval() < r.eval()
	
	def le(self, node):
		l, r = node.children
		return l.eval() <= r.eval()

	def and_op(self, node):
		l, r = node.children
		return l.eval() and r.eval()
	
	def or_op(self, node):
		l, r = node.children
		return l.eval() or r.eval()
	
	def if_statement(self, node):
		children = node.children
		if children[0].eval():
			children[1].eval()
		elif len(children) == 3:
			children[2].eval()
	
	def while_loop(self, node):
		cond, body = node.children
		while cond.eval():
			body.eval()

			if self.control_signal:
				if self.control_signal == 'continue':
					self.control_signal = None
					continue
				elif self.control_signal == 'break':
					self.control_signal = None
					break
				else:  # return
					break
	
	def for_loop(self, node):
		init, cond, inc, body = node.children
		init.eval()
		while cond.eval():
			body.eval()

			if self.control_signal:
				if self.control_signal == 'continue':
					self.control_signal = None
					inc.eval()
					continue
				elif self.control_signal == 'break':
					self.control_signal = None
					break
				else:  # return
					break

			inc.eval()

	def return_cmd(self, node):
		if node.children:
			self.retval = node.children[0].eval()
		self.control_signal = 'return'

	def break_cmd(self, node):
		self.control_signal = 'break'

	def continue_cmd(self, node):
		self.control_signal = 'continue'

	def bool(self, node):
		return bool(node.children[0].eval())
	
	def neg(self, node):
		return -node.children[0].eval()
	
	def add(self, node):
		l, r = node.children
		return l.eval() + r.eval()
	
	def sub(self, node):
		children = node.children
		ret = children[0].eval()
		for i in range(1, len(children)):
			ret -= children[i].eval()
		return ret
	
	def mul(self, node):
		l, r = node.children
		return l.eval() * r.eval()
	
	def div(self, node):
		l, r = node.children
		divisor = r.eval()
		if divisor == 0:
			raise ValueError("Interpreter: division by zero")
		return l.eval() / divisor
	
	def mod(self, node):
		l, r = node.children
		divisor = r.eval()
		if divisor == 0:
			raise ValueError("Interpreter: division by zero")
		return l.eval() % divisor


def evaluate(source):
	ast = cuscus.ast.build_ast(source)
	return Interpreter().evaluate_ast(ast)
