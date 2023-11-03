import pandas as pd
import numpy as np
import ast
from fastapi import FastAPI, HTTPException


# Cargamos los dataframes preprocesados
games = pd.read_csv('games.csv', dtype = {'id': int})
games['release_date'] = pd.to_datetime(games['release_date'])
user_items = pd.read_csv('user_items.csv')
user_reviews = pd.read_csv('user_reviews.csv', parse_dates=['posted'])
playtime_genre_year = pd.read_csv('playtime_genre_year.csv')
user_genre_year = pd.read_csv('user_genre_year.csv')
user_url = pd.read_csv('user_url.csv')

# Creamos una instancia de FastAPI
app = FastAPI()

# Funcion "PlaytimeGenre"
# Debe devolver año con mas horas jugadas para dicho género.
@app.get('/PlayTimeGenre/{genero}')
def PlayTimeGenre(genero: str):
    if genero in playtime_genre_year.columns.tolist():
        maximo = playtime_genre_year[genero].max()
        anio = playtime_genre_year[playtime_genre_year[genero] == maximo]["release_date"].values[0]
        return {f'Año de lanzamiento con más horas jugadas para {genero}: {anio}'}
    else:
        return "Género no encontrado"


# Funcion "UserForGenre"
# Debe devolver el usuario que acumula más horas jugadas para el género dado y una lista de la acumulación de horas jugadas por año.
@app.get('/UserForGenre/{genero}')
def UserForGenre(genero: str):
    if genero in user_genre_year.columns.tolist():
        user_genre_year_aux = user_genre_year.groupby(["user_id"]).sum().reset_index()
        valor_maximo = user_genre_year_aux[genero].max()
        usuario = user_genre_year_aux[user_genre_year_aux[genero] == valor_maximo]["user_id"].values[0]
        df_usuario = user_genre_year[user_genre_year["user_id"] == usuario]
        playtime_por_año = df_usuario[genero]
        años = df_usuario["release_date"]
        return {
                    f'Usuario con más horas jugadas para {genero}': usuario,
                    'Horas jugadas':
                                    [
                                    {
                                    'Año': años, 
                                    'Horas': round(playtime_por_año/60, 1),       # playtime es en minutos, convertimos a horas 
                                    }
                                    for años, playtime_por_año in zip(años, playtime_por_año) if playtime_por_año > 0
                                    ]
                }
    else:
        return "Género no encontrado"

# Funcion "UsersRecommend"
# Devuelve el top 3 de juegos MÁS recomendados por usuarios para el año dado. (reviews.recommend = True y comentarios positivos/neutrales)
@app.get('/UsersRecommend/{anio}')
def UsersRecommend(anio: int):
    if isinstance(anio, int):
        if anio in user_reviews['posted'].dt.year.tolist():
            # Filtrado por año
            reviews_aux = user_reviews[user_reviews['posted'].dt.year == anio]
            # Filtrado por aquellos registros en "recommend" es True y sentiment_analysis es 1 o 2
            reviews_aux = reviews_aux[(reviews_aux['recommend'] == True) & (reviews_aux['sentiment_analysis'].isin([1, 2]))]
            # Agrupamos por "item_id"
            reviews_year = reviews_aux[["item_id", "recommend"]].groupby(["item_id"]).count().reset_index()
            reviews_year = reviews_year.sort_values(by = "recommend", ascending = False)
            # Nos quedamos solo con los tres primeros
            reviews_year = reviews_year.head(3)
            # Hacemos un merge con games para obtener el titulo
            reviews_year = reviews_year.merge(games, left_on = 'item_id', right_on = 'id', how = 'left')
            # Crea una serie que contiene "title" si no es NaN, de lo contrario, toma "item_id"
            reviews_year = reviews_year["title"].combine_first(reviews_year["item_id"])
            mas_recomendados = reviews_year.tolist()
            return [{"Puesto " + str(i + 1): mas_recomendado} for i, mas_recomendado in enumerate(mas_recomendados)] 
        else:
            return "Año sin reviews"
    else:
        raise HTTPException(status_code = 404, detail = "Debe ingresar un año.")

# Funcion "UsersNotRecommend"
# Devuelve el top 3 de juegos MENOS recomendados por usuarios para el año dado. (reviews.recommend = False y comentarios negativos)
@app.get('/UsersNotRecommend/{anio}')
def UsersNotRecommend(anio: int):
    if isinstance(anio, int):
        if anio in user_reviews['posted'].dt.year.tolist():
            # Filtrado por año
            reviews_aux = user_reviews[user_reviews['posted'].dt.year == anio]
            # Filtrado por aquellos registros en "recommend" es False y sentiment_analysis es 0
            reviews_aux = reviews_aux[(reviews_aux['recommend'] == False) & (reviews_aux['sentiment_analysis'] == 0)]
            # Agrupamos por "item_id"
            reviews_year = reviews_aux[["item_id", "recommend"]].groupby(["item_id"]).count().reset_index()
            reviews_year = reviews_year.sort_values(by = "recommend", ascending = False)
            # Nos quedamos solo con los tres primeros
            reviews_year = reviews_year.head(3)
            # Hacemos un merge con games para obtener el titulo
            reviews_year = reviews_year.merge(games, left_on = 'item_id', right_on = 'id', how = 'left')
            # Crea una serie que contiene "title" si no es NaN, de lo contrario, toma "item_id"
            reviews_year = reviews_year["title"].combine_first(reviews_year["item_id"])
            menos_recomendados = reviews_year.tolist()
            return [{"Puesto " + str(i + 1): menos_recomendado} for i, menos_recomendado in enumerate(menos_recomendados)] 
        else:
            return "Año sin reviews"
    else:
        raise HTTPException(status_code = 404, detail = "Debe ingresar un año.")


