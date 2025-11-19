import java.util.*;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.TerminalNode;

public class EvalVisitor extends MatrixCalcBaseVisitor<Value> {

    private final Map<String, Value> tabla = new HashMap<>();

    private final boolean usarBloque;
    private final int tileSize;

    public EvalVisitor() {
        this(false, 32);
    }

    public EvalVisitor(boolean usarBloque, int tileSize) {
        this.usarBloque = usarBloque;
        this.tileSize = tileSize;
    }

    public Map<String, Value> getTabla() {
        return tabla;
    }

    @Override
    public Value visitPrograma(MatrixCalcParser.ProgramaContext ctx) {
        for (MatrixCalcParser.SentenciaContext sctx : ctx.sentencia()) {
            visit(sctx);
        }
        return null;
    }

    @Override
    public Value visitDeclaracion(MatrixCalcParser.DeclaracionContext ctx) {
        String nombre = ctx.IDENT().getText();
        if (ctx.IGUAL() != null && ctx.tipo_anotacion() == null) {
            Value v = visit(ctx.expr());
            if (v instanceof MatrixValue || v instanceof ScalarValue) {
                tabla.put(nombre, v);
            } else {
                System.err.println("Declaración " + nombre + ": tipo desconocido al inicializar");
            }
            return v;
        }
        if (ctx.tipo_anotacion() != null) {
            MatrixCalcParser.Tipo_anotacionContext tctx = ctx.tipo_anotacion();
            if (tctx.MATRIZ() != null) {
                String tipoElem = tctx.tipo_elemento().getText().toLowerCase();
                int filas = Integer.parseInt(tctx.NUMERO(0).getText());
                int columnas = Integer.parseInt(tctx.NUMERO(1).getText());
                if (ctx.IGUAL() != null) {
                    Value v = visit(ctx.expr());
                    if (!(v instanceof MatrixValue)) {
                        System.err.println("Inicialización debe ser una matriz para " + nombre);
                    } else {
                        MatrixValue mv = (MatrixValue) v;
                        if (mv.matriz.filas != filas || mv.matriz.columnas != columnas) {
                            System.err.println(String.format("Inicialización dimensiones no coinciden para %s: se esperaban %dx%d y se obtuvieron %dx%d",
                                    nombre, filas, columnas, mv.matriz.filas, mv.matriz.columnas));
                        } else {
                            if (!mv.matriz.tipoElemento.equals(tipoElem)) {
                                if (mv.matriz.tipoElemento.equals("entero") && tipoElem.equals("flotante")) {
                                    mv.matriz.tipoElemento = "flotante";
                                } else {
                                    System.err.println("No se puede convertir tipo " + mv.matriz.tipoElemento + " a " + tipoElem + " en inicialización de " + nombre);
                                }
                            }
                            tabla.put(nombre, mv);
                        }
                    }
                    return null;
                } else {
                    Matriz M = Matriz.crearCeros(filas, columnas, tipoElem);
                    tabla.put(nombre, new MatrixValue(M));
                    return null;
                }
            } else {
                String tipoSimple = tctx.getText().toLowerCase();
                if (ctx.IGUAL() != null) {
                    Value v = visit(ctx.expr());
                    if (v instanceof ScalarValue) {
                        ScalarValue sv = (ScalarValue) v;
                        double val = sv.valor;
                        if ("entero".equals(tipoSimple)) {
                            val = Math.round(val);
                            tabla.put(nombre, new ScalarValue("entero", val));
                        } else {
                            tabla.put(nombre, new ScalarValue("flotante", val));
                        }
                    } else {
                        System.err.println("Inicialización inválida para escalar " + nombre);
                    }
                    return null;
                } else {
                    if ("entero".equals(tipoSimple)) {
                        tabla.put(nombre, new ScalarValue("entero", 0));
                    } else {
                        tabla.put(nombre, new ScalarValue("flotante", 0.0));
                    }
                    return null;
                }
            }
        }
        System.err.println("Declaración inválida para " + nombre);
        return null;
    }

