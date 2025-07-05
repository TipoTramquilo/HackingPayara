#a!/bin/bash

# ==============================================================================
# Script para generar una aplicación de e-commerce .war intencionadamente vulnerable
# Propósito: Laboratorio de Ciberseguridad para practicar RCE (Remote Code Execution)
# Entorno: Java 8, Payara 4.x, PostgreSQL
# Vulnerabilidades:
#   1. Inyección de Comandos (a través de una herramienta de diagnóstico de admin).
#   2. Deserialización Insegura (a través de una cookie de sesión).
#   3. Ahora con un flujo de Login contra DB, productos dinámicos desde DB, y REGISTRO DE USUARIOS.
#   4. Funcionalidad "Recuérdame" en el inicio de sesión.
#   5. ¡NUEVO! Botón de "Iniciar Sesión" en la página principal y enlace a "Registrarse" en la página de login.
#   6. ¡ACTUALIZADO! La página inicial no muestra "Invitado" por defecto, solo el botón de inicio de sesión.
#   7. ¡ACTUALIZADO! DatabaseUtil.java modificado para usar DataSource JNDI.
#   8. ¡ACTUALIZADO! Manejo de errores de conexión a DB con HTTP 500.
#   9. ¡ACTUALIZADO! Las cookies de sesión solo se emiten tras un login exitoso.
# ==============================================================================

# --- Verificación de prerrequisitos ---
if ! command -v mvn &> /dev/null
then
    echo "ERROR: Maven (mvn) no está instalado o no se encuentra en el PATH."
    echo "Por favor, instala Maven para continuar. En sistemas Debian/Ubuntu: sudo apt install maven"
    exit 1
fi

echo "Iniciando la creación de la aplicación de e-commerce vulnerable con base de datos, registro de usuarios y 'Recuérdame'..."

# --- Estructura del Proyecto ---
PROJECT_NAME="vulnerable-ecommerce-full-features-$(date +%s)" # Nombre temporal para el directorio
BASE_DIR=$(pwd)/${PROJECT_NAME}
SRC_DIR="${BASE_DIR}/src/main/java/com/example/ecommerce"
WEBAPP_DIR="${BASE_DIR}/src/main/webapp"
WEBINF_DIR="${WEBAPP_DIR}/WEB-INF"
ADMIN_DIR="${WEBAPP_DIR}/admin"
CURRENT_DIR=$(pwd) # Para mover el WAR al directorio actual

echo "Creando la estructura de directorios temporal en: ${BASE_DIR}"
mkdir -p "${SRC_DIR}"
mkdir -p "${WEBINF_DIR}"
mkdir -p "${ADMIN_DIR}"

# --- Creación de archivos fuente ---

# 1. pom.xml: Define las dependencias del proyecto.
echo "Creando pom.xml..."
cat <<'EOF' > "${BASE_DIR}/pom.xml"
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"
         >
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>vulnerable-ecommerce</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>war</packaging>
    <name>Vulnerable E-commerce Application</name>
    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    <dependencies>
        <dependency>
            <groupId>javax.servlet</groupId>
            <artifactId>javax.servlet-api</artifactId>
            <version>3.1.0</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>commons-collections</groupId>
            <artifactId>commons-collections</artifactId>
            <version>3.1</version>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <version>42.7.3</version>
        </dependency>
        <dependency>
            <groupId>com.google.code.gson</groupId>
            <artifactId>gson</artifactId>
            <version>2.10.1</version>
        </dependency>
        <dependency>
            <groupId>javax</groupId>
            <artifactId>javaee-api</artifactId>
            <version>7.0</version>
            <scope>provided</scope>
        </dependency>
    </dependencies>
    <build>
        <finalName>vulnerable-ecommerce</finalName>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-war-plugin</artifactId>
                <version>3.2.3</version>
                <configuration>
                    <failOnMissingWebXml>false</failOnMissingWebXml>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
EOF

# 2. web.xml: Mapea los Servlets.
echo "Creando web.xml..."
cat <<'EOF' > "${WEBINF_DIR}/web.xml"
<web-app xmlns="http://xmlns.jcp.org/xml/ns/javaee"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://xmlns.jcp.org/xml/ns/javaee http://xmlns.jcp.org/xml/ns/javaee/web-app_3_1.xsd"
         version="3.1">
    <display-name>Vulnerable E-commerce</display-name>
    <welcome-file-list>
        <welcome-file>index.html</welcome-file>
    </welcome-file-list>

    <servlet>
        <servlet-name>DiagnosticsServlet</servlet-name>
        <servlet-class>com.example.ecommerce.DiagnosticsServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>DiagnosticsServlet</servlet-name>
        <url-pattern>/admin/diagnostics</url-pattern>
    </servlet-mapping>

    <servlet>
        <servlet-name>SessionServlet</servlet-name>
        <servlet-class>com.example.ecommerce.SessionServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>SessionServlet</servlet-name>
        <url-pattern>/session</url-pattern>
    </servlet-mapping>

    <servlet>
        <servlet-name>ReviewServlet</servlet-name>
        <servlet-class>com.example.ecommerce.ReviewServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>ReviewServlet</servlet-name>
        <url-pattern>/product/review</url-pattern>
    </servlet-mapping>

    <servlet>
        <servlet-name>LoginServlet</servlet-name>
        <servlet-class>com.example.ecommerce.LoginServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>LoginServlet</servlet-name>
        <url-pattern>/login</url-pattern>
    </servlet-mapping>

    <servlet>
        <servlet-name>ProductServlet</servlet-name>
        <servlet-class>com.example.ecommerce.ProductServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>ProductServlet</servlet-name>
        <url-pattern>/api/products</url-pattern>
    </servlet-mapping>

    <servlet>
        <servlet-name>RegisterServlet</servlet-name>
        <servlet-class>com.example.ecommerce.RegisterServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>RegisterServlet</servlet-name>
        <url-pattern>/register</url-pattern>
    </servlet-mapping>

