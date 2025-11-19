# Ejecución del codigo en Linux

1. 
```
export ANTLR_JAR="$PWD/antlr-4.13.2-complete.jar"
```
2. 
```
java -jar "$ANTLR_JAR" -visitor MatrixCalc.g4
```
3.
```
javac -cp ".:$ANTLR_JAR" *.java
```
4.
```
java -cp ".:$ANTLR_JAR" Main entrada.txt
```

## Ejecución en Ubuntu
