def detect_killzones(df):
    """
    Devuelve un set de índices de velas que caen dentro de las sesiones activas:
    - Tokio
    - London
    - New York
    """

    killzone_indexes = set()

    for i, row in df.iterrows():
        time = row["datetime"]
        hour = time.hour

        # Tokio session (0:00 - 9:00 UTC)
        if 0 <= hour < 9:
            killzone_indexes.add(i)

        # London session (7:00 - 10:00 UTC)
        if 7 <= hour <= 10:
            killzone_indexes.add(i)

        # New York session (13:00 - 16:00 UTC)
        if 13 <= hour <= 16:
            killzone_indexes.add(i)

    return killzone_indexes

def detect_session(df):
    """
    Devuelve un diccionario {index: session_name} para cada vela.
    London / NY / Tokyo / None
    """
    session_map = {}

    for i, row in df.iterrows():
        time = row["datetime"]
        hour = time.hour

        if 7 <= hour <= 10:
            session_map[i] = "London"
        elif 13 <= hour <= 16:
            session_map[i] = "NY"
        elif 0 <= hour <= 6:
            session_map[i] = "Tokyo"
        else:
            session_map[i] = None

    return session_map

def get_current_session():
    """
    Devuelve la sesión activa según la hora de la última vela del dataframe
    """
    import pandas as pd

    now = pd.Timestamp.utcnow()
    hour = now.hour

    if 0 <= hour < 9:
        return "Tokyo"
    elif 7 <= hour <= 10:
        return "London"
    elif 13 <= hour <= 16:
        return "New York"
    else:
        return "Other"