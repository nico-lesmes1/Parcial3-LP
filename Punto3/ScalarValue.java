// ScalarValue.java
public class ScalarValue implements Value {
    public final String tipo; // "entero" o "flotante" o "cadena" (si más adelante)
    public final double valor; // almacenamos en double para uniformidad

    public ScalarValue(String tipo, double valor) {
        this.tipo = tipo;
        this.valor = valor;
    }

    @Override
    public boolean isScalar() { return true; }
    @Override
    public boolean isMatrix() { return false; }
    @Override
    public String tipoElemento() { return tipo; }

    @Override
    public String toString() {
        if ("entero".equals(tipo)) {
            return Integer.toString((int) Math.round(valor));
        } else {
            return Double.toString(valor);
        }
    }
}