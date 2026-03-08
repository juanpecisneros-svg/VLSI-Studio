# Práctica Integradora — Unidad IV
## Python para VLSI | Maestría en Diseño Electrónico y de Circuitos Integrados
**UAA — Centro de Ciencias Básicas / Sistemas Electrónicos**  
Periodo: Febrero–Marzo 2026 | Materia: Python para VLSI

---

## Contexto

Durante la Unidad IV has aprendido a construir interfaces gráficas con Tkinter, organizar layouts complejos con `grid()` y `LabelFrame`, aplicar resaltado de sintaxis con tags en el widget `Text`, y ejecutar procesos externos desde Python con `subprocess` dentro de hilos separados con `threading`.

El código base que se te entrega (`vlsi_studio_base.py`) es una aplicación funcional parcialmente completa que ya incluye:

- Interfaz gráfica oscura con panel lateral de parámetros
- Generación de código Verilog de un sumador (módulo + testbench)
- Guardado de archivos `.v`
- Estructura de pestañas (`Notebook`) con editor y consola
- Función `_ejecutar_cmd()` lista para usarse
- Las funciones `_compilar()` y `_simular()` marcadas con `messagebox` como marcadores de posición (`placeholders`) que debes reemplazar

Tu tarea es **completar y extender** esta aplicación en tres módulos independientes.

---

## Instrucciones Generales

- Trabaja directamente sobre el archivo `vlsi_studio_base.py` que se te entrega.
- No cambies los nombres de los métodos existentes.
- Puedes añadir métodos auxiliares privados (con prefijo `_`).
- Todo el código nuevo debe integrarse sin romper lo que ya funciona.
- Entrega un **único archivo `.py`** con tu nombre en el encabezado.

---

## Módulo 1 — Selector de Compilador

### Descripción

Actualmente la aplicación solo contempla `iverilog` como compilador, pero en entornos profesionales se utiliza también ModelSim (`vsim`). Tu tarea es:

### Tareas específicas

**1.1 — Agregar el `Combobox` de selección de compilador**

En el panel izquierdo, dentro de la sección `ACCIONES` (o inmediatamente antes), agrega:
- Un `Label` con el texto `"Compilador:"`
- Un `Combobox` con las opciones: `["iverilog (Icarus)", "vsim (ModelSim)"]`
- Valor por defecto: `"iverilog (Icarus)"`
- Guarda la selección en una variable de instancia `self.var_compilador`

**1.2 — Modificar `_compilar()`**

Elimina el `messagebox` de marcador y reemplaza el cuerpo de la función para que:

- Lea el valor de `self.var_compilador`
- Si el usuario seleccionó **iverilog**:
  ```
  iverilog -o sim_<nombre> tb_<nombre>.v <nombre>.v
  ```
- Si el usuario seleccionó **vsim**:
  ```
  vlib work
  vlog <nombre>.v tb_<nombre>.v
  ```
- En ambos casos usa `threading.Thread` + `_ejecutar_cmd()` (ya implementada).
- Si el ejecutable no está en el PATH, `_ejecutar_cmd()` ya captura el `FileNotFoundError` y muestra el error en la consola. Verifica que el mensaje de error indique claramente **cuál** compilador falta y cómo instalarlo.

**1.3 — Verificación previa de archivos**

Antes de lanzar la compilación, verifica que los archivos `.v` existan en el directorio de trabajo. Si no existen, muestra un `messagebox.showerror` claro indicando que primero deben guardarse.

---

## Módulo 2 — Simulación con Consola y GTKWave

### Descripción

La función `_simular()` actualmente solo muestra un `messagebox`. Debes implementarla completamente para ejecutar la simulación y opcionalmente abrir GTKWave.

### Tareas específicas

**2.1 — Completar `_simular()`**

Elimina el `messagebox` de marcador y reemplaza el cuerpo para que:

