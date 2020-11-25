import string
from cuscus.definition import *

OPS_TOKENS = set(ADDSUB_OPS + MULDIV_OPS + CMP_OPS + LOGIC_OPS + MICS_OPS)

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