    @Override
    public Value visitAsignacion(MatrixCalcParser.AsignacionContext ctx) {
        String nombre = ctx.IDENT().getText();
        Value v = visit(ctx.expr());
        if (v == null) return null;
        if (tabla.containsKey(nombre)) {
            Value info = tabla.get(nombre);
            if (info instanceof MatrixValue && v instanceof MatrixValue) {
                MatrixValue old = (MatrixValue) info;
                MatrixValue nv = (MatrixValue) v;
                if (old.matriz.filas != nv.matriz.filas || old.matriz.columnas != nv.matriz.columnas) {
                    System.err.println(String.format("Asignación: dimensiones no coinciden para %s: %dx%d vs %dx%d",
                            nombre, old.matriz.filas, old.matriz.columnas, nv.matriz.filas, nv.matriz.columnas));
                    return null;
                } else {
                    tabla.put(nombre, nv);
                }
            } else if (info instanceof ScalarValue && v instanceof ScalarValue) {
                tabla.put(nombre, v);
            } else {
                System.err.println("Asignación inválida: tipos no coinciden para " + nombre);
            }
        } else {
            tabla.put(nombre, v);
        }
        return v;
    }

    @Override
    public Value visitImprimir(MatrixCalcParser.ImprimirContext ctx) {
        Value v = visit(ctx.expr());
        if (v == null) {
            System.out.println("Imprimir: valor inválido o error");
            return null;
        }
        if (v instanceof ScalarValue) {
            System.out.println(((ScalarValue) v).toString());
        } else if (v instanceof MatrixValue) {
            MatrixValue mv = (MatrixValue) v;
            System.out.println("Matriz " + mv.matriz.filas + " x " + mv.matriz.columnas);
            System.out.println(mv.toString());
        } else {
            System.out.println("Imprimir: valor inválido o error");
        }
        return v;
    }

    @Override
    public Value visitExpr_suma(MatrixCalcParser.Expr_sumaContext ctx) {
        List<MatrixCalcParser.Expr_prodContext> factors = ctx.expr_prod();
        Value acc = visit(factors.get(0));
        for (int i = 1; i < factors.size(); i++) {
            String op = ctx.getChild(2 * i - 1).getText(); // operator token
            Value rhs = visit(factors.get(i));
            if (acc == null || rhs == null) return null;
            if (op.equals("+")) {
                acc = applyAdd(acc, rhs);
            } else {
                acc = applySub(acc, rhs);
            }
        }
        return acc;
    }

    @Override
    public Value visitExpr_prod(MatrixCalcParser.Expr_prodContext ctx) {
        List<MatrixCalcParser.Expr_factorContext> factors = ctx.expr_factor();
        Value acc = visit(factors.get(0));
        for (int i = 1; i < factors.size(); i++) {
            String op = ctx.getChild(2 * i - 1).getText();
            Value rhs = visit(factors.get(i));
            if (acc == null || rhs == null) return null;
            if (op.equals("*")) {
                acc = applyMul(acc, rhs);
            } else if (op.equals("/")) {
                acc = applyDiv(acc, rhs);
            } else if (op.equals("@")) {
                acc = applyMatMul(acc, rhs);
            } else {
                System.err.println("Operador desconocido: " + op);
                return null;
            }
        }
        return acc;
    }

    @Override
    public Value visitUnariaNeg(MatrixCalcParser.UnariaNegContext ctx) {
        Value v = visit(ctx.expr_factor());
        if (v instanceof ScalarValue) {
            ScalarValue s = (ScalarValue) v;
            return new ScalarValue(s.tipo, -s.valor);
        } else {
            System.err.println("Negación solo aplicable a escalares");
            return null;
        }
    }

    @Override
    public Value visitLiteralNumero(MatrixCalcParser.LiteralNumeroContext ctx) {
        String txt = ctx.NUMERO().getText();
        if (txt.contains(".")) {
            double d = Double.parseDouble(txt);
            return new ScalarValue("flotante", d);
        } else {
            int iv = Integer.parseInt(txt);
            return new ScalarValue("entero", iv);
        }
    }

