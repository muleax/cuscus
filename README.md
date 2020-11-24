#### BNF-Grammar
```
S           := BLOCKLIST
WHILE       := while (EXPR) BLOCK  
IF          := if (EXPR) BLOCK [else BLOCK]  
BLOCKLIST   := {BLOCK}  
BLOCK       := CMD|IF|WHILE|'{'BLOCKLIST'}'  
CMD         := ASSIGN|PRINT  
PRINT       := print EXPR  
ASSIGN      := VAR = EXPR  
EXPR        := LOGIC [? EXPR : EXPR]  
LOGIC       := CMPADD [&&||| LOGIC]  
CMPADD      := ADD [==|>|>=|<|<= ADD]  
ADD         := SUB [+ ADD]  
SUB         := MULDIV {- MULDIV}  
MULDIV      := UNIT [\*|/ MULDIV]  
UNIT        := NUM|VAR|NEG|BOOL|'('EXPR')'  
NEG         := -UNIT  
BOOL        := bool'('EXPR')'  
VAR         := a-z {a-z|0-9|\_} except print, while, if, else  
NUM         := 1-9 {0-9}  
```