</web-app>
EOF

# 3. index.html: Página principal de la tienda
echo "Actualizando index.html para no mostrar 'Invitado' por defecto..."
cat <<'EOF' > "${WEBAPP_DIR}/index.html"
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tienda Online Vuln-Tech</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            margin: 0;
            background-color: #f0f2f5;
            color: #333;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        header {
            background: linear-gradient(to right, #007bff, #0056b3);
            color: #fff;
            padding: 1.5rem 0;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            position: relative;
        }
        header h1 {
            margin: 0;
            font-weight: 700;
        }
        .user-info {
            position: absolute;
            top: 10px;
            right: 20px;
            color: #fff;
            font-size: 0.9em;
            display: flex; /* Usar flexbox para alinear elementos */
            align-items: center; /* Centrar verticalmente */
        }
        .user-info a {
            color: #fff;
            text-decoration: underline;
            margin-left: 5px;
        }
        /* Estilo para el botón de Iniciar Sesión */
        .login-button {
            background-color: #28a745; /* Un color diferente para el botón */
            color: white;
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 600;
            text-decoration: none; /* Asegurar que no se subraye */
            margin-left: 10px; /* Espacio a la izquierda del botón */
            transition: background-color 0.3s ease;
        }
        .login-button:hover {
            background-color: #218838;
        }

        .container {
            flex: 1;
            max-width: 1200px;
            margin: 2em auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 12px;
            box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        }
        h2 {
            color: #007bff;
            text-align: center;
            margin-bottom: 1.5em;
            font-weight: 600;
        }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin-bottom: 3em;
        }
        .product-card {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            text-align: center;
            padding: 25px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        .product-card img {
            max-width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .product-card h3 {
            color: #333;
            font-size: 1.4em;
            margin-top: 0;
            margin-bottom: 10px;
        }
        .product-card p {
            font-size: 0.95em;
            color: #666;
            margin-bottom: 15px;
        }
        .product-card span {
            font-size: 1.2em;
            font-weight: 700;
            color: #28a745;
        }
        .reviews-section {
            background-color: #f9f9f9;
            border: 1px dashed #ced4da;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            margin-top: 3em;
        }
        .reviews-section h3 {
            color: #007bff;
            font-size: 1.3em;
            margin-bottom: 15px;
        }
        .reviews-section textarea {
            width: 80%;
            max-width: 600px;
            padding: 12px;
            margin-bottom: 15px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-family: 'Inter', sans-serif;
            font-size: 1em;
            resize: vertical;
        }
        .reviews-section input[type="submit"] {
            background-color: #28a745;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            transition: background-color 0.3s ease;
        }
        .reviews-section input[type="submit"]:hover {
            background-color: #218838;
        }
        .review-list {
            margin-top: 2em;
            text-align: left;
        }
        .review-item {
            background-color: #e9ecef;
            border-left: 5px solid #007bff;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
        }
        .review-item strong {
            color: #333;
        }
        .review-item em {
            font-size: 0.9em;
            color: #666;
        }
        footer {
            text-align: center;
            padding: 1.5rem;
            margin-top: 3em;
            background: #343a40;
            color: #fff;
            box-shadow: 0 -4px 8px rgba(0,0,0,0.1);
        }
        .admin-link {
            font-size: 0.75em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            margin-top: 10px;
            display: inline-block;
            transition: color 0.3s ease;
        }
        .admin-link:hover {
            color: #fff;
        }
    </style>
</head>
<body>
    <header>
        <h1>Vuln-Tech: Tu Tienda de Electrónica Confiable</h1>
        <div class="user-info">
            <span id="usernameDisplay"></span>
            <a href="login.html" id="loginLogoutLink" class="login-button">Iniciar Sesión</a>
        </div>
    </header>
    <div class="container">
        <h2>Nuestros Productos Destacados</h2>
        <div class="product-grid" id="productGrid">
            <p style="text-align: center; grid-column: 1 / -1;">Cargando productos...</p>
        </div>

        <div class="reviews-section">
            <h2>Deja tu Reseña</h2>
            <p>Nos encantaría escuchar tu opinión sobre nuestros productos.</p>
            <form action="./product/review" method="POST" target="_blank">
                <textarea name="reviewText" rows="6" cols="70" placeholder="Escribe tu reseña aquí..."></textarea><br>
                <input type="submit" value="Enviar Reseña">
            </form>
        </div>

        <div class="review-list">
            <h2>Últimas Reseñas</h2>
            <div class="review-item">
                <strong>Excelente Laptop!</strong> <em>por Juan P.</em><br>
                "La Laptop Pro X es increíblemente rápida y la batería dura todo el día. Perfecta para mi trabajo."
            </div>
            <div class="review-item">
                <strong>Auriculares imprescindibles</strong> <em>por María G.</em><br>
                "El sonido de los SoundWave es espectacular. Aislan el ruido perfectamente, ideal para viajar."
            </div>
            <div class="review-item">
                <strong>Sorprendido con el Smartwatch</strong> <em>por Carlos R.</em><br>
                "No esperaba tanto de un reloj, pero el Smartwatch Ultra superó mis expectativas. Muy útil para el ejercicio."
            </div>
        </div>
    </div>
    <footer>
        <p>&copy; 2024 Vuln-Tech - Todos los derechos reservados.</p>
        <a href="admin/index.html" class="admin-link">Acceso para Administradores</a>
    </footer>

    <script>
        // Función para obtener el valor de una cookie
        function getCookie(name) {
            const value = "; " + document.cookie;
            const parts = value.split("; " + name + "=");
            if (parts.length === 2) return parts.pop().split(";").shift();
        }

        // Función para cargar productos dinámicamente
        function loadProducts() {
            fetch('/vulnerable-ecommerce/api/products')
                .then(response => {
                    // Si el servidor devuelve un 500, capturarlo aquí
                    if (!response.ok) {
                        return response.text().then(errorMessage => {
                            throw new Error('Error al cargar productos: ' + errorMessage);
                        });
                    }
                    return response.json();
                })
                .then(products => {
                    const productGrid = document.getElementById('productGrid');
                    productGrid.innerHTML = ''; // Limpiar productos existentes

                    if (products.length === 0) {
                        productGrid.innerHTML = '<p style="text-align: center; grid-column: 1 / -1;">No hay productos disponibles en este momento.</p>';
                        return;
                    }

                    products.forEach(product => {
                        const productCard = `
                            <div class="product-card">
                                <img src="${product.imageUrl || 'https://placehold.co/300x180/007bff/FFFFFF?text=Producto'}" alt="${product.name}">
                                <h3>${product.name}</h3>
                                <p>${product.description}</p>
                                <span>Precio: $${product.price.toFixed(2)}</span>
                            </div>
                        `;
                        productGrid.insertAdjacentHTML('beforeend', productCard);
                    });
                })
                .catch(error => {
                    console.error('Error al cargar productos:', error);
                    // Mostrar un mensaje de error más informativo si la DB falla
                    document.getElementById('productGrid').innerHTML = '<p style="text-align: center; grid-column: 1 / -1; color: red;">Error al cargar los productos. Por favor, revisa la conexión con la base de datos o el estado del servidor.</p>';
                });
        }

        // Lógica de usuario y sesión
        let sessionCookie = getCookie("app_session_data");
        const usernameDisplay = document.getElementById("usernameDisplay");
        const loginLogoutLink = document.getElementById("loginLogoutLink");

        // Solo intentar obtener la sesión si la cookie existe
        if (sessionCookie) {
            fetch("/vulnerable-ecommerce/session")
                .then(response => {
                    if (!response.ok) {
                         // Si SessionServlet falla (ej. por deserialización de cookie maliciosa o DB down),
                         // asumimos que la sesión no es válida o hay un problema.
                        return response.text().then(errorMessage => {
                            console.error("Error del SessionServlet:", errorMessage);
                            // No es un error de conexión a internet, es un error del servidor procesando la solicitud
                            throw new Error("Sesión inválida o problema del servidor.");
                        });
                    }
                    return response.text();
                })
                .then(data => {
                    console.log("Respuesta del SessionServlet:", data);
                    const usernameMatch = data.match(/Usuario: (.+)/);
                    if (usernameMatch && usernameMatch[1]) {
                        usernameDisplay.textContent = "Bienvenido, " + usernameMatch[1];
                        loginLogoutLink.textContent = "Cerrar Sesión";
                        loginLogoutLink.href = "#"; // Manejar con JS
                    } else {
                        // Cookie presente pero no válida o con formato inesperado
                        usernameDisplay.textContent = ""; // No mostrar "Invitado"
                        loginLogoutLink.textContent = "Iniciar Sesión";
                        loginLogoutLink.href = "login.html";
                        // Importante: Si la cookie existe pero es inválida, se debería borrar
                        document.cookie = "app_session_data=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                    }
                })
                .catch(error => {
                    console.error("Error al contactar SessionServlet:", error);
                    // Si hay un error, asumimos que no hay sesión válida o el servlet falló
                    usernameDisplay.textContent = ""; // No mostrar "Invitado"
                    loginLogoutLink.textContent = "Iniciar Sesión";
                    loginLogoutLink.href = "login.html";
                    // Asegurarse de que la cookie se borre si hay un error
                    document.cookie = "app_session_data=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                });
        } else {
            // Si no hay cookie, no se muestra nada en el usernameDisplay, solo el botón "Iniciar Sesión"
            usernameDisplay.textContent = "";
            loginLogoutLink.textContent = "Iniciar Sesión";
            loginLogoutLink.href = "login.html";
        }

        loginLogoutLink.addEventListener('click', function(event) {
            if (this.textContent === "Cerrar Sesión") {
                event.preventDefault();
                // Establece la fecha de expiración en el pasado para eliminar la cookie
                document.cookie = "app_session_data=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                window.location.reload(); // Recargar la página para actualizar el estado de la UI
            }
        });

        // Cargar productos al cargar la página
        document.addEventListener('DOMContentLoaded', loadProducts);
    </script>
</body>
</html>
EOF

# 4. admin/index.html: Panel de administración
echo "Creando admin/index.html..."
cat <<'EOF' > "${ADMIN_DIR}/index.html"
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Panel de Administración</title>
    <style>
        body { font-family: sans-serif; margin: 2em; background-color: #f4f4f4; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; }
        h1, h2 { color: #d9534f; }
        code { background: #eee; padding: 2px 5px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Panel de Administración</h1>
        <h2>Herramienta de Diagnóstico de Red</h2>
        <p>Usa esta herramienta para verificar la conectividad con otros servidores.</p>
        <form action="./diagnostics" method="GET" target="_blank">
            <label for="host">Host o IP a verificar:</label>
            <input type="text" id="host" name="host" size="50" value="8.8.8.8">
            <input type="submit" value="Ejecutar Ping">
        </form>
    </div>
</body>
</html>
EOF

# 5. DiagnosticsServlet.java: Servlet de inyección de comandos
echo "Creando DiagnosticsServlet.java..."
cat <<'EOF' > "${SRC_DIR}/DiagnosticsServlet.java"
package com.example.ecommerce;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class DiagnosticsServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/plain;charset=UTF-8");
        String host = request.getParameter("host");

        if (host == null || host.trim().isEmpty()) {
            response.getWriter().println("Error: El parámetro 'host' está vacío.");
            return;
        }

        String command = "ping -c 3 " + host; // Vulnerable a inyección de comandos

        response.getWriter().println("Ejecutando diagnóstico: " + command + "\n");

        try {
            // Este es el punto de inyección de comandos
            String[] commands = {"/bin/sh", "-c", command};
            Process process = Runtime.getRuntime().exec(commands);

            BufferedReader stdInput = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String s;
            while ((s = stdInput.readLine()) != null) {
                response.getWriter().println(s);
            }

            BufferedReader stdError = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            while ((s = stdError.readLine()) != null) {
                response.getWriter().println("ERROR: " + s);
            }
        } catch (IOException e) {
            response.getWriter().println("Excepción al ejecutar el comando: " + e.getMessage());
        }
    }
}
EOF

# 6. SessionData.java: Clase de objeto de sesión
echo "Creando SessionData.java..."
cat <<'EOF' > "${SRC_DIR}/SessionData.java"
package com.example.ecommerce;

import java.io.Serializable;
import java.util.Date;
import java.util.UUID;

public class SessionData implements Serializable {
    private static final long serialVersionUID = 1L;
    private String username;
    private String sessionId;
    private Date lastLogin;
    private int loginCount;

    public SessionData(String username, int loginCount) {
        this.username = username;
        this.sessionId = UUID.randomUUID().toString();
        this.lastLogin = new Date();
        this.loginCount = loginCount;
    }

    public String getUsername() { return username; }
    public String getSessionId() { return sessionId; }
    public Date getLastLogin() { return lastLogin; }
    public int getLoginCount() { return loginCount; }

    @Override
    public String toString() {
        return "SessionData{username='" + username + "', sessionId='" + sessionId + "', lastLogin=" + lastLogin + ", loginCount=" + loginCount + "}";
    }
}
EOF

# 7. SessionServlet.java: Servlet para deserialización insegura de la cookie
echo "Creando SessionServlet.java..."
cat <<'EOF' > "${SRC_DIR}/SessionServlet.java"
package com.example.ecommerce;

import java.io.ByteArrayInputStream;
import java.io.ObjectInputStream;
import java.io.IOException;
import java.util.Base64;
import javax.servlet.ServletException;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class SessionServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/plain;charset=UTF-8");

        Cookie[] cookies = request.getCookies();
        String sessionDataB64 = null;
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if ("app_session_data".equals(cookie.getName())) {
                    sessionDataB64 = cookie.getValue();
                    break;
                }
            }
        }

        if (sessionDataB64 == null || sessionDataB64.trim().isEmpty()) {
            response.getWriter().println("Cookie 'app_session_data' no encontrada o vacía. Inicie sesión para obtener una.");
            // No se establece el estado 404 aquí, se asume que si no hay cookie, el usuario no está logeado.
            // Para fines de la demo, permitimos que el navegador vea este mensaje.
            return;
        }

        try {
            byte[] decodedSession = Base64.getDecoder().decode(sessionDataB64);
            ByteArrayInputStream bis = new ByteArrayInputStream(decodedSession);
            ObjectInputStream ois = new ObjectInputStream(bis);
            Object obj = ois.readObject(); // Este es el punto de la vulnerabilidad de deserialización

            if (obj instanceof SessionData) {
                SessionData session = (SessionData) obj;
                response.getWriter().println("Sesión (SessionData) procesada exitosamente desde la cookie:");
                response.getWriter().println("  - Usuario: " + session.getUsername());
                response.getWriter().println("  - ID de Sesión: " + session.getSessionId());
                response.getWriter().println("  - Último Login: " + session.getLastLogin());
                response.getWriter().println("  - Conteo de Login: " + session.getLoginCount());
            } else {
                response.getWriter().println("Objeto de sesión deserializado de un tipo inesperado: " + obj.getClass().getName());
                response.getWriter().println("Se ha procesado un objeto diferente al esperado para la sesión.");
                // Podríamos considerar borrar la cookie en este caso si es una sesión mal formada.
                // Sin embargo, para la demo, mostrar el mensaje de error es suficiente.
            }

        } catch (IllegalArgumentException e) {
            response.getWriter().println("Error al decodificar la cookie 'app_session_data': El valor no es un Base64 válido. Detalle: " + e.getMessage());
            // No hay una cookie válida, se podría considerar borrarla
            response.addCookie(new Cookie("app_session_data", "") {{ setMaxAge(0); setPath("/"); }}); // Borrar cookie inválida
        } catch (ClassNotFoundException e) {
            response.getWriter().println("Error durante la deserialización de la cookie: Clase de objeto no encontrada. Detalle: " + e.getMessage());
            response.addCookie(new Cookie("app_session_data", "") {{ setMaxAge(0); setPath("/"); }}); // Borrar cookie inválida
        } catch (IOException e) {
            response.getWriter().println("Error de entrada/salida durante el procesamiento de la cookie de sesión: " + e.getMessage());
            response.addCookie(new Cookie("app_session_data", "") {{ setMaxAge(0); setPath("/"); }}); // Borrar cookie inválida
        } catch (Exception e) {
            response.getWriter().println("Error inesperado durante el procesamiento de la cookie de sesión: " + e.getClass().getName() + ": " + e.getMessage());
            response.addCookie(new Cookie("app_session_data", "") {{ setMaxAge(0); setPath("/"); }}); // Borrar cookie inválida
        }
    }
}
EOF

# 8. ReviewServlet.java: Ahora solo para reseñas de texto plano
echo "Creando ReviewServlet.java..."
cat <<'EOF' > "${SRC_DIR}/ReviewServlet.java"
package com.example.ecommerce;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class ReviewServlet extends HttpServlet {
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/plain;charset=UTF-8");

        String reviewText = request.getParameter("reviewText");

        if (reviewText == null || reviewText.trim().isEmpty()) {
            response.getWriter().println("Error: No se encontraron datos de la reseña.");
            return;
        }

        response.getWriter().println("Reseña de texto plano recibida exitosamente:");
        response.getWriter().println("  - Contenido: \"" + reviewText + "\"");
        response.getWriter().println("¡Gracias por tu opinión!");
    }
}
EOF

# 9. DatabaseUtil.java: Clase de utilidad para la conexión a la base de datos
echo "Actualizando DatabaseUtil.java para usar DataSource JNDI..."
cat <<'EOF' > "${SRC_DIR}/DatabaseUtil.java"
package com.example.ecommerce;

import java.sql.Connection;
import java.sql.SQLException;
import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.sql.DataSource;

public class DatabaseUtil {
    private static DataSource dataSource;

    static {
        try {
            Context initialContext = new InitialContext();
            dataSource = (DataSource) initialContext.lookup("jdbc/ecommerceDB");
            System.out.println("DataSource 'jdbc/ecommerceDB' encontrado con éxito.");
        } catch (NamingException e) {
            // Este error ocurre si el recurso JNDI no está configurado en Payara.
            // Es un error crítico al inicio de la aplicación.
            System.err.println("ERROR CRÍTICO: No se pudo encontrar el recurso JNDI 'jdbc/ecommerceDB'. " +
                               "Asegúrate de que el JDBC Connection Pool y JDBC Resource estén configurados correctamente en Payara.");
            e.printStackTrace();
            // No lanzar excepción aquí directamente, para que el servidor pueda arrancar,
            // pero las llamadas a getConnection() fallarán.
        }
    }

    public static Connection getConnection() throws SQLException {
        if (dataSource == null) {
            // Si el DataSource no se pudo inicializar (ej. por error JNDI),
            // lanzamos una excepción SQL clara.
            throw new SQLException("Error de conexión a la base de datos: El DataSource 'jdbc/ecommerceDB' no está disponible. " +
                                   "Por favor, revisa la configuración de Payara y la conexión a la base de datos externa (PostgreSQL).");
        }
        try {
            return dataSource.getConnection();
        } catch (SQLException e) {
            // Capturar errores de conexión específicos (ej. DB no accesible)
            System.err.println("Error al obtener conexión de la base de datos: " + e.getMessage());
            throw new SQLException("Fallo al obtener una conexión de la base de datos. " +
                                   "Verifica que la base de datos PostgreSQL esté activa y accesible. Detalle: " + e.getMessage(), e);
        }
    }
}
EOF

# 10. Product.java: Clase para representar un producto
echo "Creando Product.java..."
cat <<'EOF' > "${SRC_DIR}/Product.java"
package com.example.ecommerce;

public class Product {
    private int id;
    private String name;
    private String description;
    private double price;
    private String imageUrl;

    public Product(int id, String name, String description, double price, String imageUrl) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.price = price;
        this.imageUrl = imageUrl;
    }

    // Getters
    public int getId() { return id; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public double getPrice() { return price; }
    public String getImageUrl() { return imageUrl; }

    // Setters (opcionales, dependiendo de si se va a modificar el objeto después de la creación)
    public void setId(int id) { this.id = id; }
    public void setName(String name) { this.name = name; }
    public void setDescription(String description) { this.description = description; }
    public void setPrice(double price) { this.price = price; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }
}
EOF

# 11. ProductServlet.java: Servlet para cargar productos desde la BD.
echo "Creando ProductServlet.java..."
cat <<'EOF' > "${SRC_DIR}/ProductServlet.java"
package com.example.ecommerce;

import com.google.gson.Gson;
import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class ProductServlet extends HttpServlet {
    private Gson gson = new Gson();

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("application/json;charset=UTF-8");
        List<Product> products = new ArrayList<>();

        try (Connection conn = DatabaseUtil.getConnection();
             PreparedStatement stmt = conn.prepareStatement("SELECT id, name, description, price, image_url FROM products");
             ResultSet rs = stmt.executeQuery()) {

            while (rs.next()) {
                int id = rs.getInt("id");
                String name = rs.getString("name");
                String description = rs.getString("description");
                double price = rs.getDouble("price");
                String imageUrl = rs.getString("image_url");
                products.add(new Product(id, name, description, price, imageUrl));
            }
        } catch (SQLException e) {
            System.err.println("Error de base de datos al obtener productos: " + e.getMessage());
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR); // Código 500
            // Mensaje genérico para el cliente, log detallado en el servidor
            response.getWriter().write(gson.toJson("Error interno del servidor al cargar productos. Por favor, revisa la conexión a la base de datos."));
            return;
        }

        response.getWriter().write(gson.toJson(products));
    }
}
EOF

