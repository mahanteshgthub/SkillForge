import os # Import the 'os' module, which provides a way of using operating system dependent functionality.

# Define BASE_DIR, which will be the absolute path to the directory where this script is located.
# os.path.abspath() returns the absolute path of the given path.
# os.path.dirname(__file__) returns the directory name of the current script.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the Config class, which will hold various configuration settings for the Flask application.
class Config:
    # SECRET_KEY is used for cryptographic operations, such as signing cookies and protecting against CSRF attacks.
    # It tries to get the SECRET_KEY from environment variables (os.environ.get("SECRET_KEY")).
    # If the environment variable is not set, it defaults to "you-will-never-guess".
    # In a production environment, this should always be set via an environment variable for security.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess" #, this-should-be-overridden")

    # SQLALCHEMY_DATABASE_URI specifies the connection string for the database.
    # Here, it's configured to use a SQLite database.
    # "sqlite:///" indicates a relative path to a SQLite database file.
    # os.path.join(BASE_DIR, "skillforge.db") constructs the full path to the 'skillforge.db' file
    # by joining the base directory of the application with the database filename.
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "skillforge.db")

    # SQLALCHEMY_TRACK_MODIFICATIONS is a Flask-SQLAlchemy configuration.
    # Setting it to False disables a feature that signals the application every time a change is about to be made to the database.
    # Disabling this saves memory and is generally recommended unless you specifically need the signals.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WTF_CSRF_ENABLED is commented out, meaning CSRF protection might be handled differently or is implicitly enabled/disabled elsewhere.
    # If uncommented and set to False, it would disable Cross-Site Request Forgery protection provided by Flask-WTF.
    # # WTF_CSRF_ENABLED = False