import tempfile
import os


class Config:
    # デバッグモードを有効にする
    DEBUG = True

    # 一時ディレクトリを使用
    UPLOAD_FOLDER = tempfile.gettempdir()
    
    # Dropzoneの設定
    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_ALLOWED_FILE_CUSTOM = True
    DROPZONE_ALLOWED_FILE_TYPE = 'image/*'
    DROPZONE_MAX_FILE_SIZE = 10
    DROPZONE_MAX_FILES = 5
    DROPZONE_TIMEOUT = 5 * 60 * 1000 
    
    # 許可する拡張子
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

config = Config()
