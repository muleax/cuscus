### Cuscus programming language
Just for fun.

##### BNF-Grammar
```
S           := CMDLIST
CMDLIST     := {CMD}
CMD         := STATEMENT;|CONTROL;|IF|WHILE|FOR|FUNDEF|'{'CMDLIST'}'
IF          := if (EXPR) CMD [else CMD]
WHILE       := while (EXPR) CMD
FOR         := for (STATEMENT; EXPR; STATEMENT) CMD
CONTROL     := return[EXPR]|break|continue
STATEMENT   := ASSIGN|PRINT|EXPR
PRINT       := print EXPR
ASSIGN      := VAR = EXPR
EXPR        := LOGIC [? EXPR : EXPR]  
LOGIC       := CMPADD [&&||| LOGIC]
CMPADD      := ADD [==|!=|>|>=|<|<= ADD]
ADD         := SUB [+ ADD]
SUB         := MULDIV {- MULDIV}
MULDIV      := UNIT [*|/|% MULDIV]
UNIT        := FUNCALL|NUM|VAR|NEG|BOOL|(EXPR)
BOOL        := bool'('EXPR')'
NEG         := -UNIT
VAR         := a-z|_ {a-z|0-9|_} except print, while, for, if, else
NUM         := 1-9 {0-9}
FUNDEF      := fun VAR ([VAR {,VAR}]) CMD
FUNCALL     := VAR ([EXPR {,EXPR}])
```

##### Example syntax
```
// define a function
fun factorial(n)
{
    if (n <= 1)
        return 1;
    else
        return n * factorial(n - 1);
}

// print 5!
print factorial(5);

// calculate and print an expression
x = 20;
y = 33;
print (y-x) * 2 - y + 17;

// for loop
for (i = 0; i < 5; i = i+1)
{
    print i;
    if (i == 2)
        break;
}

// while loop
i = 0;
while (i < 10)
{
    if (i % 2)
    {
        i = i + 1;
        continue;
    }

    print factorial(i);
    i = i + 1;
}
```
