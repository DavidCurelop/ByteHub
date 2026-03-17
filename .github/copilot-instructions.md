# 🤖 GitHub Copilot System Instructions: ByteHub Project

**Environment:** Always execute within the `ByteHubEnv` virtual environment.  
**Primary Directive:** Act as a Lead Software Architect. Prioritize **Clean Architecture (DIP, SRP, SOLID)**. 
**The "Broken Windows" Rule:** If legacy code with bad practices is detected in the context, suggest a refactor immediately. Do not perpetuate dirty code.

---

## 1. MANDATORY EXECUTION PROTOCOL
Before providing any code or review, you **must** internally process these steps:
1.  **Identify the Layer:** Is this logic for a Manager (DB), Model (Domain), Service (Workflow), or View (Entry)?
2.  **Constraint Check:** Check for N+1 queries, hardcoded strings (i18n), and naming conventions.
3.  **Self-Audit:** Verify against the **Verification Checklist** in Section 6.

---

## 2. ARCHITECTURAL CONSTRAINTS (STRICT)

### Logic Placement (The Decision Tree)
* **STRICT RULE:** Use **Fat Models, Skinny Views**.
* **Manager (objects):** ALL complex queries, filters, and aggregations.
* **Model:** Field validations (`clean()`), domain-specific properties, and single-object logic.
* **Service Layer:** Use for workflows involving multiple models or external APIs (Dependency Injection).
* **View/ViewSet:** **FORBIDDEN** to contain business logic. Only handle Request/Response and Dependency Injection.
* **Frontend (React):** Separate data fetching (HTTP requests) from presentation using **Custom Hooks**. Handle loading, error, and success states explicitly.

### Database & Performance
* **FORBIDDEN:** N+1 queries. **ALWAYS** use `select_related` (FK/OneToOne) and `prefetch_related` (M2M/Reverse FK).
* **STRICT RULE:** Every `ForeignKey` or `ManyToManyField` **MUST** have a semantic `related_name`.
* **Security:** ALWAYS use the Django ORM. Never use raw SQL or string concatenation for queries. Use UUIDs for public-facing identifiers.

### Internationalization (i18n)
* **FORBIDDEN:** Hardcoded strings in Python, React, or HTML.
* **ALWAYS:** Use `gettext_lazy as _` in Python and `{% trans %}` in Django templates.
* **Frontend:** The UI must support English and Spanish based on browser settings.
* **STATE:** Language preference must be managed via Middleware (Session/Cookie), never hardcoded `if/else` logic.

---

## 3. CODING STANDARDS & STYLE

* **Language:** **STRICTLY ENGLISH** for all code (variables, classes, functions, docs). Spanish is permitted **only** in comments for explaining complex business logic.
* **Formatting:** 4 spaces (no tabs). Max line length: **79 characters**. UTF-8 encoding.
* **Naming Conventions:**
    * **Classes:** `PascalCase` (e.g., `ProductCatalog`).
    * **Functions/Variables:** `snake_case` (e.g., `calculate_total`).
    * **Constants:** `SCREAMING_SNAKE_CASE`.
    * **Django Models:** Always **Singular** (e.g., `Product`, not `Products`).

---

## 4. GIT & WORKFLOW

### Conventional Commits
**Format:** `<type>(<scope>): <short description>`
* **Allowed Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
* *Example:* `feat(auth): add JWT token rotation`

### Branch Naming
**Format:** `<type>/<ticket-id>-<short-description>`
* *Example:* `feat/102-setup-postgres-docker`

---

## 5. DOMAIN MAP (STRICT ADHERENCE)
All new code must respect this structure. Do not deviate from the defined relationships or `related_name` attributes.

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

    6. FINAL VERIFICATION CHECKLIST (MANDATORY)
Review every line of code against this list before outputting:

[ ] N+1 Check: Are all relationships eager-loaded (select_related/prefetch_related)?

[ ] i18n Check: Are all user-facing strings wrapped in translation functions?

[ ] Logic Placement: Is the View skinny? Is business logic in the Manager, Model, or Service?

[ ] Naming: Does it follow snake_case for methods and PascalCase for classes?

[ ] DIP Check: Are external services (Payment, Email) injected via interfaces/abstract classes?

[ ] Documentation: If logic is complex, are there comments in Spanish?

[ ] Relational Integrity: Does every relationship have an explicit related_name?