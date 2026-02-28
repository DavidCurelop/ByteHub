# Instrucciones para GitHub Copilot: Desarrollo Limpio en Django + React

## 1. Rol y Filosofía Principal
Actúa como un Arquitecto de Software y Desarrollador Senior experto en Python (Django) y JavaScript/TypeScript (React). Tu objetivo principal es generar código limpio, mantenible y escalable, aplicando los principios de Clean Architecture.
* **Regla de las "Ventanas Rotas":** Si detectas código legado con malas prácticas en el contexto, sugiere refactorizaciones inmediatamente. No perpetúes el código sucio.
* **Principios SOLID:** Aplica Responsabilidad Única (SRP) y, muy especialmente, Inversión de Dependencias (DIP). Las clases y módulos de alto nivel no deben depender de los de bajo nivel.

## 2. Convenciones de Control de Versiones (Git)
Cuando sugieras comandos de Git o nombres para ramas y commits, adhiérete estrictamente a las convenciones del proyecto:
* **Commits:** Usa *Conventional Commits* (`<type>(<scope>): <short description>`). Tipos permitidos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
* **Ramas:** Usa el formato `<type>/<ticket-id>-<short-description>` todo en minúsculas (ej. `feat/123-login-react`).

## 3. Backend: Reglas para Django (API REST)
El backend actúa como servidor de recursos para la aplicación React. Todo el código de Django debe seguir estas directrices:
* **Patrón MVC / MVT:** Mantén los "Controladores" (Views/ViewSets en Django) lo más delgados posible. La lógica de negocio pesada debe ir en servicios o en los Modelos (Fat Models, Skinny Controllers).
* **Rutas (URLs):** Diseña rutas lógicas, legibles y seguras. No expongas IDs sensibles si no es necesario (prefiere UUIDs).
* **Optimización de Base de Datos (ORM):** Evita el problema de consultas N+1 (Lazy Loading). Siempre que consultes relaciones, utiliza `select_related` (para relaciones *Foreign Key* o *One-to-One*) y `prefetch_related` (para relaciones *Many-to-Many* o *Reverse Foreign Key*) para forzar el *Eager Loading*.
* **Inversión e Inyección de Dependencias:** Para servicios externos (almacenamiento, APIs de terceros, correos), utiliza interfaces o clases abstractas. Inyecta estas dependencias para facilitar el testing y la modularidad.
* **Seguridad:** Usa siempre el ORM de Django. NUNCA generes consultas SQL crudas o concatenación de strings para interactuar con la base de datos (prevención de inyección SQL).
* **Tests:** Acompaña la lógica de negocio con pruebas unitarias (`tests.py`) enfocadas en el comportamiento, no solo en la cobertura. Usa herramientas como *Faker* para generar datos de prueba.