# 12. LoginServlet.java: Maneja el login.
echo "Creando LoginServlet.java..."
cat <<'EOF' > "${SRC_DIR}/LoginServlet.java"
package com.example.ecommerce;

import java.io.ByteArrayOutputStream;
import java.io.ObjectOutputStream;
import java.io.IOException;
import java.util.Base64;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import javax.servlet.ServletException;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class LoginServlet extends HttpServlet {

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/plain;charset=UTF-8");

        String username = request.getParameter("username");
        String password = request.getParameter("password");
        String rememberMe = request.getParameter("rememberMe");
        boolean isRememberMe = "on".equals(rememberMe);

        if (username == null || password == null || username.trim().isEmpty() || password.trim().isEmpty()) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST); // 400 Bad Request
            response.getWriter().println("Usuario y contraseña no pueden estar vacíos.");
            return;
        }

        boolean isAuthenticated = false;
        String actualUsername = null;
        try (Connection conn = DatabaseUtil.getConnection();
             PreparedStatement stmt = conn.prepareStatement("SELECT username FROM users WHERE username = ? AND password = ?")) {
            stmt.setString(1, username);
            stmt.setString(2, password);
            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    isAuthenticated = true;
                    actualUsername = rs.getString("username");
                }
            }
        } catch (SQLException e) {
            System.err.println("Error de base de datos durante el login: " + e.getMessage());
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR); // 500 Internal Server Error
            response.getWriter().println("Error interno del servidor al intentar iniciar sesión. Por favor, revisa la conexión a la base de datos.");
            return;
        }

        if (isAuthenticated) {
            SessionData session = new SessionData(actualUsername, 1);
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            ObjectOutputStream oos = new ObjectOutputStream(bos);
            try {
                oos.writeObject(session);
                oos.close();
                String base64Encoded = Base64.getEncoder().encodeToString(bos.toByteArray());

                Cookie sessionCookie = new Cookie("app_session_data", base64Encoded);
                sessionCookie.setPath("/");
                // sessionCookie.setHttpOnly(true); // Descomentar en producción para seguridad
                // sessionCookie.setSecure(true); // Descomentar si se usa HTTPS en producción

                if (isRememberMe) {
                    sessionCookie.setMaxAge(7 * 24 * 60 * 60); // 7 días en segundos
                } else {
                    sessionCookie.setMaxAge(-1); // Cookie de sesión (se borra al cerrar el navegador)
                }

                response.addCookie(sessionCookie);

                response.setStatus(HttpServletResponse.SC_OK); // 200 OK
                response.getWriter().println("Inicio de sesión exitoso. Cookie de sesión establecida.");

            } catch (IOException e) {
                System.err.println("Error al serializar SessionData o establecer cookie: " + e.getMessage());
                response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR); // 500 Internal Server Error
                response.getWriter().println("Error interno al generar la cookie de sesión.");
            }

        } else {
            // Si las credenciales son inválidas, no hay cookie de sesión.
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED); // 401 Unauthorized
            response.getWriter().println("Credenciales inválidas. Por favor, verifique su usuario y contraseña.");
        }
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.sendRedirect("login.html");
    }
}
EOF

