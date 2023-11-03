
# <h1 align=center> **PROYECTO INDIVIDUAL Nº1** </h1>

# <h1 align=center> **Recomendador de juegos STEAM. FastAPI y deployment en Render** </h1>

## **Introducción**

El proyecto consiste en un modelo recomendador de juegos que utiliza técnicas de aprendizaje automático de Clustering para ofrecer sugerencias de juegos similares al buscado. El modelo se basa en un algoritmo de agrupamiento (clustering) que utiliza análisis de contenido y busca similitud en una base de datos de juegos de la plataforma STEAM.

## **Objetivo**

Como desarrolladores debemos tener la capacidad de llevar a cabo un proceso completo que abarque desde la captura de los datos hasta la entrega de la solución al cliente, y que este sea capaz de consumir la aplicación sin necesidad de un tercero.
Para conseguir la implementación se aplicó un pipeline de datos completo que incluyó la limpieza, procesamiento y transformación de datos, análisis exploratorio de datos (EDA), clustering y el despliegue del servicio de API utilizando FastAPI y Render.

# **Desarrollo**

## ETL

Contamos con tres datasets comprimidos en formato gz. Con un decompresor lo decomprimimos y obtuvimos tres archivos JSON. El primero es un dataset de aproximadamente 30 mil juegos, donde cada juego tiene información respecto a fecha de estreno, precio, categorías, publicador, desarrollador, etc. 
El segundo y tercer dataset relacionan a los usuarios de la plataforma con los juegos: El primero corresponde a los juegos que ha consumido cada usuario (user_items) y el segundo a las reviews de los usuarios (user_reviews).

Como primer obstáculo al ingestar el dataset de games encontramos que tenemos columnas anidadadas en formato json. Son features categóricas multilabel:
- "genres", "tags", "specs"
Se elaboró una estrategia que desanide y luego haga el encoding de estas features. Se hizo una función que devuelve un dataframe con las categorías de cada fila en una lista y también, a modo informativo para el desarrollador, una lista con los valores únicos de esa variable categórica. A los NaN se los asigno a la misma etiqueta "Sin Categoría" para luego decidir qué hacer con estos datos.
Gracias a esto obtuvimos que la base de datos se divide en 23 géneros distintos, 32 especificaciones y 338 tags distintos. A la columna "price" tuvimos que procesarla ya que no solo representaba números sino que había palabras en medio.
En ETL también se transformaron datos para llevarlos a datasets procesados y que ocupen menos espacio respecto a user_items, necesarios para los endpoints de la API (más adelante se darán mas detalles).

## EDA

Luego del ETL los datos son importados en otra sección. Considero más legible y ordenado ir haciendo el proyecto en etapas bien definidas.

En una primera etapa analizamos user_reviews mediante NLP (natural language processing) con la librería TextBlob. Esta nos permite determinar el sentimiento e intención del interlocutor de cada review a través de dos valores: "Polarity" de -1 a 1 (-1 representa una valoración negativa, 0 neutral y 1 positiva) y "Subjectivity" de 0 a 1 (0 representa una valoración totalmente objetiva y 1 totalmente subjetiva).

A variables como "publisher" o "developer" que son columnas categóricas le aplicamos OneHotEncoder de Scikit learn para transformarlas a columnas binarias y poder ser consumidas por un algoritmo de ML. Debido a la gran cantidad de "publisher" optamos por elegir las más relevantes e hicimos una función con el "top 30 de publicadores". Lo mismo se hizo con "developer" con un top 50.

Luego se analizó las variables continuas a cada una por separado. Con un gráfico de violín se pudo ver si tenían outliers o valores atípicos y en caso de ser así, se analizó los casos puntualmente. Al final se concluyó en que los valores de estas features eran normales.


## ML-Clustering
Ya habiendo analizado los datos pasamos a la sección de machine learning. Tenemos que hacer una buena selección de los hiperparámetros del algoritmo que haga el agrupamiento de los juegos por similitud.
Elegimos el modelo K-Means de Scikit learn para hacer el agrupamiento utilizando la distancia euclidea para el cómputo, buscar similares y elegir el mejor centroide. Para calibrarlo correctamente se usó el método del codo para determinar que con k = 25 clusters se conseguía una buena inercia.

### Main
En el main se ejecuta la API de FastAPI que nos brinda la interfaz para que podamos consumir nuestro recomendador de juegos. La aplicación tiene los siguientes endpoints, los primeros cinco en los que tenemos que aplicar transformaciones y cálculo para conseguir un resultado determinado y los dos últimos ejecutan los resultados de nuestro recomendador de juegos:

+ def **PlayTimeGenre( *`genero`* )**:
    Debe devolver año con mas horas jugadas para dicho género.


+ def **UserForGenre( *`genero`* )**:
    Debe devolver el usuario que acumula más horas jugadas para el género dado y una lista de la acumulación de horas jugadas por año.


+ def **UsersRecommend( *`año`* )**:
    Devuelve el top 3 de juegos MÁS recomendados por usuarios para el año dado. (reviews.recommend = True y comentarios positivos/neutrales)
    

+ def **UsersNotRecommend( *`año`* )**:
    Devuelve el top 3 de juegos MENOS recomendados por usuarios para el año dado. (reviews.recommend = False y comentarios negativos)
    

+ def **sentiment_analysis( *`año`* )**:
    Según el año de lanzamiento, se devuelve una lista con la cantidad de registros de reseñas de usuarios que se encuentren categorizados con un análisis de sentimiento.
    

+ def **recomendacion_juego( *`id`* )**:
    Ingresando el id de producto, deberíamos recibir una lista con 5 juegos recomendados similares al ingresado.


+ def **recomendacion_usuario( *`user_id`* )**:
    Ingresando el id de un usuario, deberíamos recibir una lista con 5 juegos recomendados para dicho usuario.