    @Override
    public Value visitLiteralMatriz(MatrixCalcParser.LiteralMatrizContext ctx) {
        MatrixCalcParser.Literal_matrizContext litCtx = ctx.literal_matriz();
        if (litCtx == null) {
            System.err.println("Error interno: literal_matriz no encontrado en el contexto");
            return null;
        }
        List<MatrixCalcParser.FilaContext> filasCtx = litCtx.fila();
        int filas = filasCtx.size();
        int columnas = -1;
        String tipoElem = null;
        double[] flat = null;
        int idx = 0;
        for (int i = 0; i < filas; i++) {
            MatrixCalcParser.FilaContext fctx = filasCtx.get(i);
            List<TerminalNode> nums = fctx.NUMERO();
            if (columnas == -1) {
                columnas = nums.size();
                flat = new double[filas * columnas];
            } else {
                if (nums.size() != columnas) {
                    System.err.println("Literal de matriz no rectangular: fila " + i);
                    return null;
                }
            }
            for (int j = 0; j < nums.size(); j++) {
                String t = nums.get(j).getText();
                double val = t.contains(".") ? Double.parseDouble(t) : Integer.parseInt(t);
                // inferir tipo
                String tElem = t.contains(".") ? "flotante" : "entero";
                if (tipoElem == null) tipoElem = tElem;
                else {
                    String promoted = Matriz.promoverTipo(tipoElem, tElem);
                    if (promoted != null) tipoElem = promoted;
                }
                flat[idx++] = val;
            }
        }
        Matriz M = new Matriz(filas, columnas, tipoElem, flat);
        return new MatrixValue(M);
    }

    @Override
    public Value visitFuncProducto(MatrixCalcParser.FuncProductoContext ctx) {
        Value a = visit(ctx.expr(0));
        Value b = visit(ctx.expr(1));
        return applyMatMul(a, b);
    }

    @Override
    public Value visitReferencia(MatrixCalcParser.ReferenciaContext ctx) {
        String nombre = ctx.IDENT().getText();
        if (!tabla.containsKey(nombre)) {
            System.err.println("Variable no declarada: " + nombre);
            return null;
        }
        return tabla.get(nombre);
    }

    @Override
    public Value visitParenExpr(MatrixCalcParser.ParenExprContext ctx) {
        return visit(ctx.expr());
    }

    private Value applyAdd(Value a, Value b) {
        if (a instanceof ScalarValue && b instanceof ScalarValue) {
            ScalarValue sa = (ScalarValue) a;
            ScalarValue sb = (ScalarValue) b;
            String tipo = Matriz.promoverTipo(sa.tipo, sb.tipo);
            if (tipo == null) { System.err.println("Tipos no compatibles en suma"); return null; }
            double res = sa.valor + sb.valor;
            if ("entero".equals(tipo)) res = Math.round(res);
            return new ScalarValue(tipo, res);
        }
        if (a instanceof MatrixValue && b instanceof MatrixValue) {
            MatrixValue ma = (MatrixValue) a;
            MatrixValue mb = (MatrixValue) b;
            if (ma.matriz.filas != mb.matriz.filas || ma.matriz.columnas != mb.matriz.columnas) {
                System.err.println("Operación entre matrices: dimensiones deben coincidir para suma/resta");
                return null;
            }
            String tipo = Matriz.promoverTipo(ma.matriz.tipoElemento, mb.matriz.tipoElemento);
            if (tipo == null) { System.err.println("Tipos de elementos incompatibles"); return null; }
            Matriz C = new Matriz(ma.matriz.filas, ma.matriz.columnas, tipo);
            for (int i = 0; i < ma.matriz.filas; i++) {
                for (int j = 0; j < ma.matriz.columnas; j++) {
                    double v = ma.matriz.get(i, j) + mb.matriz.get(i, j);
                    C.set(i, j, ("entero".equals(tipo) ? Math.round(v) : v));
                }
            }
            return new MatrixValue(C);
        }
        System.err.println("Suma inválida entre tipos");
        return null;
    }

