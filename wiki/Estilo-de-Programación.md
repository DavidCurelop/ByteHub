# Guía de Estilo de Programación

Este documento define el estándar de escritura de código para garantizar que el proyecto sea legible y mantenible por cualquier miembro del equipo.

---

## 📐 Estándares Generales

| Estándar | Regla |
|---|---|
| **Lenguaje** | El código (nombres de variables, funciones, clases) debe escribirse en **Inglés**. Los comentarios pueden ser en Español si facilitan la explicación de lógica compleja. |
| **Formato de Archivo** | Usar codificación **UTF-8**. |
| **Indentación** | Utilizar **4 espacios** por nivel. No usar tabulaciones (Tabs). |
| **Longitud de Línea** | Máximo **79 caracteres** para código y **72** para bloques de texto/docstrings. |

---

## 🏷️ Nombramiento (Naming Conventions)

| Elemento | Convención | Ejemplo |
|---|---|---|
| **Clases** | `PascalCase` | `ProductCatalog`, `UserProfile` |
| **Funciones y Variables** | `snake_case` | `calculate_total()`, `user_id` |
| **Constantes** | `SCREAMING_SNAKE_CASE` | `MAX_PAGINATION_LIMIT` |
| **Modelos de Django** | Siempre en singular | `Product` (no `Products`) |

---

## 🔀 Reglas de Git y Commits

Se debe seguir el estándar de [Conventional Commits](https://www.conventionalcommits.org/):

| Tipo | Descripción |
|---|---|
| `feat` | Nueva funcionalidad. |
| `fix` | Corrección de un error. |
| `docs` | Cambios en documentación. |
| `refactor` | Cambio de código que no corrige errores ni añade funciones. |

---

> 📌 Para más detalles sobre las reglas de arquitectura, ver [Reglas de Programación](Reglas-de-Programación).
