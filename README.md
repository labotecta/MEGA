
### *Todo el material del repositorio, incluido el código de las aplicaciones es de libre utilización, pero esperamos que su uso se acompañe de la cita correspondiente, de acuerdo con las normas habituales de citación.*
### *Así mismo nos gustaría recibir, si es posible, una copia de los modelos que se construyan a partir de este material.*

___

## Este es el repositorio del Libro "Guía práctica para Modelos de Equilibrio General Aplicado (MEGA)
## Computable General Equilibrium (CGE)"
## Publicado en la Editorial universitaria Aula Magna McGraw Hill

##<p align="center">[Tienda](https://libros.cc/autor/Alberto-Ba%C3%B1%C3%B3n-Serrano.htm)</p>

El libro muestra cómo construir y resolver un Modelo de Equilibrio General Aplicado (MEGA), sin conocimientos previos y desde el principio. Una parte importante será el planteamiento y resolución de escenarios que, en definitiva, es lo que se pretende con un MEGA. El libro no se limita a exponer cómo construir un modelo, en él se construye uno plenamente operativo. El código fuente de la aplicación informática (Python y C++) está disponible en un repositorio público y es de libre utilización, así como los datos utilizados en el calibrado y resolución de los escenarios tratados en este libro.

___

# MEGA
Un modelo de equilibrio general aplicado (MEGA) define una serie de magnitudes o variables de importancia económica y las ecuaciones que las relacionan entre sí. Como las relaciones en economía son de carácter circular, algunas ecuaciones hacen uso de valores que son el resultado de otras ecuaciones que a su vez dependen de las primeras. Una vez planteado el modelo, hay que resolver las ecuaciones, es decir, que valores han de tener las variables, para que todas las ecuaciones se cumplan de forma simultánea. Rara vez, por no decir nunca, estaremos ante un sistema de ecuaciones lineales y hay que recurrir a software de resolución de ecuaciones no lineales. Aunque la resolución de ecuaciones no tiene nada que ver con el óptimo de ninguna función, la resolución se suele plantear como un problema de minimización (o maximización) de alguna función objetivo sometida a restricciones, ya que para esto hay disponible software comercial y de libre utilización. Que función objetivo utilizar es irrelevante y lo que se busca es que el software nos encuentre una solución en la que se cumplan las restricciones que no serán otra cosa que las ecuaciones del modelo.

Un primer elemento clave son las matrices de contabilidad social (MCS), que más que una fuente de datos para determinar parámetros serán la base del modelo ya que para su construcción hay que elegir las variables (cuentas) que son relevantes para nuestro modelo y las relaciones entre ellas, dentro de algunos equilibrios básicos que deben cumplir los diferentes bloques que componen la MCS. No es imprescindible tener una MCS para construir un MEGA, pero ayuda mucho tenerla.

El objetivo de los Modelos de Equilibrio General Aplicado es obtener cual será el nuevo equilibrio de la economía y como cambiarán las variables fundamentales de esta, al poner en marcha una política.

## Contacto: alberto@interajedrez.com

## El material de este repositorio es como es, sin ningún tipo de garantía ni responsabilidad relacionados con él.