## 4. Frontend: Reglas para React
El frontend es el cliente que consume la API de Django. 
* **Componentes:** Crea componentes modulares, reutilizables y con una única responsabilidad. Sigue el principio DRY (Don't Repeat Yourself).
* **Estado y Efectos:** Separa la lógica de obtención de datos (peticiones HTTP a Django) de la lógica de presentación utilizando *Custom Hooks*.
* **Interactividad y Usabilidad:** Asegúrate de manejar los estados de carga (loading), errores y éxito al interactuar con el servidor HTTP (que por naturaleza es *stateless*).

## 5. Infraestructura y Despliegue (Docker)
Si se solicitan configuraciones de entorno:
* Genera `Dockerfile` y `docker-compose.yml` siguiendo las mejores prácticas: imágenes base ligeras (ej. `python:3.X-slim`, `node:alpine`), separación de etapas de construcción (*multi-stage builds*) y uso de volúmenes de manera eficiente.
* Mantén los contenedores inmutables e independientes.

# Guía de Estilo de Programación

Este documento define el estándar de escritura de código para garantizar
que el proyecto sea legible y mantenible por cualquier miembro del equipo.

## Estándares Generales

- **Lenguaje:**  
  El código (nombres de variables, funciones, clases) debe escribirse en
  Inglés. Los comentarios pueden ser en Español si facilitan la explicación
  de lógica compleja.

- **Formato de Archivo:**  
  Usar codificación UTF-8.

- **Indentación:**  
  Utilizar 4 espacios por nivel. No usar tabulaciones (Tabs).

- **Longitud de Línea:**  
  Máximo 79 caracteres para código y 72 para bloques de texto/docstrings.

## Nombramiento (Naming Conventions)

- **Clases:**  
  PascalCase  
  Ej: `ProductCatalog`, `UserProfile`

- **Funciones y Variables:**  
  snake_case  
  Ej: `calculate_total()`, `user_id`

- **Constantes:**  
  SCREAMING_SNAKE_CASE  
  Ej: `MAX_PAGINATION_LIMIT`

- **Modelos de Django:**  
  Siempre en singular  
  Ej: `Product`, no `Products`

## Reglas de Git y Commits  
*(Basado en CONTRIBUTING.md)*

Se debe seguir el estándar de **Conventional Commits**:

- `feat:` Nueva funcionalidad.
- `fix:` Corrección de un error.
- `docs:` Cambios en documentación.
- `refactor:` Cambio de código que no corrige errores ni añade funciones.

# Reglas de Arquitectura y Estructura del Proyecto

Estas reglas son obligatorias para mantener la **Clean Architecture**
y el principio de responsabilidad única.

## Modelos (Capa de Datos)

- **Lógica de Negocio:**  
  Aplicar el principio de *Fat Models, Skinny Views*.  
  La lógica que pertenezca al dominio debe estar en el modelo.

- **Relaciones Reversas:**  
  Toda `ForeignKey` o `ManyToManyField` debe definir un
  `related_name` explícito y semántico.  
  Ej: `comments` en lugar del valor por defecto `comment_set`.

- **Consultas Eficientes:**  
  Está prohibido generar consultas N+1.  
  Se debe usar `select_related` para llaves foráneas y
  `prefetch_related` para relaciones muchos a muchos.

- **Validación:**  
  Las reglas de integridad deben validarse en el método `clean()`
  del modelo.

## Controladores (Views)

- **Inyección de Dependencias:**  
  Las vistas no deben instanciar clases concretas de servicios
  externos directamente.  
  Se deben usar *Providers* o inyectar dependencias para facilitar
  las pruebas unitarias.

- **Responsabilidad Única:**  
  Una vista solo debe encargarse de procesar la petición del usuario
  y devolver una respuesta.  
  No debe contener consultas complejas a la base de datos sin procesar.

- **DRY (Don't Repeat Yourself):**  
  Si una lógica de filtrado se repite en varias vistas, debe moverse
  a un Manager personalizado en el modelo.

## Vistas (Templates)

- **Herencia de Plantillas:**  
  Todos los archivos de template deben iniciar con:  
  `{% extends 'base.html' %}`

- **Uso de Partials:**  
  Componentes reutilizables (headers, footers, cards) deben estar en  
  `templates/partials/` e incluirse con `{% include %}`.

- **Lógica en el Template:**  
  Está prohibido realizar lógica compleja.  
  Si el HTML requiere más de un `if` o `for` anidado, esa lógica debe
  procesarse en la vista o mediante un `template_tag`.

- **Formatos:**  
  Todos los archivos de visualización deben tener extensión `.html`.

## Rutas (URLs)

- **Espacios de Nombres:**  
  Cada aplicación de Django debe definir su `app_name` y sus rutas
  deben ser incluidas en el `urls.py` principal usando `namespace`.

- **Nombres de Ruta:**  
  Todas las rutas deben tener un atributo `name` único.  
  Ej:  
  `path('list/', ProductListView.as_view(), name='product-list')`

- **URLs Limpias:**  
  Las rutas deben ser descriptivas y en minúsculas.  
  Evitar parámetros innecesarios en la query string si pueden ir en
  el path.

## Despliegue y Entorno (Containers)

- **Dockerización:**  
  El proyecto debe contener un `Dockerfile` y un `docker-compose.yml`.  
  El código debe ser agnóstico al entorno (usar variables de entorno
  para la DB y `SECRET_KEY`).

- **Dependencias:**  
  Todas las librerías deben estar listadas en un archivo
  `requirements.txt` con sus versiones exactas.

## El codigo se basa en el siguiente diagrama de clases: 
classDiagram
    direction TB

    %% --------------------------------------------------------
    %% PATRÓN REPOSITORIO / MANAGERS (DRY & Consultas Eficientes)
    %% --------------------------------------------------------
    class UserManager {
        +get_all_admins() QuerySet
        +get_active_clients_with_orders() QuerySet
    }

    class ProductManager {
        +get_active_products_with_reviews() QuerySet
        +get_products_by_category(category_slug) QuerySet
        +get_products_managed_by(admin_id) QuerySet
    }

    class OrderManager {
        +get_user_orders_with_details(user_id) QuerySet
        +get_store_sales_summary(date_range) Dictionary
    }

    %% --------------------------------------------------------
    %% MODELOS (Fat Models, Lógica de Dominio, Validación clean())
    %% --------------------------------------------------------
    class User {
        +int id
        +String email
        +String password
        +String first_name
        +String last_name
        +String phone
        +bool is_admin
        +bool is_active
        +DateTime created_at
        +UserManager objects$
        +clean() void
        +has_admin_privileges() bool
        +get_client_lifetime_value() Decimal
    }

    class Address {
        +int id
        +User user
        +String street
        +String city
        +String state
        +String zip_code
        +String country
        +bool is_default
        +clean() void
    }

    class Category {
        +int id
        +String name
        +String slug
        +String description
        +Category parent
        +User created_by
        +clean() void
    }

    class Product {
        +int id
        +String name
        +String slug
        +String description
        +String brand
        +Decimal price
        +int stock
        +String image
        +bool is_available
        +Category category
        +User created_by
        +DateTime created_at
        +ProductManager objects$
        +clean() void
        +float avg_rating()
        +int total_sold()
        +int total_reviews()
    }

    class Cart {
        +int id
        +User user
        +DateTime created_at
        +DateTime updated_at
        +clean() void
        +Decimal get_total()
        +int get_item_count()
    }

    class CartItem {
        +int id
        +Cart cart
        +Product product
        +int quantity
        +clean() void
        +Decimal get_subtotal()
    }

    class Order {
        +int id
        +User user
        +Address shipping_address
        +String status
        +Decimal subtotal
        +Decimal shipping_cost
        +Decimal total_amount
        +DateTime created_at
        +OrderManager objects$
        +clean() void
    }

    class OrderItem {
        +int id
        +Order order
        +Product product
        +int quantity
        +Decimal unit_price
        +clean() void
        +Decimal get_subtotal()
    }

    class Payment {
        +int id
        +Order order
        +String payment_method
        +String transaction_id
        +String status
        +DateTime paid_at
        +Decimal amount
        +clean() void
    }

    class Review {
        +int id
        +Product product
        +User user
        +int rating
        +String title
        +String body
        +bool is_verified_purchase
        +DateTime created_at
        +clean() void
    }

    %% --------------------------------------------------------
    %% PROVIDERS / SERVICIOS (Inyección de Dependencias para Vistas)
    %% --------------------------------------------------------
    class IPaymentProvider {
        <<interface>>
        +process_payment(amount, method, data) PaymentResult
    }

    class StripePaymentProvider {
        +process_payment(amount, method, data) PaymentResult
    }

    class IInvoiceProvider {
        <<interface>>
        +generate_pdf(order) File
    }

    class PDFInvoiceProvider {
        +generate_pdf(order) File
    }

    IPaymentProvider <|.. StripePaymentProvider
    IInvoiceProvider <|.. PDFInvoiceProvider

    %% --------------------------------------------------------
    %% RELACIONES CON RELATED_NAME EXPLÍCITO (Semántica)
    %% --------------------------------------------------------
    
    %% Relaciones del Administrador (Auditoría/Gestión)
    User "1" <-- "0..*" Product : related_name="managed_products" (Admin)
    User "1" <-- "0..*" Category : related_name="managed_categories" (Admin)

    %% Relaciones del Cliente (Tienda)
    User "1" --> "0..*" Address : related_name="addresses" (Client)
    User "1" <-- "0..*" Cart : related_name="carts" (Client)
    User "1" <-- "0..*" Order : related_name="orders" (Client)
    User "1" <-- "0..*" Review : related_name="reviews" (Client)

    %% Otras relaciones del dominio
    Category "0..*" --> "0..1" Category : related_name="subcategories"
    Product "0..*" --> "1" Category : related_name="products"
    
    Cart "1" --> "0..*" CartItem : related_name="items"
    CartItem "0..*" --> "1" Product : related_name="cart_items"
    
    Order "0..*" --> "1" Address : related_name="shipping_address"
    Order "1" --> "1..*" OrderItem : related_name="items"
    Order "1" --> "0..1" Payment : related_name="payment"
    OrderItem "0..*" --> "1" Product : related_name="order_items"
    
    Review "0..*" --> "1" Product : related_name="reviews"

    %% Relación Lógica (Managers -> Modelos)
    UserManager --> User : manages
    ProductManager --> Product : manages
    OrderManager --> Order : manages 