# 13. login.html: Página de inicio de sesión
echo "Actualizando login.html con el enlace 'Registrarse'..."
cat <<'EOF' > "${WEBAPP_DIR}/login.html"
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesión - Vuln-Tech</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            margin: 0;
            background-color: #f0f2f5;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-container {
            background-color: #fff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        h2 {
            color: #007bff;
            margin-bottom: 30px;
            font-weight: 700;
        }
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        .form-group input[type="text"],
        .form-group input[type="password"] {
            width: calc(100% - 24px); /* Padding */
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: 1em;
            box-sizing: border-box; /* Include padding in width */
        }
        .form-group input[type="submit"] {
            background-color: #007bff;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            transition: background-color 0.3s ease;
            width: 100%;
            margin-top: 10px;
        }
        .form-group input[type="submit"]:hover {
            background-color: #0056b3;
        }
        .message {
            margin-top: 20px;
            padding: 10px;
            border-radius: 6px;
            font-weight: 600;
        }
        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .back-link {
            display: block;
            margin-top: 25px;
            color: #007bff;
            text-decoration: none;
            font-size: 0.9em;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .remember-me-group {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin-bottom: 20px;
            margin-top: -10px;
        }
        .remember-me-group input[type="checkbox"] {
            margin-right: 8px;
            width: auto;
        }
        .remember-me-group label {
            margin-bottom: 0;
            font-weight: normal;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Iniciar Sesión</h2>
        <div id="message" class="message" style="display: none;"></div>
        <form id="loginForm" action="./login" method="POST">
            <div class="form-group">
                <label for="username">Usuario:</label>
                <input type="text" id="username" name="username" required value="testuser">
            </div>
            <div class="form-group">
                <label for="password">Contraseña:</label>
                <input type="password" id="password" name="password" required value="password123">
            </div>
            <div class="remember-me-group">
                <input type="checkbox" id="rememberMe" name="rememberMe">
                <label for="rememberMe">Recuérdame</label>
            </div>
            <div class="form-group">
                <input type="submit" value="Acceder">
            </div>
        </form>
        <a href="register.html" class="back-link">¿No tienes usuario? Regístrate aquí.</a>
        <a href="index.html" class="back-link">Volver a la tienda</a>
    </div>

    <script>
        const loginForm = document.getElementById('loginForm');
        const messageDiv = document.getElementById('message');

        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const formData = new FormData(loginForm);

            fetch(loginForm.action, {
                method: 'POST',
                body: new URLSearchParams(formData).toString(),
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })
            .then(response => {
                // Capturar el texto del error si la respuesta no es OK
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text); });
                }
                return response.text(); // Devuelve el texto si es OK
            })
            .then(text => { // 'text' será el mensaje de éxito del servlet
                messageDiv.textContent = '¡Inicio de sesión exitoso! Redireccionando...';
                messageDiv.className = 'message success';
                messageDiv.style.display = 'block';
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            })
            .catch(error => {
                messageDiv.textContent = 'Error al iniciar sesión: ' + error.message;
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
            });
        });
    </script>