# Funcion "sentiment_analysis"
# Según el año de lanzamiento, se devuelve una lista con la cantidad de registros de reseñas de usuarios que se encuentren categorizados con un análisis de sentimiento.
@app.get('/sentiment_analysis/{anio}')
def sentiment_analysis(anio: int):
    if isinstance(anio, int):
        user_reviews_aux = user_reviews.merge(games[["id", "release_date"]], left_on = 'item_id', right_on = 'id', how = 'left')
        user_reviews_aux = user_reviews_aux[["sentiment_analysis", "release_date"]]
        # Corregimos los juegos no encontrados en games
        user_reviews_aux["release_date"] = user_reviews_aux["release_date"].fillna('1900-01-01')
        if anio in user_reviews_aux['release_date'].dt.year.tolist():
            # Filtramos los registros por el año de estreno solicitado
            user_reviews_aux = user_reviews_aux[user_reviews_aux["release_date"].dt.year == anio]
            user_reviews_aux = user_reviews_aux.groupby("sentiment_analysis").count().reset_index()
            user_reviews_aux = user_reviews_aux.rename(columns = {"release_date": "conteo"})
            cantidades = user_reviews_aux["conteo"].tolist()
            return {f"Negative = {cantidades[0]}", f"Neutral = {cantidades[1]}", f"Positive = {cantidades[2]}"}
        else:
            return "No hay reviews para los juegos con dicho año de estreno"
    else:
        raise HTTPException(status_code = 404, detail = "Debe ingresar un año.")


# Machine Learning. Clustering

# Cargamos el dataframe de games transformado y escalado
games_ml = pd.read_csv('games_ml.csv')

# Importamos las predicciones de KMeans que se hicieron anteriormente
labels = np.loadtxt('labels.csv', delimiter=',', dtype = int)

# Ingresando el id de producto, deberíamos recibir una lista con 5 juegos recomendados similares al ingresado.
@app.get('/recomendacion_juego/{id}')
def recomendacion_juego(id: int):
    if id in games["id"].tolist():
        rows = games_ml.loc[games["id"] == id]
        titulos_similares_general = []
        for indice, row in rows.iterrows():
            cluster_referencia = labels[indice]
            # Encontrar todas las películas en el mismo cluster que el punto de referencia
            games_cluster = games_ml.iloc[labels == cluster_referencia]
            # Calcular las distancias entre el punto de referencia y los juegos del cluster
            distancias = np.linalg.norm(games_cluster - row.values, axis = 1)
            # Ordenar los juegos por distancia y seleccionar los 5 cercanos
            indices_games_similares = np.argsort(distancias)[1:6]
            games_similares = games_cluster.iloc[indices_games_similares]
            # Obtener los títulos de los juegos similares
            titulos_similares = [games.loc[games.index == index_game]['title'].values[0]
                                for index_game in games_similares.index]
            titulos_similares_general.append({'lista recomendada': titulos_similares})
        return titulos_similares_general
    else:
        return "Id de juego no encontrado"

# Define una función para calcular el centro de un conjunto de vectores
def calcular_centro(vectores):
    return np.mean(vectores, axis=0)

# Ingresando el id de un usuario, deberíamos recibir una lista con 5 juegos recomendados para dicho usuario.
@app.get('/recomendacion_usuario/{user_id}')
def recomendacion_usuario(user_id: str):
    if user_id in user_items["user_id"].values:
        items = user_items.loc[user_items["user_id"] == user_id, "item_name"].values.tolist()
        items = [ast.literal_eval(item) for item in items][0]
        # Lista para almacenar las recomendaciones para cada ítem
        titulos_similares_general = list()

        for item in items:
            rows = games_ml.loc[games["id"] == item]
            for indice, row in rows.iterrows():
                cluster_referencia = labels[indice]
                # Encontrar todas los juegos en el mismo cluster que el punto de referencia
                games_cluster = games_ml.iloc[labels == cluster_referencia]
                # Calcular las distancias entre el punto de referencia y los juegos del cluster
                distancias = np.linalg.norm(games_cluster - row.values, axis=1)
                # Ordenar las películas por distancia y seleccionar los 5 cercanas
                indices_games_similares = np.argsort(distancias)[1:6]
                games_similares = games_cluster.iloc[indices_games_similares]
                # Obtener los títulos de los juegos similares
                titulos_similares = [games.loc[games.index == index_game]['title'].values[0]
                                    for index_game in games_similares.index]     
                # Filtrar títulos repetidos
                for titulo in titulos_similares:
                    if titulo not in titulos_similares_general:
                        titulos_similares_general.append(titulo)
        
        # Calcular el centro de "items"
        indices_entrada = games[games["id"].isin(items)].index
        games_entrada = games_ml.loc[indices_entrada]
        centro_items = np.mean(games_entrada, axis = 0)

        indices_games_similares = games[games["title"].isin(titulos_similares_general)].index
        games_similares_general = games_ml.loc[indices_games_similares]
        # Calcular las distancias entre el centro y todos los juegos en "titulos_similares_general"
        distancias_al_centro = np.linalg.norm(games_similares_general - centro_items, axis = 1)

        # Ordenar los juegos por distancia al centro y seleccionar los 5 más cercanos
        indices_similares_al_centro = np.argsort(distancias_al_centro)[:5]
        juegos_similares_al_centro = games.iloc[indices_similares_al_centro]["title"].tolist()

        return {
                'lista_recomendada_usuario': juegos_similares_al_centro
                }
    else:
        raise HTTPException(status_code = 404, detail = "El id de usuario no existe o no tiene items.")
