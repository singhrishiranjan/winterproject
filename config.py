class Config:
    SECRET_KEY = "apnasecret"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///confessions.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False