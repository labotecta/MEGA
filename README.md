
### *Todo el material del repositorio, incluido el código de las aplicaciones es de libre utilización, pero esperamos que su uso se acompañe de la cita correspondiente, de acuerdo con las normas habituales de citación.*
### *Así mismo nos gustaría recibir, si es posible, una copia de los modelos que se construyan a partir de este material.*

___

## Este es el repositorio del Libro "Guía práctica para Modelos de Equilibrio General Aplicado (MEGA)"
## "Computable General Equilibrium (CGE)"
## Publicado en la Editorial universitaria Aula Magna McGraw Hill
## [Ver en la tienda del autor](https://libros.cc/autor/Alberto-Ba%C3%B1%C3%B3n-Serrano.htm)
El libro muestra cómo construir y resolver un Modelo de Equilibrio General Aplicado (MEGA), sin conocimientos previos y desde el principio. Una parte importante será el planteamiento y resolución de escenarios que, en definitiva, es lo que se pretende con un MEGA. El libro no se limita a exponer cómo construir un modelo, en él se construye uno plenamente operativo. El código fuente de la aplicación informática (Python y C++) está disponible en un repositorio público y es de libre utilización, así como los datos utilizados en el calibrado y resolución de los escenarios tratados en este libro.

___

# MEGA
Un modelo de equilibrio general aplicado (MEGA) define una serie de magnitudes o variables de importancia económica y las ecuaciones que las relacionan entre sí. Como las relaciones en economía son de carácter circular, algunas ecuaciones hacen uso de valores que son el resultado de otras ecuaciones que a su vez dependen de las primeras. Una vez planteado el modelo, hay que resolver las ecuaciones, es decir, que valores han de tener las variables, para que todas las ecuaciones se cumplan de forma simultánea. Rara vez, por no decir nunca, estaremos ante un sistema de ecuaciones lineales y hay que recurrir a software de resolución de ecuaciones no lineales. Aunque la resolución de ecuaciones no tiene nada que ver con el óptimo de ninguna función, la resolución se suele plantear como un problema de minimización (o maximización) de alguna función objetivo sometida a restricciones, ya que para esto hay disponible software comercial y de libre utilización. Que función objetivo utilizar es irrelevante y lo que se busca es que el software nos encuentre una solución en la que se cumplan las restricciones que no serán otra cosa que las ecuaciones del modelo.

Un primer elemento clave son las matrices de contabilidad social (MCS), que más que una fuente de datos para determinar parámetros serán la base del modelo ya que para su construcción hay que elegir las variables (cuentas) que son relevantes para nuestro modelo y las relaciones entre ellas, dentro de algunos equilibrios básicos que deben cumplir los diferentes bloques que componen la MCS. No es imprescindible tener una MCS para construir un MEGA, pero ayuda mucho tenerla.

El objetivo de los Modelos de Equilibrio General Aplicado es obtener cual será el nuevo equilibrio de la economía y como cambiarán las variables fundamentales de esta, al poner en marcha una política.

## Contacto: alberto@interajedrez.com

## El material de este repositorio es como es, sin ningún tipo de garantía ni responsabilidad relacionados con él.

### Aplicaciones

Tenemos tres aplicaciones:
•	MEGA
•	MEGA_DLL
•	MEGA_GPU
MEGA.
Se trata de una aplicación escrita en Python, tiene programado el modelo de equilibrio general aplicado del libro y predefinidos algunos tipos de escenarios habituales (incrementos de demanda, ayudas, precios fijos, salarios, etc.) que se pueden concretar a través de las opciones de la aplicación. Puede resolver el modelo de forma independiente sin necesidad de otras aplicaciones o librerías externas, aunque tarda demasiado tiempo, pero puede hacer uso de la librería de enlace dinámico MEGA_DLL para reducir drásticamente el tiempo de cálculo.
Tiene la opción de generar ficheros de texto con la evolución de la solución y en especial con el conjunto de datos y opciones de cada caso, para que sirva de entrada a la aplicación MEGA_GPU.
Los datos de entrada son una matriz de contabilidad social (MCS) en formato Excel y las opciones de cálculo a través de los parámetros en la línea de comando cuando se la llama.

MEGA_DLL
Es una librería de enlace dinámico con el mismo modelo que la aplicación MEGA, puede resolver enteramente el modelo o simplemente calcular la función de mérito (merito_s(…) o merito_sol(…)). La aplicación que la llama (por ejemplo, MEGA) le facilita los datos y opciones mediante la llamada a tres procedimientos de la DLL (recibe_opciones(…), recibe_datos(…) y recibe_parametros(…)) y los parámetros que se le pasan a la función de la DLL que soluciona el modelo (soluciona(…)).

MEGA_GPU
Es una aplicación que resuelve el mismo modelo que MEGA y MEGA_DLL haciendo uso de la unidad de proceso gráfico (GPU) para aprovechar el proceso en paralelo de estas tarjetas y reducir el tiempo de cálculo. Es una aplicación independiente, pero necesita leer los datos y opciones de un fichero con el formato adecuado, como el que genera la aplicación MEGA.
