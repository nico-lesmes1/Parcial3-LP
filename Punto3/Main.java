import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.*;

import java.io.File;

public class Main {
    public static void main(String[] args) throws Exception {
        String ruta = "entrada.txt";
        boolean usarBloque = false;
        int tile = 32;
        if (args.length >= 1) ruta = args[0];
        if (args.length >= 2) usarBloque = Boolean.parseBoolean(args[1]);
        if (args.length >= 3) tile = Integer.parseInt(args[2]);

        CharStream input = CharStreams.fromFileName(ruta);
        MatrixCalcLexer lexer = new MatrixCalcLexer(input);
        CommonTokenStream tokens = new CommonTokenStream(lexer);
        MatrixCalcParser parser = new MatrixCalcParser(tokens);

        parser.removeErrorListeners();
        parser.addErrorListener(new BaseErrorListener() {
            @Override
            public void syntaxError(Recognizer<?, ?> recognizer, Object offendingSymbol,
                                    int line, int charPositionInLine, String msg, RecognitionException e) {
                System.err.printf("Error sintáctico en línea %d:%d - %s%n", line, charPositionInLine, msg);
            }
        });

        ParseTree tree = parser.programa();
        EvalVisitor visitor = new EvalVisitor(usarBloque, tile);
        visitor.visit(tree);

        System.out.println("\nEstado final de variables:");
        visitor.getTabla().forEach((k, v) -> {
            System.out.print(k + " = ");
            if (v instanceof ScalarValue) {
                System.out.println(((ScalarValue) v).toString() + " (escalar " + v.tipoElemento() + ")");
            } else if (v instanceof MatrixValue) {
                MatrixValue mv = (MatrixValue) v;
                System.out.println("Matriz " + mv.matriz.filas + "x" + mv.matriz.columnas + " tipo " + mv.tipoElemento());
                System.out.println(mv.toString());
            } else {
                System.out.println(v);
            }
        });
    }
}