- Determine cuál simulador usar según el compilador seleccionado en `self.var_compilador`:
  - **iverilog → vvp**: `vvp sim_<nombre>`
  - **vsim → vsim**: `vsim -c work.tb_<nombre> -do "run -all; quit"`
- Verifique que el ejecutable de simulación existe antes de correr.
- Use `threading.Thread` + `_ejecutar_cmd()` para no bloquear la GUI.
- Cambie automáticamente a la pestaña `"Consola"` al iniciar.

**2.2 — Apertura automática de GTKWave**

Después de la simulación (si se generó el VCD):
- Si `self.var_vcd.get()` es `True`, intenta abrir GTKWave:
  ```
  gtkwave tb_<nombre>.vcd
  ```
- Usa `subprocess.Popen` (no `run`) para que GTKWave abra de forma no bloqueante.
- Si GTKWave no está instalado, muestra en la consola un mensaje con tag `"error"` indicando cómo instalarlo, pero **no interrumpas** el flujo del programa.

**2.3 — Indicadores visuales en consola**

La consola ya tiene tags `"ok"`, `"error"` e `"info"`. Úsalos apropiadamente:
- Verde (`"ok"`): simulación completada sin errores.
- Rojo (`"error"`): fallo de compilación, timeout o herramienta no encontrada.
- Azul (`"info"`): inicio de proceso, comandos ejecutados.

**Nota:** Recuerda configurar los tags de color en la consola tal como se hace con `_setup_tags()` para los editores. La consola no tiene esos tags por defecto.

---

## Módulo 3 — Segundo Sumador

### Descripción

Actualmente la aplicación solo genera un sumador tipo `ripple_carry` (suma directa con `assign`). Debes agregar soporte para un segundo tipo de sumador seleccionado por el usuario.

### Tareas específicas

**3.1 — Elegir e implementar un segundo tipo de sumador**

Elige **uno** de los siguientes e impleméntalo en Verilog dentro de Python (como string generado dinámicamente):

**Opción A — Carry Lookahead Adder (CLA)**  
Genera el código de un CLA de N bits usando las ecuaciones de propagación (`P`) y generación (`G`):
```
G[i] = a[i] & b[i]
P[i] = a[i] ^ b[i]
C[i+1] = G[i] | (P[i] & C[i])
S[i] = P[i] ^ C[i]
```

**Opción B — Carry Select Adder**  
Genera dos sumadores de N/2 bits (uno con cin=0, otro con cin=1) y usa un mux para seleccionar el resultado correcto según el carry del bloque inferior.

**Opción C — Carry Save Adder**  
Implementa el CSA de tres operandos que reduce `{a, b, c}` a dos vectores `{sum, carry}` usando XOR y AND por bit.

El módulo Verilog generado debe ser **parametrizable en N bits** igual que el sumador original.

**3.2 — Testbench para el segundo sumador**

Genera también un testbench para el segundo sumador. Este testbench debe:
- Usar el mismo esquema de tests aleatorios que el testbench del sumador simple.
- Verificar el resultado contra la referencia `a + b (+cin)`.
- Generar su propio archivo `.vcd` si la opción está activada.

**3.4 — Integrar en `_generar()`**

Modifica `_generar()` para que también genere y muestre el código del segundo sumador en sus nuevas pestañas.

**3.5 — Integrar en `_guardar_archivos()`**

Modifica `_guardar_archivos()` para que guarde también los dos archivos nuevos.

---

## Tips y Orientación

### Sobre el `Combobox` del compilador

```python
# Agrega esto en _construir_panel_izq(), antes de los botones
lbl("Compilador:")
self.var_compilador = tk.StringVar(value="iverilog (Icarus)")
ttk.Combobox(parent,
             textvariable=self.var_compilador,
             values=["iverilog (Icarus)", "vsim (ModelSim)"],
             state="readonly", width=17).pack(padx=12, anchor="w", pady=(0,4))
```

### Cómo saber qué compilador está seleccionado

