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

<img width="801" height="181" alt="imagen" src="https://github.com/user-attachments/assets/65c41866-3a96-4d56-a671-7c1b1302cf69" />