</body>
</html>
EOF

# 14. register.html: Página de registro
echo "Creando register.html..."
cat <<'EOF' > "${WEBAPP_DIR}/register.html"
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrarse - Vuln-Tech</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            margin: 0;
            background-color: #f0f2f5;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .register-container {
            background-color: #fff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 450px;
            text-align: center;
        }
        h2 {
            color: #28a745; /* Color verde para registro */
            margin-bottom: 30px;
            font-weight: 700;
        }
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        .form-group input[type="text"],
        .form-group input[type="password"],
        .form-group input[type="email"] {
            width: calc(100% - 24px); /* Padding */
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: 1em;
            box-sizing: border-box; /* Include padding in width */
        }
        .form-group input[type="submit"] {
            background-color: #28a745; /* Color verde para botón de registro */
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            transition: background-color 0.3s ease;
            width: 100%;
            margin-top: 10px;
        }
        .form-group input[type="submit"]:hover {
            background-color: #218838;
        }
        .message {
            margin-top: 20px;
            padding: 10px;
            border-radius: 6px;
            font-weight: 600;
        }
        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .back-link {
            display: block;
            margin-top: 25px;
            color: #007bff;
            text-decoration: none;
            font-size: 0.9em;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="register-container">
        <h2>Crear Nueva Cuenta</h2>
        <div id="message" class="message" style="display: none;"></div>
        <form id="registerForm" action="./register" method="POST">
            <div class="form-group">
                <label for="username">Nombre de Usuario:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="password">Contraseña:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-group">
                <input type="submit" value="Registrarse">
            </div>
        </form>
        <a href="login.html" class="back-link">¿Ya tienes cuenta? Inicia Sesión aquí.</a>
        <a href="index.html" class="back-link">Volver a la tienda</a>
    </div>

    <script>
        const registerForm = document.getElementById('registerForm');
        const messageDiv = document.getElementById('message');

        registerForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Evitar el envío normal del formulario

            const formData = new FormData(registerForm);

            fetch(registerForm.action, {
                method: 'POST',
                body: new URLSearchParams(formData).toString(),
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text); });
                }
                return response.text();
            })
            .then(text => {
                messageDiv.textContent = '¡Registro exitoso! Redireccionando al login...';
                messageDiv.className = 'message success';
                messageDiv.style.display = 'block';
                setTimeout(() => {
                    window.location.href = 'login.html'; // Redirigir a la página de login
                }, 2000);
            })
            .catch(error => {
                messageDiv.textContent = 'Error al registrarse: ' + error.message;
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
            });
        });
    </script>