```python
def _compilar(self):
    nombre, n, _ = self._get_params()
    if nombre is None:
        return

    d   = self.dir_trabajo.get()
    mod = os.path.join(d, f"{nombre}.v")
    tb  = os.path.join(d, f"tb_{nombre}.v")
    out = os.path.join(d, f"sim_{nombre}")

    # Verificar que los archivos existen
    if not os.path.exists(mod) or not os.path.exists(tb):
        messagebox.showerror("Error", "Archivos .v no encontrados. Guarda primero.")
        return

    compilador = self.var_compilador.get()

    if "iverilog" in compilador:
        cmd = ["iverilog", "-o", out, tb, mod]
    else:  # vsim
        # ModelSim requiere dos comandos: vlib + vlog
        # Tip: puedes encadenarlos en _ejecutar_cmd o ejecutarlos secuencialmente
        cmd = ["vlog", mod, tb]   # simplificado

    self._log(f"\n$ {' '.join(cmd)}", "info")
    threading.Thread(
        target=self._ejecutar_cmd,
        args=(cmd, d, out if "iverilog" in compilador else None),
        daemon=True
    ).start()
    self.nb.select(2)
```

### Cómo abrir GTKWave de forma no bloqueante

```python
import subprocess

def _abrir_gtkwave(self, nombre, d):
    vcd_path = os.path.join(d, f"tb_{nombre}.vcd")
    if not os.path.exists(vcd_path):
        self._log("  Archivo VCD no encontrado, omitiendo GTKWave.", "error")
        return
    try:
        subprocess.Popen(["gtkwave", vcd_path])   # Popen: no bloquea
        self._log("  GTKWave abierto.", "ok")
    except FileNotFoundError:
        self._log(
            "  GTKWave no encontrado en PATH.\n"
            "  Instala con: sudo apt install gtkwave  (Linux)\n"
            "  o descarga en: https://gtkwave.sourceforge.net/",
            "error"
        )
```

### Tags de color en la consola

La consola no tiene los tags de color configurados por defecto. Agrégalos al final de `_construir_panel_der()`:

```python
# Después de crear self.txt["consola"]
self.txt["consola"].tag_configure("error", foreground="#FF5252")
self.txt["consola"].tag_configure("ok",    foreground="#69F0AE")
self.txt["consola"].tag_configure("info",  foreground="#40C4FF")
```

### Estructura del Carry Lookahead Adder en Verilog

```verilog
// Pista: estructura general del CLA de N bits (usa generate o always)
module cla_adder #(parameter N = 4)(
    input  [N-1:0] a, b,
    input          cin,
    output [N-1:0] sum,
    output         cout
);
    wire [N-1:0] G, P, C;

    assign G = a & b;           // Generate
    assign P = a ^ b;           // Propagate
    assign C[0] = cin;
    // C[i+1] = G[i] | (P[i] & C[i])  — esto lo completas tú
    assign sum = P ^ C;
    assign cout = G[N-1] | (P[N-1] & C[N-1]);
endmodule
```

### Buenas prácticas

- **Nunca modifiques widgets desde un hilo secundario.** Usa `self.root.after(0, callback)` para devolver resultados al hilo principal. La función `_log()` ya hace esto correctamente, úsala siempre.
- **Reutiliza `_ejecutar_cmd()`.** Ya maneja `FileNotFoundError`, `TimeoutExpired` y el código de retorno. No dupliques esa lógica.
- **Prueba cada módulo por separado** antes de integrarlo con los demás.
- **Documenta con comentarios** qué hace cada función que agregues.

---

## Entregables

| Archivo | Descripción |
|---|---|
| `vlsi_studio_<apellido>.py` | Código Python completo con los tres módulos implementados |

Fecha de entrega: **Domingo 15 de marzo del 2026 a mas tardar a las 9:00 pm**

---

*Python para VLSI — Unidad IV | UAA 2026*
