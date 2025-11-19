import java.util.Arrays;

public class Matriz {
    public final int filas;
    public final int columnas;
    private final double[] datos;
    public String tipoElemento; 

    public Matriz(int filas, int columnas, String tipoElemento) {
        this.filas = filas;
        this.columnas = columnas;
        this.tipoElemento = tipoElemento;
        this.datos = new double[filas * columnas];
    }

    public Matriz(int filas, int columnas, String tipoElemento, double[] datos) {
        if (datos.length != filas * columnas) {
            throw new IllegalArgumentException("Longitud de datos no coincide con dimensiones");
        }
        this.filas = filas;
        this.columnas = columnas;
        this.tipoElemento = tipoElemento;
        this.datos = Arrays.copyOf(datos, datos.length);
    }

    public double get(int i, int j) {
        return datos[i * columnas + j];
    }

    public void set(int i, int j, double val) {
        datos[i * columnas + j] = val;
    }

    public double[] datos() {
        return datos;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        for (int i = 0; i < filas; i++) {
            sb.append("[");
            for (int j = 0; j < columnas; j++) {
                double v = get(i, j);
                if ("entero".equals(tipoElemento)) {
                    sb.append((int) v);
                } else {
                    sb.append(v);
                }
                if (j < columnas - 1) sb.append(", ");
            }
            sb.append("]");
            if (i < filas - 1) sb.append(", ");
        }
        sb.append("]");
        return sb.toString();
    }

    public static Matriz crearCeros(int filas, int columnas, String tipoElemento) {
        return new Matriz(filas, columnas, tipoElemento);
    }

    public Matriz transpose() {
        Matriz t = new Matriz(columnas, filas, this.tipoElemento);
        for (int i = 0; i < filas; i++) {
            for (int j = 0; j < columnas; j++) {
                t.set(j, i, this.get(i, j));
            }
        }
        return t;
    }

    public static Matriz matmulTranspose(Matriz A, Matriz B) {
        if (A.columnas != B.filas) {
            throw new IllegalArgumentException(
                String.format("Dimensiones incompatibles para multiplicación: cols(A)=%d != filas(B)=%d", A.columnas, B.filas));
        }
        String tipoRes = promoverTipo(A.tipoElemento, B.tipoElemento);
        if (tipoRes == null) {
            throw new IllegalArgumentException("Tipos de elemento incompatibles: " + A.tipoElemento + " vs " + B.tipoElemento);
        }
        Matriz BT = B.transpose();
        int m = A.filas;
        int p = B.columnas;
        int n = A.columnas;
        Matriz C = new Matriz(m, p, tipoRes);
        for (int i = 0; i < m; i++) {
            int offA = i * A.columnas;
            for (int j = 0; j < p; j++) {
                int offBT = j * BT.columnas; // BT.columnas == B.filas == n
                double s = 0;
                for (int k = 0; k < n; k++) {
                    double a = A.datos()[offA + k];
                    double b = BT.datos()[offBT + k];
                    s += a * b;
                }
                if ("entero".equals(tipoRes)) {
                    C.datos()[i * p + j] = (int) Math.round(s);
                } else {
                    C.datos()[i * p + j] = s;
                }
            }
        }
        return C;
    }

    public static Matriz matmulBlock(Matriz A, Matriz B, int tile) {
        if (A.columnas != B.filas) {
            throw new IllegalArgumentException(
                String.format("Dimensiones incompatibles para multiplicación: cols(A)=%d != filas(B)=%d", A.columnas, B.filas));
        }
        String tipoRes = promoverTipo(A.tipoElemento, B.tipoElemento);
        if (tipoRes == null) {
            throw new IllegalArgumentException("Tipos de elemento incompatibles: " + A.tipoElemento + " vs " + B.tipoElemento);
        }
        int m = A.filas;
        int n = A.columnas;
        int p = B.columnas;
        Matriz C = new Matriz(m, p, tipoRes);
        for (int ii = 0; ii < m; ii += tile) {
            for (int jj = 0; jj < p; jj += tile) {
                for (int kk = 0; kk < n; kk += tile) {
                    int iLim = Math.min(ii + tile, m);
                    int jLim = Math.min(jj + tile, p);
                    int kLim = Math.min(kk + tile, n);
                    for (int i = ii; i < iLim; i++) {
                        for (int k = kk; k < kLim; k++) {
                            double a = A.get(i, k);
                            int baseC = i * p;
                            int baseB = k * p;
                            for (int j = jj; j < jLim; j++) {
                                C.datos()[baseC + j] += a * B.datos()[baseB + j];
                            }
                        }
                    }
                }
            }
        }
        if ("entero".equals(tipoRes)) {
            for (int i = 0; i < C.datos().length; i++) {
                C.datos()[i] = Math.round(C.datos()[i]);
            }
        }
        return C;
    }

    public static String promoverTipo(String t1, String t2) {
        if (t1.equals(t2)) return t1;
        if ((t1.equals("entero") && t2.equals("flotante")) || (t1.equals("flotante") && t2.equals("entero"))) return "flotante";
        return null;
    }
}