</body>
</html>
EOF


# 15. RegisterServlet.java: Maneja el registro de usuarios
echo "Creando RegisterServlet.java..."
cat <<'EOF' > "${SRC_DIR}/RegisterServlet.java"
package com.example.ecommerce;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet; // Importar ResultSet para la verificación de existencia
import java.sql.SQLException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class RegisterServlet extends HttpServlet {
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/plain;charset=UTF-8");

        String username = request.getParameter("username");
        String email = request.getParameter("email");
        String password = request.getParameter("password");

        if (username == null || username.trim().isEmpty() ||
            email == null || email.trim().isEmpty() ||
            password == null || password.trim().isEmpty()) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().println("Todos los campos (usuario, email, contraseña) son obligatorios.");
            return;
        }

        try (Connection conn = DatabaseUtil.getConnection()) {
            // Verificar si el usuario o email ya existen
            String checkSql = "SELECT COUNT(*) FROM users WHERE username = ? OR email = ?";
            try (PreparedStatement checkStmt = conn.prepareStatement(checkSql)) {
                checkStmt.setString(1, username);
                checkStmt.setString(2, email);
                try (ResultSet rs = checkStmt.executeQuery()) {
                    if (rs.next() && rs.getInt(1) > 0) {
                        response.setStatus(HttpServletResponse.SC_CONFLICT); // 409 Conflict
                        response.getWriter().println("El nombre de usuario o email ya está en uso. Por favor, elija otro.");
                        return;
                    }
                }
            }

            // Si no existe, proceder con la inserción
            String insertSql = "INSERT INTO users (username, email, password) VALUES (?, ?, ?)";
            try (PreparedStatement stmt = conn.prepareStatement(insertSql)) {
                stmt.setString(1, username);
                stmt.setString(2, email);
                stmt.setString(3, password); // NOTA: En una aplicación real, las contraseñas DEBEN ser hasheadas y salteadas.

                int rowsAffected = stmt.executeUpdate();

                if (rowsAffected > 0) {
                    response.setStatus(HttpServletResponse.SC_OK);
                    response.getWriter().println("¡Registro exitoso para el usuario: " + username + "!");
                } else {
                    response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                    response.getWriter().println("No se pudo registrar el usuario. Por favor, intente de nuevo.");
                }
            }

        } catch (SQLException e) {
            System.err.println("Error de base de datos durante el registro: " + e.getMessage());
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            response.getWriter().println("Error interno del servidor durante el registro. Por favor, revisa la conexión a la base de datos.");
        }
    }
}
EOF


# --- Proceso de Construcción y Limpieza ---
echo "Navegando al directorio del proyecto: ${BASE_DIR}"
cd "${BASE_DIR}" || { echo "Error: No se pudo navegar al directorio del proyecto."; exit 1; }

echo "Limpiando y construyendo el proyecto Maven..."
# El "clean" asegura que se borren compilaciones anteriores.
# El "package" compila y empaqueta el WAR.
mvn clean package

if [ $? -eq 0 ]; then
    echo "Construcción de la aplicación exitosa. Archivo WAR generado:"
    ls -lh target/*.war
    # Mover el WAR al directorio actual para fácil acceso
    mv target/*.war "${CURRENT_DIR}/"
    echo "Archivo WAR movido a: ${CURRENT_DIR}/vulnerable-ecommerce.war"
else
    echo "ERROR: Falló la construcción de la aplicación Maven."
fi

echo "Limpiando el directorio temporal del proyecto: ${BASE_DIR}"
cd "${CURRENT_DIR}"
rm -rf "${BASE_DIR}"

echo "Proceso completado."
