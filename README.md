#### BNF-Grammar
```
S           := CMDLIST
CMDLIST     := {CMD}
CMD         := STATEMENT;|IF|WHILE|FOR|FUNDEF|'{'CMDLIST'}'
IF          := if (EXPR) CMD [else CMD]
WHILE       := while (EXPR) CMD
FOR         := for (STATEMENT; EXPR; STATEMENT) CMD
STATEMENT   := ASSIGN|PRINT|EXPR
PRINT       := print EXPR
ASSIGN      := VAR = EXPR
EXPR        := LOGIC [? EXPR : EXPR]  
LOGIC       := CMPADD [&&||| LOGIC]
CMPADD      := ADD [==|!=|>|>=|<|<= ADD]
ADD         := SUB [+ ADD]
SUB         := MULDIV {- MULDIV}
MULDIV      := UNIT [*|/|% MULDIV]
UNIT        := NUM|VAR|NEG|BOOL|FUNCALL|(EXPR)
BOOL        := bool'('EXPR')'
NEG         := -UNIT
VAR         := a-z|_ {a-z|0-9|_} except print, while, for, if, else
NUM         := 1-9 {0-9}
VARLIST     := VAR {,VAR}
FUNDEF      := fun (VARLIST) CMD
FUNCALL     := VAR (VARLIST)
```