    private Value applySub(Value a, Value b) {
        if (a instanceof ScalarValue && b instanceof ScalarValue) {
            ScalarValue sa = (ScalarValue) a;
            ScalarValue sb = (ScalarValue) b;
            String tipo = Matriz.promoverTipo(sa.tipo, sb.tipo);
            if (tipo == null) { System.err.println("Tipos no compatibles en resta"); return null; }
            double res = sa.valor - sb.valor;
            if ("entero".equals(tipo)) res = Math.round(res);
            return new ScalarValue(tipo, res);
        }
        if (a instanceof MatrixValue && b instanceof MatrixValue) {
            MatrixValue ma = (MatrixValue) a;
            MatrixValue mb = (MatrixValue) b;
            if (ma.matriz.filas != mb.matriz.filas || ma.matriz.columnas != mb.matriz.columnas) {
                System.err.println("Operación entre matrices: dimensiones deben coincidir para resta");
                return null;
            }
            String tipo = Matriz.promoverTipo(ma.matriz.tipoElemento, mb.matriz.tipoElemento);
            if (tipo == null) { System.err.println("Tipos de elementos incompatibles"); return null; }
            Matriz C = new Matriz(ma.matriz.filas, ma.matriz.columnas, tipo);
            for (int i = 0; i < ma.matriz.filas; i++) {
                for (int j = 0; j < ma.matriz.columnas; j++) {
                    double v = ma.matriz.get(i, j) - mb.matriz.get(i, j);
                    C.set(i, j, ("entero".equals(tipo) ? Math.round(v) : v));
                }
            }
            return new MatrixValue(C);
        }
        System.err.println("Resta inválida entre tipos");
        return null;
    }

    private Value applyMul(Value a, Value b) {
        if (a instanceof ScalarValue && b instanceof ScalarValue) {
            ScalarValue sa = (ScalarValue) a;
            ScalarValue sb = (ScalarValue) b;
            String tipo = Matriz.promoverTipo(sa.tipo, sb.tipo);
            if (tipo == null) { System.err.println("Tipos no compatibles en multiplicación"); return null; }
            double res = sa.valor * sb.valor;
            if ("entero".equals(tipo)) res = Math.round(res);
            return new ScalarValue(tipo, res);
        }
        if (a instanceof ScalarValue && b instanceof MatrixValue) {
            ScalarValue s = (ScalarValue) a;
            MatrixValue Mv = (MatrixValue) b;
            String tipoRes = Matriz.promoverTipo(s.tipo, Mv.matriz.tipoElemento);
            if (tipoRes == null) { System.err.println("Tipos no compatibles escalar*matriz"); return null; }
            Matriz C = new Matriz(Mv.matriz.filas, Mv.matriz.columnas, tipoRes);
            for (int i = 0; i < Mv.matriz.filas; i++) {
                for (int j = 0; j < Mv.matriz.columnas; j++) {
                    double v = Mv.matriz.get(i, j) * s.valor;
                    C.set(i, j, "entero".equals(tipoRes) ? Math.round(v) : v);
                }
            }
            return new MatrixValue(C);
        }
        if (a instanceof MatrixValue && b instanceof ScalarValue) {
            return applyMul(b, a);
        }
        System.err.println("Multiplicación inválida entre tipos con operador *");
        return null;
    }

    private Value applyDiv(Value a, Value b) {
        if (a instanceof ScalarValue && b instanceof ScalarValue) {
            ScalarValue sa = (ScalarValue) a;
            ScalarValue sb = (ScalarValue) b;
            if (sb.valor == 0) { System.err.println("División por cero"); return null; }
            String tipo = Matriz.promoverTipo(sa.tipo, sb.tipo);
            double res = sa.valor / sb.valor;
            return new ScalarValue("flotante", res);
        }
        System.err.println("Division inválida o no soportada para matrices/mezcla");
        return null;
    }

    private Value applyMatMul(Value a, Value b) {
        if (!(a instanceof MatrixValue) || !(b instanceof MatrixValue)) {
            System.err.println("El operador @ requiere dos matrices");
            return null;
        }
        MatrixValue A = (MatrixValue) a;
        MatrixValue B = (MatrixValue) b;
        try {
            Matriz C;
            if (usarBloque) {
                C = Matriz.matmulBlock(A.matriz, B.matriz, tileSize);
            } else {
                C = Matriz.matmulTranspose(A.matriz, B.matriz);
            }
            return new MatrixValue(C);
        } catch (IllegalArgumentException e) {
            System.err.println("Error multiplicación matricial: " + e.getMessage());
            return null;
        }
    }
}