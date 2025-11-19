// MatrixValue.java
public class MatrixValue implements Value {
    public final Matriz matriz;

    public MatrixValue(Matriz matriz) {
        this.matriz = matriz;
    }

    @Override
    public boolean isScalar() { return false; }
    @Override
    public boolean isMatrix() { return true; }
    @Override
    public String tipoElemento() { return matriz.tipoElemento; }

    @Override
    public String toString() {
        return matriz.toString();
    }
}