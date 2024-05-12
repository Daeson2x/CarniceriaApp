import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
from datetime import datetime
import subprocess
import os
from tkinter import *
class ConexionDB:
    def __init__(self):
        self.dbname = "proyectoDB"
        self.user = "postgres"
        self.password = "daeson"
        self.host = "localhost"
        self.port = "5432"
        self.conn = self.establecer_conexion()

    def establecer_conexion(self):
        try:
            conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.verificar_y_crear_tablas(conn)
            return conn
        except psycopg2.Error as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos: {e}")
            return None

    def verificar_y_crear_tablas(self, conn):
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id_producto INTEGER PRIMARY KEY UNIQUE,
                    descripcion VARCHAR(100),
                    precio NUMERIC,
                    existencias NUMERIC
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS proveedores (
                    id_proveedores SERIAL PRIMARY KEY,
                    nombre VARCHAR(100),
                    telefono VARCHAR(20),
                    direccion VARCHAR(100)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id_cliente SERIAL PRIMARY KEY,
                    nombre VARCHAR(100),
                    telefono VARCHAR(20),
                    direccion VARCHAR(100)
                )
            """)
            # Crear vistas
            cur.execute("""
                CREATE OR REPLACE VIEW productos_mas_baratos AS
                SELECT descripcion, precio FROM productos WHERE precio <= 150.00
            """)
            
            cur.execute("""
                CREATE OR REPLACE VIEW productos_menos_existencias AS
                SELECT descripcion, existencias FROM productos WHERE existencias <= 10.00
            """)
            
            cur.execute("""
                CREATE OR REPLACE VIEW productos_mayor_existencias AS
                SELECT descripcion, existencias FROM productos WHERE existencias >= 20.00
            """)

            conn.commit()
        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al verificar o crear tablas: {e}")
        finally:
            if cur:
                cur.close()

    def verificar_credenciales(self, username, password):
        if username == "admin" and password == "admin123":
            return True
        else:
            messagebox.showerror("Error de inicio de sesión", "Credenciales incorrectas.")
            return False

class ProductoManager:
    def __init__(self, conn):
        self.conn = conn

    def insertar_producto(self, id_producto, descripcion, precio, existencias):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO productos (id_producto, descripcion, precio, existencias)
                VALUES (%s, %s, %s, %s)
            """, (id_producto, descripcion, float(precio), float(existencias)))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Producto ingresado correctamente.")
        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al insertar el producto: {e}")
        finally:
            if cur:
                cur.close()

class CarniceriaApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("Carniceria App")
        self.geometry("1200x500")
        self.configure(bg="#a22543")
        self.conexion_db = ConexionDB()
        self.usuario_autenticado = False
        self.withdraw()
        self.ventana_inicio_sesion()

    def ventana_inicio_sesion(self):
        self.login_window = tk.Toplevel(self)
        self.login_window.title("Inicio de Sesión")
        self.login_window.geometry("300x150")
        self.login_window.configure(bg="#f0f0f0")
        self.style = ttk.Style()
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("TButton", background="#e8090d", foreground="black")
        ttk.Label(self.login_window, text="Usuario:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.login_window, font=("Arial", 12))
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(self.login_window, text="Contraseña:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.login_window, show="*", font=("Arial", 12))
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.login_window, text="Iniciar Sesión", command=self.verificar_credenciales).grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    def verificar_credenciales(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if self.conexion_db.verificar_credenciales(username, password):
            self.usuario_autenticado = True
            self.login_window.destroy()
            self.iniciar_app()
        else:
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)

    def iniciar_app(self):
        if self.usuario_autenticado:
            self.create_menu()
            self.deiconify()

    def create_menu(self):
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        # Menu ventas
        ventas_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Venta", menu=ventas_menu)
        ventas_menu.add_command(label="Nota de Venta")

        # Menú Productos
        productos_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Productos", menu=productos_menu)

        # Submenú para Mostrar Productos
        mostrar_productos_submenu = tk.Menu(productos_menu, tearoff=0)
        productos_menu.add_cascade(label="Mostrar Productos", menu=mostrar_productos_submenu)
        mostrar_productos_submenu.add_command(label="Mostrar todos los productos", command=self.mostrar_productos)
        mostrar_productos_submenu.add_command(label="Productos más baratos", command=self.mostrar_productos_mas_baratos)
        mostrar_productos_submenu.add_command(label="Productos con menos existencias", command=self.mostrar_productos_menos_existencias)
        mostrar_productos_submenu.add_command(label="Productos con mayores existencias", command=self.mostrar_productos_mayor_existencias)

        productos_menu.add_command(label="Ingresar Producto", command=self.insertar_producto)
        productos_menu.add_command(label="Modificar Producto", command=self.modificar_producto)
        productos_menu.add_command(label="Eliminar Producto", command=self.eliminar_producto)

        # Menú Clientes
        clientes_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Clientes", menu=clientes_menu)
        clientes_menu.add_command(label="Mostrar Clientes", command=self.mostrar_clientes)
        clientes_menu.add_command(label="Ingresar Cliente", command=self.registrar_cliente)
        clientes_menu.add_command(label="Modificar Cliente", command=self.modificar_cliente)
        clientes_menu.add_command(label="Eliminar Cliente", command=self.eliminar_cliente)

        # Menu Proveedores
        proveedores_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Proveedores", menu=proveedores_menu)
        proveedores_menu.add_command(label="Mostrar Proveedor", command=self.mostrar_proveedor)
        proveedores_menu.add_command(label="Ingresar Proveedor", command=self.registrar_proveedor)
        proveedores_menu.add_command(label="Modificar Proveedor", command=self.modificar_proveedor)
        proveedores_menu.add_command(label="Eliminar Proveedor", command=self.eliminar_proveedor)

        # Menu Backups
        backup_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Backups", menu=backup_menu)
        backup_menu.add_command(label="Crear Respaldo", command=self.crear_respaldo)
        backup_menu.add_command(label="Restaurar respaldo", command=self.restaurar_respaldo)

        self.imagen = tk.PhotoImage(file="logo.png")
        self.imagen_resized = self.imagen.subsample(2, 2)  # Redimensionar la imagen a la mitad
        self.label_imagen = tk.Label(self, image=self.imagen_resized)
        self.label_imagen.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.btn_cerrar_sesion = ttk.Button(self, text="Cerrar Sesión", command=self.cerrar_sesion)
        self.btn_cerrar_sesion.place(relx=0.5, rely=0.95, anchor="center")

        
    def insertar_producto(self):
        if self.usuario_autenticado:
            if hasattr(self, "ventana_ingreso_producto"):
                self.ventana_ingreso_producto.deiconify()  # Si ya existe la ventana, mostrarla
            else:
                self.ventana_ingreso_producto = tk.Toplevel(self)
                self.ventana_ingreso_producto.title("Ingresar Producto")
                self.ventana_ingreso_producto.geometry("300x200")
                self.ventana_ingreso_producto.configure(bg="#f0f0f0")

                etiquetas = ["ID Producto:", "Descripción:", "Precio:", "Existencias:"]
                entradas = []
                for i, label_text in enumerate(etiquetas):
                    ttk.Label(self.ventana_ingreso_producto, text=label_text).grid(row=i, column=0, padx=5, pady=5)
                    entry = tk.Entry(self.ventana_ingreso_producto)
                    entry.grid(row=i, column=1, padx=5, pady=5)
                    entradas.append(entry)

                boton_insertar = tk.Button(self.ventana_ingreso_producto, text="Insertar", command=lambda: self.guardar_producto(*[e.get() for e in entradas]))
                boton_insertar.grid(row=len(etiquetas), column=0, columnspan=2, padx=5, pady=5)

                # Configurar el evento de cierre de la ventana
                self.ventana_ingreso_producto.protocol("WM_DELETE_WINDOW", self.cerrar_ventana_ingreso_producto)

    def cerrar_ventana_ingreso_producto(self):
        if hasattr(self, "ventana_ingreso_producto"):
            self.ventana_ingreso_producto.withdraw()  # Ocultar la ventana en lugar de cerrarla


    def guardar_producto(self, id_producto, descripcion, precio, existencias):
        self.producto_manager = ProductoManager(self.conexion_db.establecer_conexion())
        self.producto_manager.insertar_producto(id_producto, descripcion, precio, existencias)

    def mostrar_productos(self):
        if not self.usuario_autenticado:
            return

        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute("SELECT * FROM productos")
            productos = cur.fetchall()

            if not productos:
                messagebox.showinfo("Productos", "No hay productos registrados.")
                return

            if hasattr(self, "tabla_productos_frame"):
                self.tabla_productos_frame.destroy()
                delattr(self, "tabla_productos_frame")  # Eliminar el atributo

            self.tabla_productos_frame = ttk.Frame(self)
            self.tabla_productos_frame.pack(fill="both", expand=True)

            # Sección de opciones
            opciones_frame = ttk.Frame(self.tabla_productos_frame)
            opciones_frame.pack(side="top", padx=5, pady=5, fill="x")

            # Opciones de ordenamiento
            opciones_ordenamiento = ["existencias", "id_producto", "descripcion", "precio"]
            combo_ordenamiento = ttk.Combobox(opciones_frame, values=opciones_ordenamiento)
            combo_ordenamiento.current(0)  # Seleccionar la primera opción por defecto
            combo_ordenamiento.pack(side="left", padx=5)

            # Opciones de orden ascendente o descendente
            opciones_orden = ["Ascendente", "Descendente"]
            combo_orden = ttk.Combobox(opciones_frame, values=opciones_orden)
            combo_orden.current(0)  # Seleccionar la primera opción por defecto
            combo_orden.pack(side="left", padx=5)

            boton_ordenar = ttk.Button(opciones_frame, text="Ordenar", command=lambda: self.ordenar_productos(tabla_productos, combo_ordenamiento.get(), combo_orden.get()))
            boton_ordenar.pack(side="left", padx=5, pady=5)

            # Operadores de agregación
            opciones_agregacion = ["avg", "min", "max", "sum", "count"]
            combo_agregacion = ttk.Combobox(opciones_frame, values=opciones_agregacion)
            combo_agregacion.current(0)  # Seleccionar la primera opción por defecto
            combo_agregacion.pack(side="left", padx=5)
            boton_agregar_agregacion = ttk.Button(opciones_frame, text="Agregar Agregación", command=lambda: self.agregar_agregacion_productos(tabla_productos, combo_agregacion.get(), combo_ordenamiento.get()))
            boton_agregar_agregacion.pack(side="left", padx=5, pady=5)

            # Operadores de comparación
            opciones_comparacion = ["=", "<", ">", "<=", ">=", "<>"]
            combo_comparacion = ttk.Combobox(opciones_frame, values=opciones_comparacion)
            combo_comparacion.current(0)  # Seleccionar la primera opción por defecto
            combo_comparacion.pack(side="left", padx=5)

            etiqueta_valor = tk.Label(opciones_frame, text="Valor:")
            etiqueta_valor.pack(side="left", padx=5)

            campo_valor = tk.Entry(opciones_frame)
            campo_valor.pack(side="left", padx=5)

            boton_agregar_comparacion = ttk.Button(opciones_frame, text="Agregar Comparación", command=lambda: self.agregar_comparacion_productos(tabla_productos, combo_comparacion.get(), campo_valor.get(), combo_ordenamiento.get()))
            boton_agregar_comparacion.pack(side="left", padx=5, pady=5)

            # Tabla de productos
            tabla_productos_frame = ttk.Frame(self.tabla_productos_frame)
            tabla_productos_frame.pack(fill="both", expand=True)

            # Establecer el estilo para la tabla
            estilo_tabla = ttk.Style()
            estilo_tabla.configure("Custom.Treeview", background="#ffffff")  # Color de fondo personalizado

            # Definir las columnas de la tabla
            columnas = ("ID Producto", "Descripción", "Precio", "Existencias")
            tabla_productos = ttk.Treeview(tabla_productos_frame, columns=columnas, show="headings", style="Custom.Treeview")
            for col in columnas:
                tabla_productos.heading(col, text=col)

            for producto in productos:
                tabla_productos.insert("", "end", values=producto)

            tabla_productos.pack(padx=5, pady=5, fill="both", expand=True)

            # Botón para quitar la tabla
            boton_quitar_tabla = ttk.Button(tabla_productos_frame, text="Quitar Tabla", command=self.quitar_tabla)
            boton_quitar_tabla.pack(side="bottom", pady=5)

        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al mostrar productos: {e}")

        finally:
            if cur:
                cur.close()

    def mostrar_productos_mas_baratos(self):
        if not self.usuario_autenticado:
            return

        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute("SELECT * FROM productos_mas_baratos")
            productos_menos_existencias = cur.fetchall()

            if not productos_menos_existencias:
                messagebox.showinfo("Productos productos mas baratos", "No hay productos registrados.")
                return

            # Limpiar frame si ya existe
            if hasattr(self, "tabla_productos_mas_baratos_frame"):
                self.tabla_productos_menos_existencias_frame.destroy()
                delattr(self, "tabla_productos_mas_baratos_frame")

            # Crear frame para la tabla
            self.tabla_productos_menos_existencias_frame = ttk.Frame(self)
            self.tabla_productos_menos_existencias_frame.pack(fill="both", expand=True)

            # Crear Treeview para mostrar los productos con menos existencias
            tree = ttk.Treeview(self.tabla_productos_menos_existencias_frame, columns=("Descripción", "Precio"))
            tree.heading("#1", text="Descripción")
            tree.heading("#2", text="Precio")

            # Insertar datos en la tabla
            for producto in productos_menos_existencias:
                tree.insert("", "end", values=producto)

            # Ajustar columnas
            for col in ("Descripción", "Precio"):
                tree.column(col, width=100, anchor="center")

            tree.pack(fill="both", expand=True)

        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al mostrar productos mas baratos: {e}")

        finally:
            if cur:
                cur.close()

    def mostrar_productos_menos_existencias(self):
        if not self.usuario_autenticado:
            return

        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute("SELECT * FROM productos_menos_existencias")
            productos_menos_existencias = cur.fetchall()

            if not productos_menos_existencias:
                messagebox.showinfo("Productos con menos existencias", "No hay productos registrados.")
                return

            # Limpiar frame si ya existe
            if hasattr(self, "tabla_productos_menos_existencias_frame"):
                self.tabla_productos_menos_existencias_frame.destroy()
                delattr(self, "tabla_productos_menos_existencias_frame")

            # Crear frame para la tabla
            self.tabla_productos_menos_existencias_frame = ttk.Frame(self)
            self.tabla_productos_menos_existencias_frame.pack(fill="both", expand=True)

            # Crear Treeview para mostrar los productos con menos existencias
            tree = ttk.Treeview(self.tabla_productos_menos_existencias_frame, columns=("Descripción", "Existencias"))
            tree.heading("#1", text="Descripción")
            tree.heading("#2", text="Existencias")

            # Insertar datos en la tabla
            for producto in productos_menos_existencias:
                tree.insert("", "end", values=producto)

            # Ajustar columnas
            for col in ("Descripción", "Existencias"):
                tree.column(col, width=100, anchor="center")

            tree.pack(fill="both", expand=True)

        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al mostrar productos con menos existencias: {e}")

        finally:
            if cur:
                cur.close()


    def mostrar_productos_mayor_existencias(self):
        if not self.usuario_autenticado:
            return

        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute("SELECT * FROM productos_mayor_existencias")
            productos_menos_existencias = cur.fetchall()

            if not productos_menos_existencias:
                messagebox.showinfo("Productos con mayor existencias", "No hay productos registrados.")
                return

            # Limpiar frame si ya existe
            if hasattr(self, "tabla_productos_mayor_existencias_frame"):
                self.tabla_productos_menos_existencias_frame.destroy()
                delattr(self, "tabla_productos_mayor_existencias_frame")

            # Crear frame para la tabla
            self.tabla_productos_menos_existencias_frame = ttk.Frame(self)
            self.tabla_productos_menos_existencias_frame.pack(fill="both", expand=True)

            # Crear Treeview para mostrar los productos con menos existencias
            tree = ttk.Treeview(self.tabla_productos_menos_existencias_frame, columns=("Descripción", "Existencias"))
            tree.heading("#1", text="Descripción")
            tree.heading("#2", text="Existencias")

            # Insertar datos en la tabla
            for producto in productos_menos_existencias:
                tree.insert("", "end", values=producto)

            # Ajustar columnas
            for col in ("Descripción", "Existencias"):
                tree.column(col, width=100, anchor="center")

            tree.pack(fill="both", expand=True)

        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al mostrar productos con menos existencias: {e}")

        finally:
            if cur:
                cur.close()


    def agregar_comparacion_productos(self, tabla_productos, operador, valor, columna_ordenamiento):
        # Ejemplo de cómo agregar un filtro de comparación con un valor ingresado por el usuario
        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute(f"SELECT * FROM productos WHERE {columna_ordenamiento} {operador} %s", (valor,))  # Usar la columna de ordenamiento seleccionada
            productos_filtrados = cur.fetchall()
            
            # Limpiar la tabla antes de mostrar los resultados filtrados
            tabla_productos.delete(*tabla_productos.get_children())
            
            for producto in productos_filtrados:
                tabla_productos.insert("", "end", values=producto)

        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al agregar operación de comparación: {e}")

        finally:
            if cur:
                cur.close()

    def agregar_agregacion_productos(self, tabla_productos, operador, columna_ordenamiento):
        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute(f"SELECT {operador}({columna_ordenamiento}) FROM productos")
            resultado = cur.fetchone()[0]

            messagebox.showinfo("Resultado de Agregación", f"El resultado de la operación de {operador} es: {resultado}")

        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al agregar operación de agregación: {e}")

        finally:
            if cur:
                cur.close()

    def ordenar_productos(self, tabla, columna_orden, orden):
        # Obtener todos los ítems de la tabla
        items = tabla.get_children()

        # Ordenar los ítems según la columna seleccionada y el orden elegido
        if columna_orden == "existencias":
            if orden == "Ascendente":
                items = sorted(items, key=lambda x: float(tabla.item(x)["values"][3]))  # Columna "Existencias"
            else:
                items = sorted(items, key=lambda x: float(tabla.item(x)["values"][3]), reverse=True)
        elif columna_orden == "id_producto":
            if orden == "Ascendente":
                items = sorted(items, key=lambda x: int(tabla.item(x)["values"][0]))  # Columna "ID Producto"
            else:
                items = sorted(items, key=lambda x: int(tabla.item(x)["values"][0]), reverse=True)
        elif columna_orden == "descripcion":
            if orden == "Ascendente":
                items = sorted(items, key=lambda x: tabla.item(x)["values"][1].lower())  # Columna "Descripción"
            else:
                items = sorted(items, key=lambda x: tabla.item(x)["values"][1].lower(), reverse=True)
        elif columna_orden == "precio":
            if orden == "Ascendente":
                items = sorted(items, key=lambda x: float(tabla.item(x)["values"][2]))  # Columna "ID Producto"
            else:
                items = sorted(items, key=lambda x: float(tabla.item(x)["values"][2]), reverse=True)

        # Limpiar la tabla
        for item in items:
            tabla.move(item, "", "end")

    def quitar_tabla(self):
        if hasattr(self, "tabla_productos_frame"):
            self.tabla_productos_frame.destroy()
            delattr(self, "tabla_productos_frame")  # Eliminar el atributo

    def eliminar_producto(self):
        if self.usuario_autenticado:
            def eliminar(id_producto):
                try:
                    cur = self.conexion_db.conn.cursor()
                    cur.execute("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
                    self.conexion_db.conn.commit()

                    if cur.rowcount > 0:
                        messagebox.showinfo("Éxito", "El producto se eliminó correctamente.")
                    else:
                        messagebox.showerror("Error", "No se encontró ningún producto con ese ID.")

                    entrada_id_eliminar.delete(0, tk.END)

                except psycopg2.Error as e:
                    messagebox.showerror("Error", f"Error al eliminar el producto: {e}")

                finally:
                    if cur:
                        cur.close()

            ventana_eliminar = tk.Toplevel()
            ventana_eliminar.title("Eliminar Producto")

            etiqueta_id_eliminar = tk.Label(ventana_eliminar, text="ID Producto a Eliminar:")
            etiqueta_id_eliminar.grid(row=0, column=0, padx=5, pady=5)
            entrada_id_eliminar = tk.Entry(ventana_eliminar)
            entrada_id_eliminar.grid(row=0, column=1, padx=5, pady=5)

            boton_eliminar = tk.Button(ventana_eliminar, text="Eliminar", command=lambda: eliminar(entrada_id_eliminar.get()))
            boton_eliminar.grid(row=1, column=0, columnspan=2, padx=5, pady=5)


    def crear_respaldo(self):
     if self.usuario_autenticado:
        try:
            # Obtener el directorio de trabajo actual
            directorio_actual = os.getcwd()

            # Crear el directorio 'respaldos' dentro del directorio actual si no existe
            directorio_respaldos = os.path.join(directorio_actual, 'respaldos')
            if not os.path.exists(directorio_respaldos):
                os.makedirs(directorio_respaldos)

            fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_archivo = f"respaldo_{fecha_actual}.sql"
            ruta_archivo = os.path.join(directorio_respaldos, nombre_archivo)  # Construir la ruta completa del archivo
            comando = f"pg_dump -U postgres -d proyectoDB -f \"{ruta_archivo}\""
            os.environ['PGPASSWORD'] = 'daeson'
            subprocess.run(comando, shell=True)

            messagebox.showinfo("Éxito", f"Se creó el respaldo en {ruta_archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

    def restaurar_respaldo(self):
        if self.usuario_autenticado:
            try:
                # Utilizar el explorador de archivos para seleccionar el archivo de respaldo
                archivo_respaldo = filedialog.askopenfilename(initialdir="/", title="Seleccionar archivo de respaldo", filetypes=(("Archivos SQL", "*.sql"), ("Todos los archivos", "*.*")))
                if not archivo_respaldo:
                    messagebox.showwarning("Advertencia", "No se seleccionó ningún archivo de respaldo.")
                    return

                # Comando para restaurar la base de datos desde el archivo de respaldo seleccionado
                comando = f"psql -U postgres -d proyectoDB -f \"{archivo_respaldo}\""
                os.environ['PGPASSWORD'] = '12345'
                subprocess.run(comando, shell=True)

                messagebox.showinfo("Éxito", f"Se restauró el respaldo desde {archivo_respaldo}.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al restaurar el respaldo: {str(e)}")

    def registrar_cliente(self):
        if self.usuario_autenticado:
            ventana_registro = tk.Toplevel(self)
            ventana_registro.title("Registrar Cliente")
            etiquetas = ["ID:", "Nombre:", "Teléfono:", "Dirección:"]
            entradas = []
            
            for i, label_text in enumerate(etiquetas):
                ttk.Label(ventana_registro, text=label_text).grid(row=i, column=0, padx=5, pady=5)
                if i == 0:  # Si es el campo de ID
                    entry = ttk.Label(ventana_registro, text="Generado Automaticamente", state="disabled")
                else:
                    entry = tk.Entry(ventana_registro)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entradas.append(entry)
            
            boton_registrar = tk.Button(ventana_registro, text="Registrar", command=lambda: self.guardar_cliente(*[e.get() for e in entradas[1:]]))
            boton_registrar.grid(row=len(etiquetas), column=0, columnspan=2, padx=5, pady=5)

    def guardar_cliente(self, nombre, telefono, direccion):
        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute("""
                INSERT INTO clientes (nombre, telefono, direccion)
                VALUES (%s, %s, %s)
                RETURNING id_cliente
            """, (nombre, telefono, direccion))
            id_cliente = cur.fetchone()[0]
            self.conexion_db.conn.commit()
            messagebox.showinfo("Éxito", f"Cliente registrado correctamente. ID: {id_cliente}")
        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al registrar el cliente: {e}")
        finally:
            if cur:
                cur.close()

    def mostrar_clientes(self):
        if not self.usuario_autenticado:
            return

        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute("SELECT * FROM clientes")
            clientes = cur.fetchall()

            if not clientes:
                messagebox.showinfo("Clientes", "No hay clientes registrados.")
                return

            if hasattr(self, "tabla_clientes_frame"):
                self.tabla_clientes_frame.destroy()
                delattr(self, "tabla_clientes_frame")  # Eliminar el atributo

            self.tabla_clientes_frame = ttk.Frame(self)
            self.tabla_clientes_frame.pack(fill="both", expand=True)

            # Establecer el estilo para la tabla
            estilo_tabla = ttk.Style()
            estilo_tabla.configure("Custom.Treeview", background="#ffffff")  # Color de fondo personalizado

            # Definir las columnas de la tabla
            columnas = ("id_cliente", "nombre", "telefono", "direccion")
            tabla_clientes = ttk.Treeview(self.tabla_clientes_frame, columns=columnas, show="headings", style="Custom.Treeview")
            for col in columnas:
                tabla_clientes.heading(col, text=col)

            for cliente in clientes:
                tabla_clientes.insert("", "end", values=cliente)

            tabla_clientes.pack(padx=5, pady=5, fill="both", expand=True)

            # Crear campos de búsqueda en la parte superior de la tabla
            frame_busqueda = ttk.Frame(self.tabla_clientes_frame)
            frame_busqueda.pack(pady=5)

            # Etiqueta y menú desplegable para las columnas
            etiqueta_columna = tk.Label(frame_busqueda, text="Columna:")
            etiqueta_columna.grid(row=0, column=0, padx=5, pady=5)
            opciones_columna = columnas[1:]  # Excluir la columna ID_Cliente
            campo_columna = ttk.Combobox(frame_busqueda, values=opciones_columna)
            campo_columna.grid(row=0, column=1, padx=5, pady=5)

            # Etiqueta y menú desplegable para los comparadores
            etiqueta_comparador = tk.Label(frame_busqueda, text="Comparador:")
            etiqueta_comparador.grid(row=0, column=2, padx=5, pady=5)
            opciones_comparador = ["=", "<>", ">", ">=", "<", "<="]
            campo_comparador = ttk.Combobox(frame_busqueda, values=opciones_comparador)
            campo_comparador.grid(row=0, column=3, padx=5, pady=5)

            # Etiqueta y campo de entrada para el valor
            etiqueta_valor = tk.Label(frame_busqueda, text="Valor:")
            etiqueta_valor.grid(row=0, column=4, padx=5, pady=5)
            campo_valor = tk.Entry(frame_busqueda)
            campo_valor.grid(row=0, column=5, padx=5, pady=5)

            # Botón para buscar cliente
            boton_buscar = tk.Button(frame_busqueda, text="Buscar", command=lambda: self.buscar_cliente(tabla_clientes, campo_columna.get(), campo_comparador.get(), campo_valor.get()))
            boton_buscar.grid(row=0, column=6, padx=5, pady=5)

            # Botón para quitar la tabla de clientes
            boton_cerrar_tabla_clientes = tk.Button(self.tabla_clientes_frame, text="Cerrar", command=self.quitar_tabla_clientes)
            boton_cerrar_tabla_clientes.pack(side="bottom", pady=5)

        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al mostrar clientes: {e}")

        finally:
            if cur:
                cur.close()

    def buscar_cliente(self, tabla_clientes, columna, comparador, valor):
        if columna and comparador and valor:
            try:
                cur = self.conexion_db.conn.cursor()
                consulta = f"SELECT * FROM clientes WHERE {columna} {comparador} %s"
                cur.execute(consulta, (valor,))
                resultados = cur.fetchall()

                tabla_clientes.delete(*tabla_clientes.get_children())

                if resultados:
                    for cliente in resultados:
                        tabla_clientes.insert("", "end", values=cliente)
                else:
                    messagebox.showinfo("Búsqueda de Cliente", "No se encontraron clientes con ese criterio.")

            except psycopg2.Error as e:
                messagebox.showerror("Error", f"Error al buscar cliente: {e}")

            finally:
                if cur:
                    cur.close()
        else:
            messagebox.showerror("Error", "Por favor complete todos los campos.")

    def quitar_tabla_clientes(self):
        if hasattr(self, "tabla_clientes_frame"):
            self.tabla_clientes_frame.destroy()
            delattr(self, "tabla_clientes_frame")  # Eliminar el atributo


    def eliminar_cliente(self):
        if self.usuario_autenticado:
            def eliminar(id_cliente):
                try:
                    cur = self.conexion_db.conn.cursor()
                    cur.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
                    self.conexion_db.conn.commit()

                    if cur.rowcount > 0:
                        messagebox.showinfo("Éxito", "El cliente se eliminó correctamente.")
                    else:
                        messagebox.showerror("Error", "No se encontró ningún cliente con ese ID.")

                    entrada_id_eliminar.delete(0, tk.END)

                except psycopg2.Error as e:
                    messagebox.showerror("Error", f"Error al eliminar el cliente: {e}")

                finally:
                    if cur:
                        cur.close()

            ventana_eliminar = tk.Toplevel()
            ventana_eliminar.title("Eliminar Cliente")

            etiqueta_id_eliminar = tk.Label(ventana_eliminar, text="ID Cliente a Eliminar:")
            etiqueta_id_eliminar.grid(row=0, column=0, padx=5, pady=5)
            entrada_id_eliminar = tk.Entry(ventana_eliminar)
            entrada_id_eliminar.grid(row=0, column=1, padx=5, pady=5)

            boton_eliminar = tk.Button(ventana_eliminar, text="Eliminar", command=lambda: eliminar(entrada_id_eliminar.get()))
            boton_eliminar.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

    def registrar_proveedor(self):
     if self.usuario_autenticado:
        ventana_registro = tk.Toplevel(self)
        ventana_registro.title("Registrar Proveedor")
        etiquetas = ["ID Proveedor:", "Nombre:", "Teléfono:", "Dirección:"]
        entradas = []
        for i, label_text in enumerate(etiquetas):
            ttk.Label(ventana_registro, text=label_text).grid(row=i, column=0, padx=5, pady=5)
            if i == 0:  # Si es el campo de ID
                entry = ttk.Label(ventana_registro, text="Generado automáticamente", state="disabled")
            else:
                entry = tk.Entry(ventana_registro)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entradas.append(entry)
        
        boton_registrar = tk.Button(ventana_registro, text="Registrar", command=lambda: self.guardar_proveedor(*[e.get() for e in entradas[1:]]))
        boton_registrar.grid(row=len(etiquetas), column=0, columnspan=2, padx=5, pady=5)

    def guardar_proveedor(self, nombre, telefono, direccion):
        try:
            cur = self.conexion_db.conn.cursor()
            cur.execute("""
                INSERT INTO proveedores (nombre, telefono, direccion)
                VALUES (%s, %s, %s)
            """, (nombre, telefono, direccion))
            self.conexion_db.conn.commit()
            messagebox.showinfo("Éxito", "Proveedor registrado correctamente.")
        except psycopg2.Error as e:
            messagebox.showerror("Error", f"Error al registrar el proveedor: {e}")
        finally:
            if cur:
                cur.close()

    def mostrar_proveedor(self):
        if self.usuario_autenticado:
            try:
                cur = self.conexion_db.conn.cursor()
                cur.execute("SELECT * FROM proveedores")
                proveedores = cur.fetchall()

                if proveedores:
                    if hasattr(self, "tabla_proveedores_frame"):
                        self.tabla_proveedores_frame.destroy()
                        delattr(self, "tabla_proveedores_frame")  # Eliminar el atributo

                    self.tabla_proveedores_frame = ttk.Frame(self)
                    self.tabla_proveedores_frame.pack(fill="both", expand=True)

                    # Establecer el estilo para la tabla
                    estilo_tabla = ttk.Style()
                    estilo_tabla.configure("Custom.Treeview", background="#ffffff")  # Color de fondo personalizado

                    tabla_proveedores = ttk.Treeview(self.tabla_proveedores_frame, columns=("ID_Proveedor", "Nombre", "Teléfono", "Dirección"), show="headings", style="Custom.Treeview")
                    tabla_proveedores.heading("ID_Proveedor", text="ID_Proveedor")
                    tabla_proveedores.heading("Nombre", text="Nombre")
                    tabla_proveedores.heading("Teléfono", text="Teléfono")
                    tabla_proveedores.heading("Dirección", text="Dirección")

                    for proveedor in proveedores:
                        tabla_proveedores.insert("", "end", values=proveedor)

                    tabla_proveedores.pack(padx=5, pady=5, fill="both", expand=True)

                    # Botón para quitar la tabla de proveedores
                    boton_quitar_tabla_proveedores = ttk.Button(self.tabla_proveedores_frame, text="Quitar Tabla", command=self.quitar_tabla_proveedores)
                    boton_quitar_tabla_proveedores.pack(pady=5)

                else:
                    messagebox.showinfo("Proveedores", "No hay proveedores registrados.")

            except psycopg2.Error as e:
                messagebox.showerror("Error", f"Error al mostrar proveedores: {e}")

            finally:
                if cur:
                    cur.close()

    def quitar_tabla_proveedores(self):
        if hasattr(self, "tabla_proveedores_frame"):
            self.tabla_proveedores_frame.destroy()
            delattr(self, "tabla_proveedores_frame")  # Eliminar el atributo

    def eliminar_proveedor(self):
        if self.usuario_autenticado:
            def eliminar(id_proveedor):
                try:
                    cur = self.conexion_db.conn.cursor()
                    cur.execute("DELETE FROM proveedores WHERE proveedor_id = %s", (id_proveedor,))
                    self.conexion_db.conn.commit()

                    if cur.rowcount > 0:
                        messagebox.showinfo("Éxito", "El proveedor se eliminó correctamente.")
                    else:
                        messagebox.showerror("Error", "No se encontró ningún proveedor con ese ID.")

                    entrada_id_eliminar.delete(0, tk.END)

                except psycopg2.Error as e:
                    messagebox.showerror("Error", f"Error al eliminar el proveedor: {e}")

                finally:
                    if cur:
                        cur.close()

        ventana_eliminar = tk.Toplevel()
        ventana_eliminar.title("Eliminar Proveedor")

        etiqueta_id_eliminar = tk.Label(ventana_eliminar, text="ID Proveedor a Eliminar:")
        etiqueta_id_eliminar.grid(row=0, column=0, padx=5, pady=5)
        entrada_id_eliminar = tk.Entry(ventana_eliminar)
        entrada_id_eliminar.grid(row=0, column=1, padx=5, pady=5)

        boton_eliminar = tk.Button(ventana_eliminar, text="Eliminar", command=lambda: eliminar(entrada_id_eliminar.get()))
        boton_eliminar.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

    def modificar_producto(self):
        if self.usuario_autenticado:
            def guardar_modificacion(id_producto, nueva_descripcion, nuevo_precio, nuevas_existencias):
                try:
                    cur = self.conexion_db.conn.cursor()

                    # Construir la consulta SQL dinámicamente
                    query = "UPDATE productos SET "
                    valores = []

                    if nueva_descripcion:
                        query += "descripcion = %s, "
                        valores.append(nueva_descripcion)
                    if nuevo_precio:
                        query += "precio = %s, "
                        valores.append(float(nuevo_precio))
                    if nuevas_existencias:
                        query += "existencias = %s, "
                        valores.append(float(nuevas_existencias))

                    # Eliminar la última coma y espacio
                    query = query[:-2]

                    # Agregar la cláusula WHERE
                    query += " WHERE id_producto = %s"
                    valores.append(id_producto)

                    # Ejecutar la consulta
                    cur.execute(query, tuple(valores))
                    self.conexion_db.conn.commit()
                    messagebox.showinfo("Éxito", "Producto modificado correctamente.")
                except psycopg2.Error as e:
                    messagebox.showerror("Error", f"Error al modificar el producto: {e}")
                finally:
                    if cur:
                        cur.close()

            ventana_modificar = tk.Toplevel(self)
            ventana_modificar.title("Modificar Producto")

            etiquetas = ["ID Producto:", "Nueva Descripción:", "Nuevo Precio:", "Nuevas Existencias:"]
            entradas = []
            for i, label_text in enumerate(etiquetas):
                ttk.Label(ventana_modificar, text=label_text).grid(row=i, column=0, padx=5, pady=5)
                entry = tk.Entry(ventana_modificar)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entradas.append(entry)

            boton_modificar = tk.Button(ventana_modificar, text="Modificar", command=lambda: guardar_modificacion(*[e.get() for e in entradas]))
            boton_modificar.grid(row=len(etiquetas), column=0, columnspan=2, padx=5, pady=5)

    def modificar_cliente(self):
        if self.usuario_autenticado:
            def guardar_modificacion(id_cliente, nuevo_nombre, nuevo_telefono, nueva_direccion):
                try:
                    cur = self.conexion_db.conn.cursor()

                    # Construir la consulta SQL dinámicamente
                    query = "UPDATE clientes SET "
                    valores = []

                    if nuevo_nombre:
                        query += "nombre = %s, "
                        valores.append(nuevo_nombre)
                    if nuevo_telefono:
                        query += "telefono = %s, "
                        valores.append(nuevo_telefono)
                    if nueva_direccion:
                        query += "direccion = %s, "
                        valores.append(nueva_direccion)

                    # Eliminar la última coma y espacio
                    query = query[:-2]

                    # Agregar la cláusula WHERE
                    query += " WHERE id_cliente = %s"
                    valores.append(id_cliente)

                    # Ejecutar la consulta
                    cur.execute(query, tuple(valores))
                    self.conexion_db.conn.commit()
                    messagebox.showinfo("Éxito", "Cliente modificado correctamente.")
                except psycopg2.Error as e:
                    messagebox.showerror("Error", f"Error al modificar el cliente: {e}")
                finally:
                    if cur:
                        cur.close()

            ventana_modificar = tk.Toplevel(self)
            ventana_modificar.title("Modificar Cliente")

            etiquetas = ["ID Cliente:", "Nuevo Nombre:", "Nuevo Teléfono:", "Nueva Dirección:"]
            entradas = []
            for i, label_text in enumerate(etiquetas):
                ttk.Label(ventana_modificar, text=label_text).grid(row=i, column=0, padx=5, pady=5)
                entry = tk.Entry(ventana_modificar)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entradas.append(entry)

            boton_modificar = tk.Button(ventana_modificar, text="Modificar", command=lambda: guardar_modificacion(*[e.get() for e in entradas]))
            boton_modificar.grid(row=len(etiquetas), column=0, columnspan=2, padx=5, pady=5)

    def modificar_proveedor(self):
        if self.usuario_autenticado:
            def guardar_modificacion(id_proveedor, nuevo_nombre, nuevo_telefono, nueva_direccion):
                try:
                    cur = self.conexion_db.conn.cursor()

                    # Construir la consulta SQL dinámicamente
                    query = "UPDATE proveedores SET "
                    valores = []

                    if nuevo_nombre:
                        query += "nombre = %s, "
                        valores.append(nuevo_nombre)
                    if nuevo_telefono:
                        query += "telefono = %s, "
                        valores.append(nuevo_telefono)
                    if nueva_direccion:
                        query += "direccion = %s, "
                        valores.append(nueva_direccion)

                    # Eliminar la última coma y espacio
                    query = query[:-2]

                    # Agregar la cláusula WHERE
                    query += " WHERE proveedor_id = %s"
                    valores.append(id_proveedor)

                    # Ejecutar la consulta
                    cur.execute(query, tuple(valores))
                    self.conexion_db.conn.commit()
                    messagebox.showinfo("Éxito", "Proveedor modificado correctamente.")
                except psycopg2.Error as e:
                    messagebox.showerror("Error", f"Error al modificar el proveedor: {e}")
                finally:
                    if cur:
                        cur.close()

            ventana_modificar = tk.Toplevel(self)
            ventana_modificar.title("Modificar Proveedor")

            etiquetas = ["ID Proveedor:", "Nuevo Nombre:", "Nuevo Teléfono:", "Nueva Dirección:"]
            entradas = []
            for i, label_text in enumerate(etiquetas):
                ttk.Label(ventana_modificar, text=label_text).grid(row=i, column=0, padx=5, pady=5)
                entry = tk.Entry(ventana_modificar)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entradas.append(entry)

            boton_modificar = tk.Button(ventana_modificar, text="Modificar", command=lambda: guardar_modificacion(*[e.get() for e in entradas]))
            boton_modificar.grid(row=len(etiquetas), column=0, columnspan=2, padx=5, pady=5)
    def cerrar_sesion(self):
        self.destroy()  # Cerrar la ventana principal
if __name__ == "__main__":
    app = CarniceriaApp()
    app.mainloop()
