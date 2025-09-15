"""
Alembic environment configuration for PredictFood SQLite database
"""
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Ajouter le répertoire parent au path pour importer les modèles
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Importer vos modèles PredictFood
try:
    # Essayer d'importer selon votre structure de projet
    from models import *
    
    # Si vous utilisez SQLModel
    try:
        from sqlmodel import SQLModel
        target_metadata = SQLModel.metadata
    except ImportError:
        # Si vous utilisez SQLAlchemy classique
        from database import Base
        target_metadata = Base.metadata
        
except ImportError as e:
    print(f"⚠️ Attention: Impossible d'importer les modèles: {e}")
    print("Assurez-vous que votre fichier models.py existe et contient vos modèles SQLModel")
    target_metadata = None

# Configuration Alembic
config = context.config

# Interpréter le fichier de configuration pour les logs
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_database_url():
    """
    Récupère l'URL de la base de données depuis les variables d'environnement
    ou utilise la valeur par défaut pour SQLite
    """
    # Priorité 1: Variable d'environnement DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        return database_url
    
    # Priorité 2: Chemin depuis variable d'environnement
    database_path = os.getenv("DATABASE_PATH", "database.db")
    
    # Priorité 3: Valeur par défaut
    return f"sqlite:///{database_path}"

def include_object(object, name, type_, reflected, compare_to):
    """
    Décider quels objets inclure dans la migration automatique
    """
    # Exclure les tables temporaires ou système
    if type_ == "table" and name.startswith("tmp_"):
        return False
    
    # Exclure la table alembic_version (gérée automatiquement)
    if type_ == "table" and name == "alembic_version":
        return False
        
    return True

def run_migrations_offline() -> None:
    """
    Exécuter les migrations en mode 'offline'.
    
    Cela configure le contexte avec juste l'URL et non un Engine,
    bien que un Engine soit également acceptable ici. En omettant
    l'Engine, nous n'avons même pas besoin d'un DBAPI disponible.
    """
    url = get_database_url()
    
    print(f"🔗 Connexion à la base: {url}")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Options spéciales pour SQLite
        render_as_batch=True,  # Nécessaire pour ALTER TABLE avec SQLite
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    Exécuter les migrations en mode 'online'.
    
    Dans ce scénario nous devons créer un Engine et associer
    une connexion avec le contexte.
    """
    # Récupérer la configuration et définir l'URL de la base
    configuration = config.get_section(config.config_ini_section)
    database_url = get_database_url()
    configuration["sqlalchemy.url"] = database_url
    
    print(f"🔗 Connexion à la base: {database_url}")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Options spécifiques à SQLite
        connect_args={
            "check_same_thread": False,  # Nécessaire pour FastAPI
        }
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Options importantes pour SQLite
            render_as_batch=True,  # Nécessaire pour ALTER TABLE
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
            # Options de nommage pour éviter les conflits
            naming_convention={
                "ix": "ix_%(column_0_label)s",
                "uq": "uq_%(table_name)s_%(column_0_name)s",
                "ck": "ck_%(table_name)s_%(constraint_name)s",
                "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                "pk": "pk_%(table_name)s"
            }
        )

        with context.begin_transaction():
            context.run_migrations()

# Point d'entrée principal
if context.is_offline_mode():
    print("🔄 Mode offline - Génération du SQL...")
    run_migrations_offline()
else:
    print("🔄 Mode online - Exécution des migrations...")
    run_migrations_online()
    print("✅ Migrations terminées!")